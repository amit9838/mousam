# Overview rules

The overview is the one-line message under the current conditions, for
example *"Rain is likely to start around 5:00 PM with 70% chance."*

This file is the **source of truth**. To change a rule, change this file
first, then the code and the numbers to match. If the code and this file
disagree, the code is wrong.

| What | Where |
| --- | --- |
| The rules, and merging the ones that happen at once | [`src/core/overview/rules.py`](../src/core/overview/rules.py) (`RuleBook.default()`, `combine()`) |
| Hour tests shared by the rules | [`src/core/overview/hour_tests.py`](../src/core/overview/hour_tests.py) |
| When it opens | [`src/core/overview/announce.py`](../src/core/overview/announce.py), timed by [`src/state/overview_engine.py`](../src/state/overview_engine.py) |
| Notifications | [`src/ui/notifications.py`](../src/ui/notifications.py), sent by [`src/app.py`](../src/app.py) |
| Numbers | [`src/config.py`](../src/config.py), under "Overview" and "Overview rules" |
| Wordings | [`src/core/overview/messages.py`](../src/core/overview/messages.py) |

---

## 1. How it works, in short

Each time the overview runs:

1. **Pick the window**: the hours to look at (section 3).
2. **Run every rule.** Each one either stays silent or returns one
   *insight*. A rule that fails says nothing (section 2.4).
3. **Drop** insights that are no longer true.
4. **Sort** the rest by priority, highest first.
5. **Merge** insights that happen at the same time into one sentence
   (section 5).
6. **Decide** which insight to show now, if any (section 6).
7. **Show it** in the window, or send it as a notification (section 7).

The calm rule always speaks, so there is always at least one insight.
Nothing is thrown away: insights that don't open now wait for their turn.

---

## 2. Terms

### 2.1 Insight

What a rule returns when it has something to say:

| Part | Meaning |
| --- | --- |
| message | one whole sentence, translated as a whole |
| level | how serious it is (2.2) |
| priority | which insight wins within a level |
| topic | what it is about (rain, air, …); each topic has its own notification |
| about | the forecast hour or event it describes, or "now". Used to tell news from a repeat (6.3) |
| happens | the hour it starts, or now. Usually the same as *about*: rain easing around 4 PM is *about* 4 PM but *happens* now. Used for merging (section 5) |
| icon | optional, shown before the message |
| heading | optional (*Tomorrow*); otherwise the window's heading |
| valid until | the moment the message stops being true (section 4) |
| open time | how long it stays open, set by its level (8) |

### 2.2 Levels

| Level | Meaning | Heading colour |
| --- | --- | --- |
| extreme | danger to people or property | error (red) |
| high | disrupts plans, or a health risk | warning (yellow) |
| medium | worth changing plans for | accent |
| low | nice to know | plain |
| calm | nothing to say | plain |

The level decides how an insight is shown, how often it is repeated and
whether it becomes a notification.

### 2.3 Hours

- **Now** means the current hour.
- **A wet hour** has a 50% chance of precipitation or more; **a dry hour**
  less. An hour with no data is neither.
- **A wet spell** runs from the first wet hour to the first dry hour after
  it. If it is wet all through the window, the spell is the whole window.
- **Snow or rain**: an hour is snow when it has a snow code (71, 73, 75,
  77, 85, 86), otherwise rain.
- **Two insights happen together** when both happen now, or both happen
  later within **60 minutes** of each other. One now and one later never
  happen together (with two exceptions: turning stormy and turning heavy,
  section 5).

### 2.4 Ignore on fail

If a rule fails (for example on missing or odd data), it says nothing. The
other rules still run. The failure is logged in debug mode only.

### 2.5 Units

All thresholds are **metric**. With imperial units, temperatures (°F) and
wind speeds (mph) are converted to metric before comparing. Rain (mm) and
visibility (m) come from the API in metric in both systems. Messages show
values in the user's own units.

---

## 3. The window

