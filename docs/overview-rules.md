# Overview rules

This file is the **source of truth** for the overview: the one-line message
under the current conditions ("Rain is likely to start around
5:00 PM with 70% chance."). The code follows it:

- the rules: [`src/CORE_OverviewRules.py`](../src/CORE_OverviewRules.py), one `Rule` per rule, collected in `RuleBook.default()`
- the numbers: [`src/configs.py`](../src/configs.py), under "Overview rules"
- the wordings: [`src/CORE_OverviewMessages.py`](../src/CORE_OverviewMessages.py), several per message

**To change a rule, change this file first**, then the code and the numbers
to match. If the code and this file disagree, the code is wrong.

---

## The basics

### What a rule does

A rule looks at the forecast and either has something to say or stays
silent. When it speaks, it gives one **insight**:

- a **message**: one whole sentence, translated as a whole
- a **severity**: *info*, *warning* or *error*
- a **priority**: which insight wins when several rules speak
- an optional **icon**, shown before the message
- an optional **heading**, like *Tomorrow*; otherwise the window's heading is used
- **valid until**: the moment the message stops being true
- **how long it stays open** once shown, set by its severity

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

### Which insight wins

Every rule runs. Insights that are no longer true are dropped, and the rest
are sorted by priority, highest first. The calm rule always speaks, so there
is always at least one insight.

How the app picks from that list and when it shows it (timing, repeats) is
decided by the overview engine, not by the rules.

### How long a message stays open

A base time of 15 seconds, plus extra for severe messages:

| Severity | Base | Extra | Open for |
| --- | --- | --- | --- |
| info | 15 s | 0 s | 15 seconds |
| warning | 15 s | 7 s | 22 seconds |
| error | 15 s | 15 s | 30 seconds |

---

## The rules

From most to least important. "An hour" means an hour inside the window.

### 1. Storm

- **Priority** 100 · **Severity** error · **Icon** storm
- **Applies when** an hour has a thunderstorm weather code (95, 96 or 99).
- **Says**, for the first such hour:
  - now: "Thunderstorms are likely right now. Stay indoors if you can."
  - later: "Thunderstorms are likely around 4:00 PM. Plan to be indoors by then."

### 2. Freezing rain

- **Priority** 95 · **Severity** warning · **Icon** showers
- **Applies when** an hour has a freezing drizzle or freezing rain code
  (56, 57, 66 or 67).
- **Says**, for the first such hour:
  - now: "Freezing rain is likely right now. Roads and paths may be icy."
  - later: "Freezing rain is likely around 2:00 AM. Roads and paths may turn icy."

### 3. Heavy rain or snow

- **Priority** 90 · **Severity** warning · **Icon** showers, or snow
- **Applies when** an hour has a heavy rain code (65, 82), a heavy snow
  code (75, 86), or **7.6 mm** of precipitation or more.
- **Snow or rain**: snow when that hour has any snow code (71, 73, 75, 77,
  85, 86), otherwise rain.
- **Says**, for the first such hour:
  - now: "Heavy rain is likely right now. Expect puddles and slow roads." / "Heavy snow is likely right now. Travel may be slow."
  - later: "Heavy rain is likely around 3:00 PM. Keep an umbrella close." / "Heavy snow is likely around 3:00 PM. Travel may be slow after that."

### 4. Extreme feels like

- **Priority** 85 · **Severity** warning · **Icon** none
- **Applies when** the hottest hour feels like **40 °C** or more, or (if
  not) the coldest hour feels like **−15 °C** or less. Heat is checked first.
- **Says**, for that hottest or coldest hour:
  - heat, now: "It feels like 41° right now. Stay hydrated and seek shade."
  - heat, later: "It will feel like 41° by around 2:00 PM. Stay hydrated and seek shade."
  - cold, now: "It feels like −18° right now. Dress warmly, in layers."
  - cold, later: "It will feel like −18° by around 6:00 AM. Dress warmly, in layers."

### 5. Air quality

- **Priority** 80 · **Severity** warning · **Icon** none
- **Applies when** the **US AQI** reaches **151** (unhealthy) or more in
  an hour of the window.
- **Says**, for the first such hour:
  - now: "Air quality is unhealthy right now. Limit time outdoors if you can."
  - later: "Air quality turns unhealthy around 10:00 AM. Consider limiting time outdoors."

### 6. UV

- **Priority** 75 · **Severity** warning · **Icon** clear (sun)
- **Applies when** an hour has a UV index of **8** or more.
- **Says**, for the first run of such hours, ending at the end of its last hour:
  - now: "UV is very high until about 3:00 PM. Use sunscreen and cover up."
  - later: "UV will be very high from about 11:00 AM to 3:00 PM. Use sunscreen outdoors."

### 7. Rain or snow

- **Priority** 60 · **Severity** info · **Icon** showers, or snow
- **A wet hour** has a **50%** chance of precipitation or more.
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

- **Priority** 55 · **Severity** info, or warning from **60 km/h** ·
  **Icon** windy
- **Applies when** an hour has wind of **40 km/h** or more (strong).
- **Says**, for the first such hour and its speed:
  - now: "Strong wind right now, around 45 km/h. Secure loose items outdoors."
  - later: "Wind picks up to 45 km/h around 3:00 PM. Secure loose items outdoors."

### 9. Fog

- **Priority** 50 · **Severity** info · **Icon** fog
- **Applies when** an hour has visibility under **1 km**, or a fog code
  (45 or 48).
- **Says**, for the first such hour:
  - now: "It is foggy right now, with low visibility. Drive with care."
  - within an hour of the next sunrise: "Fog is likely around sunrise, with low visibility. Drive with care."
  - otherwise: "Fog is likely around 5:00 AM, with low visibility. Drive with care."

### 10. Temperature swing

- **Priority** 40 · **Severity** info · **Icon** none
- **Applies when** the window's warmest or coldest hour is **6 °C** or more
  away from the current hour's temperature. If both are, the bigger change
  wins.
- **Says**, for that hour:
  - warmer: "Expect it to warm up to 29° by around 2:00 PM."
  - colder: "Expect it to cool down to 14° by around 6:00 AM. Keep a layer handy."

### 11. Tomorrow

- **Priority** 30 · **Severity** info · **Icon** showers, or none ·
  **Heading** Tomorrow
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

- **Priority** 20 · **Severity** info · **Icon** sunset, or sunrise
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

- **Priority** 0 · **Severity** info · **Icon** none
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
are in `CORE_OverviewMessages.py`.

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

1. Describe it here: priority, severity, icon, when it applies, what it says.
2. Add its wordings to `CORE_OverviewMessages.py` under a new key: 4–5 for
   a common message, 2 for a rare safety one.
3. Add its priority to `OVERVIEW_PRIORITIES` and any threshold to
   `configs.py` (metric).
4. In `CORE_OverviewRules.py`, build it from what is there before writing a
   new class: a `FirstHourRule` with an `HourTest` (`HasCode`, `AtLeast`,
   `Below`, `AnyOf`) and a `Phrasing` covers "the first hour that …". Only
   when it needs more, subclass `Rule` and write `evaluate(ctx)`. Add it to
   `RuleBook.default()`, in priority order.
5. Make sure its `valid_until` follows "Every message must stay true".
6. Run `./update-pot`.
