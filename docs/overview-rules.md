# Overview rules

This file is the **source of truth** for the overview: the one-line message
under the current conditions ("Rain is likely to start around
5:00 PM with 70% chance."). The code follows it:

- the rules: [`src/core/overview/rules.py`](../src/core/overview/rules.py), one `Rule` per rule, collected in `RuleBook.default()`
- when it opens: [`src/core/overview/announce.py`](../src/core/overview/announce.py)
- the numbers: [`src/config.py`](../src/config.py), under "Overview rules"
- the wordings: [`src/core/overview/messages.py`](../src/core/overview/messages.py), several per message

**To change a rule, change this file first**, then the code and the numbers
to match. If the code and this file disagree, the code is wrong.

---

## The basics

### What a rule does

A rule looks at the forecast and either has something to say or stays
silent. When it speaks, it gives one **insight**:

- a **message**: one whole sentence, translated as a whole
- a **level**: *calm*, *low*, *medium*, *high* or *extreme* (see "Levels")
- a **priority**: which insight wins when several rules speak
- a **topic**: what it is about (rain, air, …); each topic has its own
  notification
- **what it is about**: the forecast hour or the event it describes, or
  "now". With the rule, the message and the level, this tells whether it
  is news (see "The same insight, or a new one")
- **when it happens**: the hour it starts, or now. Usually the same as what
  it is about; rain easing around 4 PM is about 4 PM but happens now.
  Combining uses it (see "Several things at once")
- an optional **icon**, shown before the message
- an optional **heading**, like *Tomorrow*; otherwise the window's heading is used
- **valid until**: the moment the message stops being true
- **how long it stays open** once shown, set by its level

### Levels

From nothing to say to danger. The level decides how the insight is shown,
how often it is repeated and whether it is sent as a notification (see
"When the overview opens"); within one level, the priority orders insights.

| Level | Meaning | Heading colour |
| --- | --- | --- |
| extreme | danger to people or property | error (red) |
| high | disrupts plans, or a health risk | warning (yellow) |
| medium | worth changing plans for | accent |
| low | nice to know | plain |
| calm | nothing to say | plain |

### The window: which hours the rules look at

The window follows the part of the day:

- **By day**: from now until sunset, but always at least **3 hours** ahead,
  so late afternoon still looks ahead. Heading: **Today**.
- **At night**: from now until the next sunrise. Heading: **Tonight**.
- **No sunrise or sunset** (polar day or night): the next **12 hours**.
  Heading: **Tonight**.

It is day when the next sunset comes before the next sunrise.

The window includes the current hour. "Now" in a message means the
current hour.

### Units

All thresholds are **metric**. With imperial units, temperatures (°F) and
wind speeds (mph) are converted to metric before they are compared.
Messages show values in the user's own units. Rain (mm) and visibility (m)
come from the API in metric in both systems.

### Every message must stay true

Each insight says until when it is right, and is never shown after that:

- Something happening **now** is right until the next full hour, when it
  is checked again.
- Something happening **around a time** ("around 4:00 PM") is right until
  that time.
- Something lasting **until about a time** is right until that time.
- **Tomorrow** is right until local midnight, when tomorrow becomes today.
- **Minutes away** ("in 40 minutes") is right while it is no more than
  **5 minutes** off.

### Ignore on fail

If a rule fails, for example on missing or odd data, it says nothing. The
other rules still run, so one broken rule never breaks the overview. The
failure is logged in debug mode only.

### Which insights are there

Every rule runs. Insights that are no longer true are dropped, and the rest
are sorted by priority, highest first. Then things that happen together are
combined or folded into one (see "Several things at once"). The calm rule
always speaks, so there is always at least one insight. Nothing is thrown
away: the insights take turns (below).

### When the overview opens, and with what

Code: `core/overview/announce.py`; the numbers are
`OVERVIEW_MIN_GAP_MINUTES` and the `OVERVIEW_REMIND_*` values in
`config.py`.

The overview opens when it has **something new to say**, and only now and
then to **remind** of something it has already said.

**The same insight, or a new one.** Two insights are the same when they
come from the same rule, with the same message, the same level, and
about the same forecast hour or event. Time passing doesn't change that
("in 40 minutes" becoming "in 35 minutes"). A changed forecast does: rain
moving from 4 PM to 7 PM, wind rising from medium to high, tomorrow turning
from warmer to rainy. A change in the chance alone (60% → 85% for the same
hour) is not news.

**What has been said is remembered** for each location: each insight, when
it was last announced, and how many times.

- Refreshes keep it, so the same forecast after a refresh is not news.
- An insight that goes away and comes back (a storm that comes and goes)
  is still remembered, so it doesn't count as news again. It is forgotten
  4 hours after it was last true.
- Clicking the info button counts as announcing the insight it shows.
- Switching location, or turning off both the overview and notifications,
  starts over.

**When each insight is due.**

| The insight | Due |
| --- | --- |
| never said | now: it is **news** |
| said before, medium or above | a **reminder**, after 30 minutes (extreme), 60 (high) or 120 (medium); each next reminder waits twice as long, at most 4 hours |
| said before, low | never again: low is said once |
| calm | said once per location; never reminded |

So an unchanged high insight opens at 0, 60, 180 and 420 minutes, then
every 4 hours; an unchanged storm after 30, 90 and 210 minutes. A busy forecast
opens more often because it has more news, not because of a timer.

**Calm takes no turn** while anything else is worth saying; it is shown only
when it is the only insight.

**Which one opens.** Among the insights that are due: news before
reminders, then the highest level, then the highest priority. So
something more urgent turning up (a storm) opens first, at once.

**The gap.** Nothing opens within **5 minutes** of the last opening; an
insight that is due opens as soon as those 5 minutes are up.

**Several things at once: combine, fold, or the next turn.** Every
opening shows **one sentence**. Two things that happen together become one
sentence only when a natural one exists; otherwise the second one gets the
next turn. A single insight is always shown as it is: rain with no storm or
wind is the plain rain sentence.

*Combine.* A known pair becomes one sentence, with its own message, when
both happen within **60 minutes** of each other, and both now or both
later (one now and one later is not combined: "right now" would be wrong
for one of them, "from around" for the other):

| Pair | Message |
| --- | --- |
| storm + wind | "Thunderstorms with strong wind, around 45 km/h, are likely from around 4:00 PM." |
| storm + heavy rain | "Thunderstorms with heavy rain are likely from around 4:00 PM." |
| heavy rain + wind | "Heavy rain and strong wind, around 45 km/h, are likely from around 4:00 PM." |
| heavy snow + wind | "Heavy snow and strong wind, around 45 km/h, are likely from around 4:00 PM." |
| rain + wind | "Rain and strong wind, around 45 km/h, are likely from around 4:00 PM." |
| snow + wind | "Snow and strong wind, around 45 km/h, are likely from around 4:00 PM." |

Each also has a "right now" message ("Thunderstorms with strong wind,
around 45 km/h, are likely right now."). The pairs are tried in this order,
each insight used once, so storm + heavy rain + wind becomes storm + wind,
and the heavy rain gets the next turn. The combined insight:

- says the earlier of the two times, as "from around", so it is true for
  both; it is true until the earlier of the two stops being true
- has the higher level of the two, and the rule, topic and priority of the
  more important one (storm, then heavy rain or snow, then rain or snow,
  then wind)
- covers both: announcing it counts as saying each of them, so when the
  wind drops later, the storm alone is not news again

*Fold.* Some insights already say another one, within the same 60 minutes
(and both now or both later):

| Kept | Folded into it |
| --- | --- |
| storm | rain or snow |
| heavy rain | rain |
| heavy snow | snow |

The folded insight isn't shown, but it counts as said with the one it is
folded into. Folding comes before combining.

*The next turn.* Anything not combined or folded stays its own insight:
a storm now and UV three hours later, a third urgent thing, one now and
one later. It is news, so it opens on its own once the 5-minute gap is
over. Nothing is lost, and nothing is shown at once.

**Between openings** the text on screen is kept up to date without opening
(the values change, the wording stays). When the shown insight stops being
true, the most important remaining one takes its place, also without opening.

**Where it is shown: one place at a time.**

- While the main window can be seen, the overview opens in it, for news
  and reminders.
- While the window is minimized, hidden by compact mode, or otherwise out of
  sight, it is sent as a desktop notification instead (the city as its
  title, the sentence as its body; clicking it opens the main window). Only
  news of medium or above is sent, plus reminders of extreme ones (storms).
  Low and calm are never sent.

**One notification per topic.** Each topic has its own notification, so
air quality and rain can be there side by side. A new message replaces only
the one on the same topic: heavy rain shares the rain topic, so "Heavy rain
around 5:00 PM" replaces "Rain is likely around 4:00 PM". A combined insight
is sent under the more important topic and covers the other: "storm + wind"
withdraws the wind notification.

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

A notification is **withdrawn** when it is no longer right or needed:

- its topic has no insight any more (it stopped being true, or the forecast
  changed: rain turning to snow withdraws rain); a combined one as soon as
  either of its parts stops being true, since its sentence names both
- the location changes
- notifications are turned off (or the overview and notifications both are)
- the main window comes into view: the overview shows it there

Either can be turned off in Preferences: *Weather Overview* and *Show
Notifications*. The forecast is only worked out while at least one is on.

| Overview | Notifications | Window in sight | Window out of sight |
| --- | --- | --- | --- |
| on | on | overview | notification |
| on | off | overview | nothing |
| off | on | nothing | notification |
| off | off | nothing (no processing) | nothing |

**Refreshes don't count.** A refresh (Ctrl+R, auto-refresh, changing units,
clock or icons) keeps what has been said, so it neither opens the overview
nor resets the reminders. Switching location, or turning off both the
overview and notifications, starts over.

### How long a message stays open

A base time of 15 seconds, plus extra for urgent messages:

| Level | Base | Extra | Open for |
| --- | --- | --- | --- |
| calm, low, medium | 15 s | 0 s | 15 seconds |
| high | 15 s | 7 s | 22 seconds |
| extreme | 15 s | 15 s | 30 seconds |

---

## The rules

From most to least important. "An hour" means an hour inside the window.

### 1. Storm

- **Priority** 100 · **Level** extreme · **Icon** storm · **Topic** storm
- **Applies when** an hour has a thunderstorm weather code (95, 96 or 99).
- **Says**, for the first such hour:
  - now: "Thunderstorms are likely right now. Stay indoors if you can."
  - later: "Thunderstorms are likely around 4:00 PM. Plan to be indoors by then."

### 2. Freezing rain

- **Priority** 95 · **Level** high · **Icon** showers · **Topic** freezing
- **Applies when** an hour has a freezing drizzle or freezing rain code
  (56, 57, 66 or 67).
- **Says**, for the first such hour:
  - now: "Freezing rain is likely right now. Roads and paths may be icy."
  - later: "Freezing rain is likely around 2:00 AM. Roads and paths may turn icy."

### 3. Heavy rain or snow

- **Priority** 90 · **Level** high · **Icon** showers, or snow · **Topic** rain, or snow
- **Applies when** an hour has a heavy rain code (65, 82), a heavy snow
  code (75, 86), or **7.6 mm** of precipitation or more.
- **Snow or rain**: snow when that hour has any snow code (71, 73, 75, 77,
  85, 86), otherwise rain.
- **Says**, for the first such hour:
  - now: "Heavy rain is likely right now. Expect puddles and slow roads." / "Heavy snow is likely right now. Travel may be slow."
  - later: "Heavy rain is likely around 3:00 PM. Keep an umbrella close." / "Heavy snow is likely around 3:00 PM. Travel may be slow after that."

### 4. Extreme feels like

- **Priority** 85 · **Level** high · **Icon** none · **Topic** feels_like
- **Applies when** the hottest hour feels like **40 °C** or more, or (if
  not) the coldest hour feels like **−15 °C** or less. Heat is checked first.
- **Says**, for that hottest or coldest hour:
  - heat, now: "It feels like 41° right now. Stay hydrated and seek shade."
  - heat, later: "It will feel like 41° by around 2:00 PM. Stay hydrated and seek shade."
  - cold, now: "It feels like −18° right now. Dress warmly, in layers."
  - cold, later: "It will feel like −18° by around 6:00 AM. Dress warmly, in layers."

### 5. Air quality

- **Priority** 80 · **Level** high · **Icon** none · **Topic** air
- **Applies when** the **US AQI** reaches **151** (unhealthy) or more in
  an hour of the window.
- **Says**, for the first such hour:
  - now: "Air quality is unhealthy right now. Limit time outdoors if you can."
  - later: "Air quality turns unhealthy around 10:00 AM. Consider limiting time outdoors."

### 6. UV

- **Priority** 75 · **Level** high · **Icon** clear (sun) · **Topic** uv
- **Applies when** an hour has a UV index of **8** or more.
- **Says**, for the first run of such hours, ending at the end of its last hour:
  - now: "UV is very high until about 3:00 PM. Use sunscreen and cover up."
  - later: "UV will be very high from about 11:00 AM to 3:00 PM. Use sunscreen outdoors."

### 7. Rain or snow

- **Priority** 60 · **Level** medium · **Icon** showers, or snow · **Topic** rain, or snow
- **A wet hour** has a **50%** chance of precipitation or more, a **dry
  hour** less. An hour with no data is neither.
- **Snow or rain**: snow when that hour has a snow code, otherwise rain.
- **Says**:
  - wet now, and a dry hour later in the window:
    "Rain is likely right now, easing off around 4:00 PM." (the first dry hour)
  - wet now, and wet all through the window:
    "Rain is likely to keep falling until about 6:00 PM." (the end of the window, rounded)
  - dry now, wet later:
    "Rain is likely to start around 5:00 PM with 70% chance." (the first wet hour and its chance)
  - dry all through the window: nothing.
- Snow uses the same sentences with "Snow".

### 8. Wind

- **Priority** 55 · **Level** medium, or high from **60 km/h** ·
  **Icon** windy · **Topic** wind
- **Applies when** an hour has wind of **40 km/h** or more (strong).
- **Says**, for the first such hour and its speed:
  - now: "Strong wind right now, around 45 km/h. Secure loose items outdoors."
  - later: "Wind picks up to 45 km/h around 3:00 PM. Secure loose items outdoors."

### 9. Fog

- **Priority** 50 · **Level** medium · **Icon** fog · **Topic** fog
- **Applies when** an hour has visibility under **1 km**, or a fog code
  (45 or 48).
- **Says**, for the first such hour:
  - now: "It is foggy right now, with low visibility. Drive with care."
  - within an hour of the next sunrise: "Fog is likely around sunrise, with low visibility. Drive with care."
  - otherwise: "Fog is likely around 5:00 AM, with low visibility. Drive with care."

### 10. Temperature swing

- **Priority** 40 · **Level** low · **Icon** none · **Topic** temperature
- **Applies when** the window's warmest or coldest hour is **6 °C** or more
  away from the current hour's temperature. If both are, the bigger change
  wins.
- **Says**, for that hour:
  - warmer: "Expect it to warm up to 29° by around 2:00 PM."
  - colder: "Expect it to cool down to 14° by around 6:00 AM. Keep a layer handy."

### 11. Tomorrow

- **Priority** 30 · **Level** low · **Icon** showers, or none ·
  **Heading** Tomorrow · **Topic** tomorrow
- **Applies** only from **6 PM** local time, until midnight.
- **Says**, checking in this order:
  - tomorrow's chance of rain is **50%** or more:
    "Rain is likely tomorrow with 60% chance, so plan ahead."
  - tomorrow's high is **4 °C** or more above today's:
    "Tomorrow will be warmer than today, with a high of 31°."
  - tomorrow's high is **4 °C** or more below today's:
    "Tomorrow will be cooler than today, with a high of 22°."
  - otherwise: nothing.

### 12. Sunset and sunrise

- **Priority** 20 · **Level** low · **Icon** sunset, or sunrise · **Topic** sun
- **Applies when**, by day, sunset is within **2 hours**, or, at night,
  sunrise is within **3 hours**.
- **Says**:
  - under an hour away: "The sun sets in about 40 minutes." The minutes are rounded to
    the nearest 5 (exact halves round down), and the message is never more
    than 5 minutes off while shown.
  - an hour or more away: "The sun rises in about 2 hours, at 6:12 AM." The hours
    are rounded to the nearest whole hour (halves down), with the exact time
    alongside.
  - in the last 2½ minutes: nothing, since "in 5 minutes" would be wrong.
- The minutes form takes over from 57½ minutes before the event.

### 13. Calm

- **Priority** 0 · **Level** calm · **Icon** none · **Topic** calm
- **Applies** always. It is the fallback when no other rule speaks.
- **Says**: "Conditions should stay steady until about 7:00 AM." (the end of the window, rounded)

---

## Varied wording

Each message has a key (`rain.start`, `calm`, …) and several wordings that
say the same thing, so the overview does not read the same every time:

- **Common messages** (rain and snow, wind, fog, temperature, tomorrow,
  sunset and sunrise, calm): **4–5 wordings**.
- **Rare safety messages** (storm, freezing rain, heavy rain or snow,
  extreme feels like, air quality, UV): **2 wordings**, kept plain.

The examples in this file are the first wording of each message; the rest
are in `core/overview/messages.py`.

**When the wording changes.** One wording is picked at random each time the
overview is announced (opens by itself). Between announcements the wording
stays the same, and only the values update ("about 40 minutes" becomes
"about 30 minutes"), so the text never changes its phrasing under the reader.

**Every wording of a message:**

- says the same thing, with the same placeholders
- follows "Writing messages" below

## Writing messages

- One whole sentence per message, with placeholders (`{time}`, `{temp}`,
  `{chance}`, `{speed}`, `{n}`). Never build a sentence from pieces.
- Counts use plural forms (`ngettext`): "1 minute", "5 minutes".
- Times follow the user's 12/24-hour setting, in the city's time zone.
- **Predicted times are rounded and hedged.** A forecast is never
  minute-exact, so every predicted time is rounded, and the sentence always
  says so with "about", "around" or "by around": "Rain is likely to start
  around 5:00 PM", "until about 6:30 AM", "cool down to 14° by around
  6:00 AM". The further
  ahead, the rounder:

  | How far ahead | Rounded to | Example (6:38 AM) |
  | --- | --- | --- |
  | up to 3 hours | 10 minutes | "about 6:40 AM" |
  | 3 to 5 hours | 30 minutes | "about 6:30 AM" |
  | more than 5 hours | the hour | "about 7:00 AM" |

  24-hour times round the same way ("06:40"). Counts are hedged too:
  "The sun sets in about 40 minutes".
- **Only sunrise and sunset are exact**, since they are known to the
  minute: "The sun rises in about 2 hours, at 6:12 AM."
- Temperatures show the number and a degree sign ("14°"); the unit is in
  the current conditions next to it.
- **Full, friendly sentences.** Say what happens in a complete sentence
  and fold details like the chance into it ("Rain is likely to start around
  5:00 PM with 70% chance."). Add a short second sentence only for advice
  ("Drive with care."), never to repeat what the first one said. Avoid
  clipped headline style ("Rain likely 5 PM").
- Keep a message under about 90 characters: the pill shows that much before
  it ellipsizes (the full text is in its tooltip).
- No "a"/"an" before a number ("a 80% chance"): the right article depends
  on the number. Write "with 80% chance".
- After changing a message, run `./update-pot`.

## Adding a rule

1. Describe it here: priority, level, icon, topic, when it applies, what
   it says, and what it is about (for "The same insight, or a new one").
2. Add its wordings to `core/overview/messages.py` under a new key: 4–5 for
   a common message, 2 for a rare safety one.
3. Add its priority to `OVERVIEW_PRIORITIES` and any threshold to
   `config.py` (metric).
4. In `core/overview/rules.py`, build it from what is there before writing a
   new class: a `FirstHourRule` with an `HourTest` (`HasCode`, `AtLeast`,
   `Below`, `AnyOf`) and a `Phrasing` covers "the first hour that …". Only
   when it needs more, subclass `Rule` and write `evaluate(ctx)`. Add it to
   `RuleBook.default()`, in priority order.
5. Make sure its `valid_until` follows "Every message must stay true".
6. Run `./update-pot`.