The rules only look at hours inside the window. It always includes the
current hour.

| Situation | Window | Heading |
| --- | --- | --- |
| Day (next sunset comes before next sunrise) | now until sunset, but at least **3 hours** | Today |
| Night | now until the next sunrise | Tonight |
| No sunrise or sunset (polar day or night) | the next **12 hours** | Tonight |

---

## 4. Every message must stay true

An insight is never shown after its *valid until*:

| The message says | True until |
| --- | --- |
| something happening **now** | the next full hour (then it is checked again) |
| something **around a time** ("around 4:00 PM") | that time |
| something lasting **until about a time** | that time |
| **tomorrow** | local midnight |
| **minutes away** ("in 40 minutes") | while it is at most **5 minutes** off |
| **the weather at sunset or sunrise** | the sunset or sunrise |
| **two things in one sentence** | the first of them stops being true |

---

## 5. Several things at once

Every opening shows **one sentence**. Two insights become one sentence only
when a natural sentence exists; otherwise the second waits for the next
turn. A single insight is always shown as it is.

Four steps run in this order. Each insight is used at most once.

### 5.1 Turning stormy (rain leads a storm)

**When:** rain now (or starting later), and a storm later **in the same
wet spell**: after the rain starts and before its first dry hour (any storm
hour counts if it rains all through the window).

**Not when:** the storm is in the rain's first hour, before the rain, or
after the rain has eased; those are folded or combined instead. Only rain
turns stormy; snow is folded into a storm.

| Rain message | Becomes |
| --- | --- |
| falling now, easing later | "Rain right now, turning stormy before it eases off around 8:00 PM." |
| falling now, all through the window | "Rain right now, turning stormy later and lasting until about 7:00 AM." |
| starting later | "Rain from around 4:00 PM with 70% chance, turning stormy later." |

- The storm's hour is not said; the rain gives the time (and its chance
  when it starts later).
- Takes the storm's rule, level (extreme), icon and topic; names both
  topics (storm, rain).
- True until the storm's hour, or the rain's end if sooner. Then "Thunderstorms
  are likely right now" takes over, with the rain folded in.
- It counts as being about the rain's hour, so the storm moving within the
  same spell (5 PM → 6 PM) is not news.
- It runs first, so the rain isn't folded away. A wind or heavy rain with
  that storm then gets its own turn.

### 5.2 Fold (one already says the other)

When they happen together:

| Kept | Folded into it |
| --- | --- |
| storm | rain or snow |
| heavy rain | rain |
| heavy snow | snow |

The folded insight isn't shown, but counts as said with the kept one. Its
notification is withdrawn when the kept one is sent.

### 5.3 Turning heavy (rain becomes heavy rain)

**When:** rain now (or starting later), and heavy rain later **in the same
wet spell** (the same for snow and heavy snow). This takes what the fold
refused: one now and one later, or more than 60 minutes apart.

| Rain or snow message | Becomes |
| --- | --- |
| falling now, easing later | "Rain right now, turning heavy around 11:00 PM and easing off around 6:00 AM." |
| falling now, all through the window | "Rain right now, turning heavy around 11:00 PM and lasting until about 7:00 AM." |
| starting later | "Rain from around 2:00 PM, turning heavy around 5:00 PM." |

- Takes the heavy one's rule and level (high), and the rain or snow topic.
- True until the heavy hour. Then "Heavy rain is likely right now" takes
  over, with the rain folded in.
- The easing time or the heavy hour moving is news.
- Heavy rain after the rain has eased is a second spell: each keeps its own
  turn.

### 5.4 Combine (a known pair)

When they happen together, tried in this order:

| Pair | Message |
| --- | --- |
| storm + wind | "Thunderstorms with strong wind, around 45 km/h, are likely from around 4:00 PM." |
| storm + heavy rain | "Thunderstorms with heavy rain are likely from around 4:00 PM." |
| heavy rain + wind | "Heavy rain and strong wind, around 45 km/h, are likely from around 4:00 PM." |
| heavy snow + wind | "Heavy snow and strong wind, around 45 km/h, are likely from around 4:00 PM." |
| rain + wind | "Rain and strong wind, around 45 km/h, are likely from around 4:00 PM." |
| snow + wind | "Snow and strong wind, around 45 km/h, are likely from around 4:00 PM." |

Each pair also has a "right now" message ("Thunderstorms with strong wind,
around 45 km/h, are likely right now.").

- Because of the order, storm + heavy rain + wind becomes storm + wind, and
  the heavy rain gets the next turn.
- An insight already turned or folded isn't combined again.
- Says the **earlier** of the two times, as "from around". True until the
  earlier of the two stops being true.
- Takes the **higher level** of the two, and the rule, topic and priority of
  the more important one: storm, then heavy rain or snow, then rain or
  snow, then wind.
- Names both topics: its notification replaces the other's, and is
  withdrawn as soon as either part stops being true.

### 5.5 The next turn

Anything not merged stays its own insight (a storm now and UV three hours
later, a third urgent thing, one now and one later). It opens on its own
after the gap (6.6).

---

## 6. When the overview opens

Numbers: `OVERVIEW_MIN_GAP_MINUTES`, `OVERVIEW_REMIND_*`,
`OVERVIEW_FORGET_MINUTES`, `OVERVIEW_COMBINE_MINUTES`,
`OVERVIEW_NOTIFY_TOPICS` in `config.py`.

The overview opens when it has **something new to say**, and now and then
to **remind** of something already said.

### 6.1 When it runs

- Nothing runs while the app starts.
- First run: **10 seconds** after the first data load
  (`OVERVIEW_FIRST_DELAY`).
- After each later refresh: **2 seconds** (`OVERVIEW_REFRESH_DELAY`).
- Otherwise only when something changes: an insight stops being true, a
  reminder is due, or the gap after an opening ends.

### 6.2 Fresh data

The overview sees a changed forecast only after a refresh.

| Refresh | How |
| --- | --- |
| automatic | every **10 minutes** (`AUTO_REFRESH_MINUTES`), always; no setting |
| Ctrl+R | at once, with responses up to a minute old (`DATA_CACHE_TTL`) |
| Ctrl+Shift+R | fetches the location again without cached data |

### 6.3 News or a repeat

Two insights are **the same** when they have the same rule, message, level,
and the same forecast hour or event they are about.

| Change | News? |
| --- | --- |
| time passing ("in 40 minutes" → "in 35 minutes") | no |
| only the chance changes (60% → 85%, same hour) | no |
| the hour moves (rain 4 PM → 7 PM) | yes |
| the level changes (wind medium → high) | yes |
| the message changes (tomorrow warmer → rainy) | yes |

A merged insight counts as each of its parts: it is news when either part
is, and saying it counts as saying both.

### 6.4 Memory

What has been said is remembered **per location**: each insight, when it
was last announced, and how many times.

- A refresh keeps the memory: the same forecast after a refresh is not news,
  and reminders are not reset.
- An insight that goes away and comes back (a storm that comes and goes) is
  still remembered. It is forgotten **4 hours** after it was last true.
- Clicking the info button counts as announcing the insight it shows.
- Switching location, or turning off both the overview and notifications,
  starts over.

### 6.5 When each insight is due

| Insight | Due |
| --- | --- |
| never said | now: it is **news** |
| said before, extreme | reminder after 30 min |
| said before, high | reminder after 60 min |
| said before, medium | reminder after 120 min |
| said before, low | never again (said once) |
| calm | once per location, never reminded |

Each next reminder waits **twice as long**, at most **4 hours**. So an
unchanged high insight opens at 0, 60, 180 and 420 minutes, then every
4 hours; an unchanged storm at 0, then 30, 90 and 210 minutes.

**Calm takes no turn** while anything else is worth saying; it is shown only
when it is the only insight.

### 6.6 Which one opens

Among the insights that are due:

1. news before reminders,
2. then the highest level,
3. then the highest priority.

So something more urgent (a storm) opens first, at once.

**The gap:** nothing opens within **15 minutes** of the last opening. The
others that are due open one at a time, each after the gap.

**Except urgent news:** extreme news (a storm, freezing rain, dangerous heat
or cold) opens at once, even inside the gap, so a safety warning never waits
behind a UV note. Not when the last opening was extreme too: two extreme
things still take turns, each after the gap, so one never replaces the
other a moment after it opened.

### 6.7 Between openings

- The text on screen stays up to date without opening: values change, the
  wording stays.
- When the shown insight stops being true, the most important remaining one
  takes its place, also without opening.

---

## 7. Where it is shown

One place at a time.

| Main window | Shown as |
| --- | --- |
| can be seen | the overview pill opens in it, for news and reminders. The info button opens it on the insight shown |
| minimized, hidden by compact mode, or otherwise out of sight | a desktop notification: the city as title, the sentence as body; clicking it opens the main window |

### 7.1 What is sent as a notification

- news of **medium or above**
- news about **tomorrow** (low, but worth knowing before the evening ends)
- reminders of **extreme** insights (storms)

Other low insights and calm are never sent.

| Level | Notification priority |
| --- | --- |
| low, medium | low |
| high | normal |
| extreme | high |

Never "urgent", so Do Not Disturb still holds.

### 7.2 One notification per topic

Each topic has its own notification, so air quality and rain can be there
side by side. A new message replaces only the one on the same topic: heavy
rain shares the rain topic, so "Heavy rain around 5:00 PM" replaces "Rain is
likely around 4:00 PM". A merged insight is sent under its main topic and
covers the other ("storm + wind" withdraws the wind notification).

| Topic | Rules |
| --- | --- |
| storm | storm |
| freezing | freezing rain |
| rain | rain, heavy rain |
| snow | snow, heavy snow |
| feels_like | extreme feels like |
| air | air quality |
| uv | UV |
| wind | wind |
| fog | fog |
| temperature | temperature swing |
| tomorrow | tomorrow |
| sun | sunset and sunrise |
| calm | calm (never sent) |

### 7.3 When a notification is withdrawn

- its topic has no insight any more (it stopped being true, or the forecast
  changed: rain turning to snow withdraws rain)
- a combined one: as soon as either part stops being true
- a folded one: stays while its own topic is true
- the location changes
- notifications are turned off
- the main window comes into view (the overview shows it there)

### 7.4 Settings

Preferences → *Weather Overview*: *Show Overview* and *Notifications*.

| Overview | Notifications | Window in sight | Window out of sight |
| --- | --- | --- | --- |
| on | on | overview | notification |
| on | off | overview | nothing |
| off | on | nothing | notification |
| off | off | nothing (no processing) | nothing |

---

## 8. How long a message stays open

| Level | Open for |
| --- | --- |
| calm, low, medium | 15 seconds |
| high | 22 seconds (15 + 7) |
| extreme | 30 seconds (15 + 15) |

---

## 9. The rules

"An hour" means an hour inside the window. Examples are the first wording of
each message.

### Summary

| # | Rule | Priority | Level | Topic | Icon | Applies when |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Storm | 100 | extreme | storm | storm | code 95, 96 or 99 |
| 2 | Freezing rain | 95 | high | freezing | showers | code 56, 57, 66 or 67 |
| 3 | Heavy rain or snow | 90 | high | rain / snow | showers / snow | code 65, 82, 75, 86, or ≥ 7.6 mm |
| 4 | Extreme feels like | 85 | high | feels_like | none | feels like ≥ 40 °C, else ≤ −15 °C |
| 5 | Air quality | 80 | high | air | none | US AQI ≥ 151 |
| 6 | UV | 75 | high | uv | clear | UV index ≥ 8 |
| 7 | Rain or snow | 60 | medium | rain / snow | showers / snow | a wet hour |
| 8 | Wind | 55 | medium, high from 60 km/h | wind | windy | wind ≥ 40 km/h |
| 9 | Fog | 50 | medium | fog | fog | visibility < 1 km, or code 45 or 48 |
| 10 | Temperature swing | 40 | low | temperature | none | ≥ 6 °C from now |
| 11 | Tomorrow | 30 | low | tomorrow | showers / none | from 6 PM; rain or a different high |
| 12 | Sunset and sunrise | 20 | low | sun | sunset / sunrise | sunset ≤ 2 h, or sunrise ≤ 3 h |
| 13 | Calm | 0 | calm | calm | none | always |

### 9.1 Storm

**Applies when** an hour has code 95, 96 or 99. Uses the first such hour.

| Case | Says |
| --- | --- |
| now | "Thunderstorms are likely right now. Stay indoors if you can." |
| later, chance ≥ 50% | "Thunderstorms are likely around 4:00 PM with 80% chance of rain. Be indoors by then." |
| later, chance < 50% | "Thunderstorms are possible around 4:00 PM, with 30% chance of rain." |
| later, no chance in the data | "Thunderstorms are likely around 4:00 PM. Plan to be indoors by then." |

- **The chance** is the storm hour's own precipitation probability, never
  another hour's. It says "chance of rain", not "of thunderstorms": the
  forecast gives the chance of precipitation, not of lightning.
- The code and the chance come from different models, so a storm with a
  low chance is common; "possible" keeps the sentence from contradicting
  itself.
- *Likely* and *possible* are different messages: crossing 50% is news; a
  change on the same side is not.
- **Merges:** rain leads it (turning stormy); rain or snow folded in; wind
  or heavy rain combined.

### 9.2 Freezing rain

**Applies when** an hour has code 56, 57, 66 or 67. Uses the first such hour.

| Case | Says |
| --- | --- |
| now | "Freezing rain is likely right now. Roads and paths may be icy." |
| later | "Freezing rain is likely around 2:00 AM. Roads and paths may turn icy." |

### 9.3 Heavy rain or snow

**Applies when** an hour has a heavy rain code (65, 82), a heavy snow code
(75, 86), or **7.6 mm** of precipitation or more. Uses the first such hour;
snow if that hour has a snow code, otherwise rain.

| Case | Rain | Snow |
| --- | --- | --- |
| now | "Heavy rain is likely right now. Expect puddles and slow roads." | "Heavy snow is likely right now. Travel may be slow." |
| later | "Heavy rain is likely around 3:00 PM. Keep an umbrella close." | "Heavy snow is likely around 3:00 PM. Travel may be slow after that." |

**Merges:** rain or snow folded in, or turning heavy; storm or wind combined.

### 9.4 Extreme feels like

**Applies when** the hottest hour feels like **40 °C** or more; if not, when
the coldest hour feels like **−15 °C** or less. Heat is checked first.

| Case | Says |
| --- | --- |
| heat, now | "It feels like 41° right now. Stay hydrated and seek shade." |
| heat, later | "It will feel like 41° by around 2:00 PM. Stay hydrated and seek shade." |
| cold, now | "It feels like −18° right now. Dress warmly, in layers." |
| cold, later | "It will feel like −18° by around 6:00 AM. Dress warmly, in layers." |

### 9.5 Air quality

**Applies when** the US AQI reaches **151** (unhealthy) or more. Uses the
first such hour. Without air quality data, it says nothing (the weather is
still shown).

| Case | Says |
| --- | --- |
| now | "Air quality is unhealthy right now. Limit time outdoors if you can." |
| later | "Air quality turns unhealthy around 10:00 AM. Consider limiting time outdoors." |

### 9.6 UV

**Applies when** an hour has a UV index of **8** or more. Uses the first run
of such hours, ending at the end of its last hour.

| Case | Says |
| --- | --- |
| now | "UV is very high until about 3:00 PM. Use sunscreen and cover up." |
| later | "UV will be very high from about 11:00 AM to 3:00 PM. Use sunscreen outdoors." |

### 9.7 Rain or snow

**Applies when** there is a wet hour (2.3). Snow uses the same sentences
with "Snow".

| Case | Says | Happens |
| --- | --- | --- |
| wet now, a dry hour later | "Rain is likely right now, easing off around 4:00 PM." (the first dry hour) | now |
| wet now and all through the window | "Rain is likely to keep falling until about 6:00 PM." (end of window) | now |
| dry now, wet later | "Rain is likely to start around 5:00 PM with 70% chance." (first wet hour, its chance) | first wet hour |
| dry all through the window | nothing | |

**Merges:** leads a storm (turning stormy), folded into a storm or heavy
rain, turning heavy, or combined with wind.

### 9.8 Wind

**Applies when** an hour has wind of **40 km/h** or more. Uses the first such
hour and its speed. Level is medium, or high from **60 km/h**.

| Case | Says |
| --- | --- |
| now | "Strong wind right now, around 45 km/h. Secure loose items outdoors." |
| later | "Wind picks up to 45 km/h around 3:00 PM. Secure loose items outdoors." |

**Merges:** combined with a storm, heavy rain or snow, or rain or snow.

### 9.9 Fog

**Applies when** an hour has visibility under **1 km**, or code 45 or 48.
Uses the first such hour.

| Case | Says |
| --- | --- |
| now | "It is foggy right now, with low visibility. Drive with care." |
| within an hour of the next sunrise | "Fog is likely around sunrise, with low visibility. Drive with care." |
| otherwise | "Fog is likely around 5:00 AM, with low visibility. Drive with care." |

### 9.10 Temperature swing

**Applies when** the window's warmest or coldest hour is **6 °C** or more
away from the current hour. If both are, the bigger change wins.

| Case | Says |
| --- | --- |
| warmer | "Expect it to warm up to 29° by around 2:00 PM." |
| colder | "Expect it to cool down to 14° by around 6:00 AM. Keep a layer handy." |

### 9.11 Tomorrow

**Applies** only from **6 PM** local time until midnight. Heading:
**Tomorrow**. The only low insight sent as a notification
(`OVERVIEW_NOTIFY_TOPICS`), as news only, never reminded.

Checked in this order; the first match wins:

| Case | Says |
| --- | --- |
| tomorrow's chance of rain ≥ 50% | "Rain is likely tomorrow with 60% chance, so plan ahead." |
| tomorrow's high ≥ 4 °C above today's | "Tomorrow will be warmer than today, with a high of 31°." |
| tomorrow's high ≥ 4 °C below today's | "Tomorrow will be cooler than today, with a high of 22°." |
| otherwise | nothing |

### 9.12 Sunset and sunrise

**Applies when**, by day, sunset is within **2 hours**, or, at night,
sunrise is within **3 hours**.

**The sun's hour** is the hourly hour nearest the event (6:12 PM → 6 PM,
6:40 PM → 7 PM; exactly half past → the later hour). The sentence says what
the weather at that hour brings. The first row that matches:

| Weather at the sun's hour | Says |
| --- | --- |
| thunderstorm code | "Thunderstorms at sunset, around 6:10 PM, best watched from indoors." |
| snow code, chance ≥ 50% | "Snow at sunset, around 6:10 PM, for a quiet, wintry evening." |
| chance ≥ 50%, or a freezing rain code | "A rainy sunset around 6:10 PM. Watch for a rainbow if the sun peeks through!" |
| fog (visibility < 1 km, or a fog code) | "A misty sunset around 6:10 PM, with soft, hazy light." |
| wind ≥ 60 km/h | "A very windy sunset around 6:10 PM, best enjoyed from a sheltered spot." |
| wind ≥ 40 km/h, clear or mainly clear (0, 1) | "Clear and windy for sunset around 6:10 PM, with crisp, fresh air." |
| wind ≥ 40 km/h, partly cloudy or overcast (2, 3) | "A windy sunset around 6:10 PM, with a few clouds." |
| overcast (3) | "A cloudy sunset around 6:10 PM, with soft, even light." |
| partly cloudy (2) | "A few clouds at sunset, around 6:10 PM, could bring some color." |
| clear or mainly clear (0, 1) | "Clear skies for sunset around 6:10 PM, a great evening to catch it." |

Sunrise uses the same sentences with "sunrise" (and "morning" for
"evening").

- Rain, snow, fog and wind use the same thresholds as their own rules, so
  the sun sentence never mentions weather no other rule would. From
  60 km/h, where wind becomes high, the sentences point to shelter. The
  wind's speed is left to the wind insight.
- **The time** is rounded to 10 minutes with "around" (6:12 PM → "around
  6:10 PM", 6:15 PM → "around 6:20 PM"). The sun's time doesn't move, so the
  sentence stays the same, and true, until the event.

**Without weather data** for the sun's hour (or with another code, such as
rain with a low chance), it counts down instead:

| Time to the event | Says |
| --- | --- |
| 57½ minutes or more | "The sun rises in about 2 hours, at 6:12 AM." (nearest hour, halves down, exact time alongside) |
| 2½ to 57½ minutes | "The sun sets in about 40 minutes." (nearest 5 minutes, halves down; never more than 5 minutes off) |
| under 2½ minutes | nothing ("in 5 minutes" would be wrong) |

**About / news:** it is about the event and happens now. A change of
weather at the sun's hour is news, said once (low); time passing isn't.

**Merges:** nothing. It is about the sun, not the weather, so rain at
sunset gives both sentences; they take turns, the rain first.

### 9.13 Calm

**Applies** always: the fallback when no other rule speaks.

Says: "Conditions should stay steady until about 7:00 AM." (end of the
window, rounded)

---

## 10. Writing messages

### 10.1 Varied wording

Each message has a key (`rain.start`, `calm`, …) and several wordings that
say the same thing with the same placeholders:

| Messages | Wordings |
| --- | --- |
| common: rain and snow, wind, fog, temperature, tomorrow, sunset and sunrise, calm | 4–5 |
| the weather at sunset and sunrise (20 messages) | 2 each |
| rare safety: storm, freezing rain, heavy rain or snow, extreme feels like, air quality, UV | 2, kept plain |
| two things at once: combined pairs, turning stormy, turning heavy | 2, one sentence, no advice after it |

A wording is picked at random **each time the overview opens by itself**.
Between openings the wording stays and only the values update, so the
phrasing never changes under the reader.

### 10.2 Form

- One whole sentence per message, with placeholders: `{time}`, `{temp}`,
  `{chance}`, `{speed}`, `{n}`, and `{start}`, `{end}`, `{heavy_time}` for
  two times. Never build a sentence from pieces: two things at once get
  their own message key.
- Counts use plural forms (`ngettext`): "1 minute", "5 minutes".
- Times follow the user's 12/24-hour setting, in the city's time zone.
- Temperatures show the number and a degree sign ("14°").
- Keep a message under about **90 characters** (the pill ellipsizes after
  that; the full text is in its tooltip).
- No "a"/"an" before a number: write "with 80% chance".

### 10.3 Times are rounded and hedged

A forecast is never minute-exact, so every predicted time is rounded and
said with "about", "around" or "by around":

| How far ahead | Rounded to | 6:38 AM becomes |
| --- | --- | --- |
| up to 3 hours | 10 minutes | "about 6:40 AM" |
| 3 to 5 hours | 30 minutes | "about 6:30 AM" |
| more than 5 hours | the hour | "about 7:00 AM" |

24-hour times round the same way ("06:40"). Counts are hedged too ("in
about 40 minutes"). Only the sunrise and sunset countdown gives an exact
time ("at 6:12 AM").

### 10.4 Tone

- **About the weather, for everyone.** Say what the weather does and what
  follows from it, not what to do with personal plans: no commute, laundry,
  watering plants or "best time to go out".
- **Full, friendly sentences.** Fold details like the chance into the
  sentence. Add a short second sentence only for advice ("Drive with
  care."), never to repeat the first. No headline style ("Rain likely 5 PM").
- **Sunset and sunrise are positive.** Say what each weather brings (color,
  soft light, a rainbow, a quiet snowy evening), not what it takes away: no
  "hide", "block" or "miss". Hedge what isn't certain ("could", "may",
  "often"). Plain words, no dramatic imagery (blankets, racing clouds,
  painted skies). Thunderstorms and very strong wind stay safety-first.

After changing a message, run `./update-pot`.

---

## 11. Adding a rule

1. **Describe it here**: priority, level, icon, topic, when it applies,
   what it says, and what it is about (6.3).
2. **Add its wordings** to `core/overview/messages.py` under a new key:
   4–5 for a common message, 2 for a rare safety one.
3. **Add its numbers**: its priority to `OVERVIEW_PRIORITIES`, any threshold
   to `config.py` (metric).
4. **Build it** in `core/overview/rules.py` from what exists:
   - "The first hour that …" is a `FirstHourRule` with an `HourTest` and a
     `Phrasing`.
   - Hour tests are in `core/overview/hour_tests.py`: `HasCode`, `AtLeast`,
     `Below`, `AnyOf`, `AllOf`, and the shared `IS_WET`, `IS_DRY`,
     `IS_SNOW`, `IS_FOGGY`, `IS_WINDY`, `IS_VERY_WINDY`. Reuse a shared one
     so two rules never disagree on what counts as rain or wind.
   - Only when that isn't enough, subclass `Rule` and write
     `evaluate(ctx)`, as `StormRule` and `SunRule` do.
   - Add it to `RuleBook.default()`, in priority order.
5. **Check validity**: its `valid_until` follows section 4, and it sets what
   it is about and when it happens (`Sentence.about` and `when`; `Phrasing`
   fills them in).
6. **Decide how it merges** if it often happens with another rule: a fold,
   a pair (with its own message keys), or a turning. Add it to `FOLDS`,
   `COMBINATIONS`, `TURNING_STORMY` or `TURNING_HEAVY` in `rules.py`, and to
   section 5 here.
7. **Add a test** in `tests/test_overview_rules.py`.
8. Run `./update-pot`.

---

## 12. Reading the debug log

Turn it on with:

```
gsettings set io.github.amit9838.mousam debug-mode true
```

Each run logs, in this order:

```
Overview folded: precipitation (rain.start) into storm
Overview not combined: storm + wind: one now, one later
Overview: 3 insights, 2 taking turns
  storm (storm): extreme, priority 100, said 1x, due in 1800s
  wind (wind): high, priority 55, new
  calm (calm): calm, priority 0, not taking turns
Overview opens (news): storm: Thunderstorms are likely around 4:00 PM with 80% chance of rain. … (runs again in 900s)
Overview next turn: wind (news, after the gap)
Overview channel: storm (news, extreme) -> notification overview-storm
```

| Line | Means |
| --- | --- |
| `turning stormy`, `folded`, `turning heavy`, `combined`, `not combined` | merging, and why not (once per run). E.g. `Overview turning stormy: precipitation (rain.start) + storm (17:00) -> rain_stormy.start` |
| one line per insight | topic, level, priority, and memory: `new`, `said 2x, due in 3600s`, `not repeated` (low, calm) or `not taking turns` (calm next to something else) |
| `opens (news)`, `opens (reminder)`, `silent update` | the sentence as shown, and when it runs again |
| `next turn` | due too; opens after the 15-minute gap |
| `channel` | where it went: `window`, `notification overview-<topic>`, or `nowhere` and why |
| `Notification … sent / withdrawn` | from `mousam.notifications`, with the reason for withdrawing |
