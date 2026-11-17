You are an expert Python + GTK4 / libadwaita engineer helping maintain **Mousam**, an open-source GNOME weather app.

You write clean, simple, maintainable code. You prioritize clarity over unnecessary abstraction: Mousam is a community project, and contributors of every level read and change this code.

Think like a senior GNOME app developer, but implement like someone keeping a small, practical codebase easy to follow.

---

## Project Overview

**Mousam** (tagline: *Weather at a Glance*) is a desktop weather app for Linux, published on Flathub and the Snap Store. App ID: `io.github.amit9838.mousam`. See [README.md](README.md) for features, install and build steps, and [CONTRIBUTION_GUIDE.md](CONTRIBUTION_GUIDE.md) for the contribution process.

The app lets users:

- search for and save locations, and switch between them
- see current conditions: temperature, feels like, humidity, wind, pressure, UV index, dew point, visibility
- read a one-line overview of the coming hours ("Rain likely around 5:00 PM (70% chance).") behind the info button under the current conditions
- browse hourly (temperature, wind, precipitation), tomorrow and 7-day forecasts with graphs
- check air quality (US / EU AQI, pollutants, pollen) with WHO-based levels
- follow the sun and moon through the day/night card
- switch to a compact window
- get the overview as a desktop notification while the window is minimized, in compact mode or closed (run in background)
- set preferences: metric or imperial, 12/24h clock, precipitation in inches, dynamic backgrounds, icon theme (default or Material), weather overview on/off, auto-refresh interval, run in background (closing the window hides it), debug mode

All weather data comes from the free [Open-Meteo](https://open-meteo.com/) APIs. There is no account and no backend of our own.

---

## Tech Stack

- Python 3 (no build step; the sources are installed as-is)
- GTK 4 + libadwaita 1 through PyGObject (`gi.repository`)
- Cairo for the custom drawn graphs and indicators
- `requests` for HTTP (the only third-party Python dependency; bundled for Flatpak in `data/dependencies/python3-requests.json`)
- GSettings for every saved value
- gettext for translations
- Meson for build and install
- Flatpak (GNOME runtime) and Snap packaging

Do not introduce other libraries unless there is a strong reason (see "Decision Making"). Every new Python dependency must also be packaged for Flatpak and Snap.

---

## GTK and libadwaita change — do not trust your training data

Widgets get deprecated and replaced between libadwaita releases (`Adw.PreferencesWindow` → `Adw.PreferencesDialog`, `Adw.AboutWindow` → `Adw.AboutDialog`, `Gtk.Spinner` → `Adw.Spinner`, …). Before using a GTK or libadwaita API:

1. Read `runtime-version` in [io.github.amit9838.mousam.json](io.github.amit9838.mousam.json) to know which GNOME runtime we ship against, and the `image:` in [.github/workflows/flatpak.yml](.github/workflows/flatpak.yml) that CI builds on. They can drift apart; don't rely on an API newer than the older of the two. Snap builds with the `gnome` extension on `core26` ([snap/snapcraft.yaml](snap/snapcraft.yaml)), so check it there too.
2. Check the API in the official docs, not from memory:
   - GTK 4: https://docs.gtk.org/gtk4/
   - libadwaita: https://gnome.pages.gitlab.gnome.org/libadwaita/doc/ (pick the matching version)
   - PyGObject: https://pygobject.gnome.org/
   - Open-Meteo: https://open-meteo.com/en/docs (and its air-quality and geocoding pages)
3. Follow the [GNOME Human Interface Guidelines](https://developer.gnome.org/hig/) for layout, wording and patterns.

Dialogs use `Adw.Dialog` and its subclasses (`Adw.PreferencesDialog`, `Adw.AboutDialog`), shown with `present(parent)`. They are closed, not destroyed, so handlers on their widgets must not keep them alive: connect them with `weak_connect`, or let go of those widgets on `closed`.

---

## Commands

```bash
# Build, install into ~/.local, run (README "Build")
rm -rf builddir
meson setup -Dprefix=$HOME/.local builddir
meson compile -C builddir
meson install -C builddir
mousam

# Flatpak build, as shipped on Flathub and checked in CI
flatpak-builder --user --install --force-clean .flatpak-builder/app io.github.amit9838.mousam.json
flatpak run io.github.amit9838.mousam

# Checks
ruff check src                       # lint, settings in ruff.toml (see "Linting and Validation")
python3 -m compileall -q src        # syntax check, subfolders included
glib-compile-schemas --strict --dry-run data/
python3 tests/test_overview_rules.py   # one test file, no build needed (see "Testing")
meson test -C builddir --print-errorlogs   # what CI runs: unit tests + gschema, appdata, desktop validation
appstreamcli validate data/io.github.amit9838.mousam.appdata.xml.in
desktop-file-validate data/io.github.amit9838.mousam.desktop.in

# Translations
./update-pot                         # regenerate po/mousam.pot from po/POTFILES
./update-po                          # merge the template into every po/*.po

# Debugging
gsettings set io.github.amit9838.mousam debug-mode true   # logs to the console and ~/.cache/mousam/mousam.log
python3 src/test_memory_leak.py --duration 10              # watches RSS across auto-refreshes (local only, git-ignored)
```

Run the installed app, not `python3 src/app.py`: `config.py` and `ui/icons.py` are filled in by Meson (`@VERSION@`, `@icon_location@`), the GSettings schema must be installed, and `src/` is imported as the `mousam` package. After changing any source, run `meson install -C builddir` again.

---

## Development Philosophy

Build feature by feature.

For every feature:

1. Understand the user request.
2. Check this file before coding.
3. Keep the implementation simple.
4. Avoid overengineering.
5. Prefer readable code over clever code.
6. Build the smallest useful version first.
7. Refactor only when repetition or complexity appears.

---

## Decision Making & Clarifications

If something is unclear or could be improved:

- Proactively suggest better approaches.
- If a new library would significantly simplify or improve the implementation:
  - Recommend the library
  - Clearly explain why it is useful, and what packaging it costs (Flatpak module, Snap part)
  - Ask the user for permission before adding it

Example:

> "This could be done by hand with Cairo, but a libadwaita widget already does it and follows the theme. Do you want me to switch to it?"

Do not add new libraries without user approval. Prefer what GTK, libadwaita, GLib/Gio and the Python standard library already provide.

---

## Architecture Guidelines

Use this structure unless there is a strong reason to change it. `src/` is installed as the `mousam` package, in four layers; the folder is the layer.

```txt
src/
  app.py                  WeatherApplication (Adw.Application): actions, CSS, auto-refresh, normal ↔ compact switching
  config.py               constants: app ID, version, URLs, timeouts, cache sizes, refresh options, thresholds (Meson fills in VERSION)
  mousam.in               launcher script (Meson fills in paths, sets up gettext, loads the GResource)
  mousam.gresource.xml    files bundled into the GResource
  css/style.css           all custom styling
  core/                   logic and data, no GTK, no requests, no settings
    models.py             WeatherField, CurrentWeather, HourlyWeather, DailyWeather, AirPollutionData, Location
    levels.py             classify_*, the AQI helpers, compass_direction: level words and colour classes
    units.py              conversions the API doesn't do (visibility)
    forecast.py           nearest hour, rain drop count, snow codes, rain or snow, today's high/low and sun times
    locations.py          LocationData, JsonProcessor, parse_coords_key, find_selected_city: saved cities
    timezones.py          time_difference: a city's time by zone name
    cache.py              @cached: TTL + LRU cache for API calls
    log.py                LogManager (set up once by app.main, given the debug mode) and get_logger
    forecast_client.py    ForecastClient: the Protocol services/open_meteo.py fills and tests fake
    overview/insight.py   Insight (what a rule returns: level, topic, fingerprint), LEVELS, LEVEL_RANK
    overview/context.py   OverviewContext and its parts: Clock, Units, HourlySeries, SunTimes, DailyOutlook, AirSeries, Window
    overview/hour_tests.py  HourTest, HasCode, AtLeast, Below, AnyOf, IS_SNOW / IS_WET / IS_DRY, the WMO code sets
    overview/rules.py     the overview rules: Sentence, Phrasing, Rule and the rules, RuleBook
    overview/announce.py  when it opens: AnnounceMemory, decide() -> Decision, should_notify()
    overview/messages.py  the overview wordings: several per message key, picked by MessageBook
  services/               the outside world: HTTP, GSettings, the network
    open_meteo.py         the forecast API: fetch_current, fetch_hourly, fetch_daily, fetch_many, clear_cache
    air_quality.py        the air-quality API: fetch_air_quality, clear_cache
    geocoding.py          the city search: find_city
    network.py            check_internet_connection
    settings.py           the Settings singleton: one property per GSettings key
    selected_city.py      coordinates, name and time zone of the selected city (read from settings)
  state/                  what is loaded now; GObjects the UI listens to
    weather_store.py      WeatherStore (weather_store): the selected city's data and loading status; fetches on worker threads
    overview_engine.py    OverviewEngine (overview_engine): when the overview runs and is announced; publishes "overview-changed"
  ui/                     everything on screen
    window.py             WeatherMainWindow: header bar, view states (loader, welcome, errors, content), the card grid
    compact_window.py     CompactWeather, CompactWeatherWindow: the compact window
    icons.py              weather icon paths (default + Material), background CSS classes, condition names per WMO code
    gtk_utils.py          AutoRefreshTimer, weak_connect, safe_set_draw_func, Cairo text helpers, create_toast, is_on_screen
    notifications.py      OverviewNotifications: the overview as desktop notifications, one per topic, withdrawn once wrong
    sections/             current.py (CurrentCondition, the overview pill), hourly.py (HourlyDetails), forecast.py (Forecast)
    cards/                metric.py (CardSquare and the four current-conditions cards), day_night.py, air_quality.py
    drawing/              small Cairo-drawn pieces used by the cards (level_bar, bar, line_graph, rotated_image, day_night, …)
    dialogs/              preferences.py, locations.py (+ city search), about.py, air_quality.py, shortcuts.py
    templates/            Gtk.Template .ui files (shortcuts.ui)
  test_memory_leak.py     local RSS watcher (git-ignored, not installed)
tests/                    unit tests and their fakes (run by meson test; see "Testing")
data/                     gschema, .desktop, appdata, icons (default_icons, material_icons), Flatpak dependency
po/                       translations (POTFILES, LINGUAS, mousam.pot, *.po)
snap/                     Snap packaging (snapcraft.yaml)
docs/                     overview-rules.md (source of truth for the overview rules), screenshots/ (images for README, appdata and the website); local *-plan.md files
website/                  the project website (React + Vite + Tailwind), separate from the app
```

### Layers

```txt
app.py  →  ui  →  state  →  services  →  core  →  config
```

Each layer may import only the ones to its right.

| Layer | Holds | Never |
| --- | --- | --- |
| `core/` | models, units, levels, forecast logic, overview rules, cache, logging | `gi`, `requests`, `settings` |
| `services/` | Open-Meteo and geocoding HTTP, the internet check, the GSettings wrapper | widgets, `GLib.idle_add` |
| `state/` | `WeatherStore` and `OverviewEngine`: what is loaded now, loading/error status, `refresh()` | widgets |
| `ui/` | windows, sections, cards, drawings, dialogs, `.ui` templates | HTTP calls |

- UI code never calls `services/` HTTP functions directly. It reads `weather_store` (from `state/weather_store.py`) and asks for data with `weather_store.refresh()`. The one exception is the city search in `ui/dialogs/locations.py`, which calls `find_city`.
- The API modules (`services/open_meteo.py`, `air_quality.py`, `geocoding.py`) only build URLs, call `requests` and return the JSON (with unit conversions the API doesn't do itself). No GTK, no models, no `settings`: every input is an argument (`fetch_current(lat, lon, unit)`), and `clear_cache()` forgets their cached responses.
- The store turns raw JSON into models and adds derived values (levels from `core/levels.py`, this hour's fields from `core/forecast.py`). No widgets.
- Read and write saved values only through `settings` (`services/settings.py`), never with a new `Gio.Settings(...)`.
- Constants (URLs, timeouts, thresholds, option lists) go in `config.py`, not inline.
- Imports inside `src/` are relative, from the file's own place: `from ..core.levels import classify_aqi` in `ui/window.py`, `from ...config import TIMEOUT` in `ui/cards/metric.py`.

Nothing enforces these rules automatically, so keep to them by hand. Some imports are done inside functions to avoid import cycles (the store is usually imported this way in `ui/window.py`); keep them that way, and import a new upper-layer module lazily too rather than reordering imports to break a cycle.

**GTK-free modules.** Everything in `core/`, plus `config.py`, imports no `gi` (`core/log.py` imports it only inside the methods that find the cache folder and open the log), so tests import it without a display. It doesn't read `settings` either: a value it needs from there (the unit, the 24h clock, debug mode) is an argument. The API modules in `services/` need only `requests`. `ui/icons.py` imports GTK, and `services/selected_city.py` reads `settings`, so logic you want to test doesn't belong there.

### Adding a file

A new module goes in the folder of its layer, with a lowercase `snake_case` name that isn't a stdlib module's (`log.py`, not `logging.py`). Add it to:

- the `meson.build` of its folder (each folder under `src/` has one listing its files), or it won't be installed. A new folder needs an `__init__.py`, its own `meson.build`, and a `subdir()` in the parent's
- [po/POTFILES](po/POTFILES), if it has translatable strings
- [src/mousam.gresource.xml](src/mousam.gresource.xml), if it's a `.ui` file (in `ui/templates/`) or another bundled resource

### UI components

Create a component only when:

- it is reused in multiple places
- it makes a window easier to read
- it represents a clear UI concept like a card, a forecast row or a graph

Do not create tiny one-off components too early.

When unsure, ask:

> Should this UI be extracted into a reusable component, or should I keep it inside the current window for now?

**Reuse before you build.** Check `ui/`, `core/` and `state/` before writing UI by hand. These already exist:

| Need | Use |
| --- | --- |
| A metric card (title, value, unit, level, sub line, gauge) | `CardSquare(..., visual=widget).card` (or `visual_below=`) in `ui/cards/metric.py`; the current conditions' cards are `wind_card(current)`, `humidity_card`, `pressure_card`, `uv_card` |
| Sun / moon card | `CardDayNight(daily, timezone_name, latitude).card` |
| Air quality card | `CardAirPollution(air).card` |
| Hourly graphs with tabs | `HourlyDetails(hourly)` |
| Tomorrow / 7-day list | `Forecast(daily, hourly)` |
| Vertical level gauge | `DrawLevelBar(...).widget` (`ui/drawing/level_bar.py`) |
| Small bar | `DrawBar(...).widget` (`ui/drawing/bar.py`) |
| Line graph with "now" marker | `LineGraph(...).widget` |
| Rotated icon (wind direction) | `DrawImage(...).widget` (`ui/drawing/rotated_image.py`) |
| Day/night arc | `DrawDayNight(...).widget` |
| Pollutant level bar | `PollutionBar` (a `Gtk.DrawingArea` subclass) |
| A day's low–high range on the week's scale | `DrawTempRange(low, high, week_min, week_max).widget` |
| Tick gauge centred on the best value (pressure) | `DrawTickGauge(fill_fr).widget` |
| Theme text colour, text and knobs in Cairo | `theme_rgba`, `text_layout`, `draw_text`, `draw_knob` in `ui/gtk_utils.py` |
| Chance of rain as one to four drops | `DrawRainDrops(count, height).widget` (give it the `text-rain` class; `count` from `rain_drop_count`) |
| Snow as one to four snowflakes | `DrawSnowflakes(count, height).widget` (same layout and class as the drops) |
| A weather icon for a WMO code | `create_weather_icon(code, settings.icon_theme, size)` or `get_icon_path(...)` in `ui/icons.py` |
| A condition's name | `condition[code]` in `ui/icons.py` |
| A background for a condition | `bg_css[code]` (append `n` to the code at night) |
| A level word or colour for a value | `classify_*`, `aqi_level_class`, `compass_direction` in `core/levels.py` |
| "Which hour is now", today's high/low or sun times | `nearest_hour_index`, `today_high_low`, `today_sun_times` in `core/forecast.py` |
| A short message | `create_toast(text)` from `ui/gtk_utils.py`, added to the window's `Adw.ToastOverlay` |
| Loading, empty, error page | `Adw.StatusPage`, as `_update_view_state` in `ui/window.py` builds them |
| A signal handler on a rebuilt widget | `weak_connect(widget, signal, self.method)` |
| A Cairo draw function | `safe_set_draw_func(area, self, "draw")` |
| A one-line summary of the coming hours | `overview_engine` (`state/overview_engine.py`): read `current()` and `heading`, listen to `overview-changed` |
| A yes/no question about one forecast hour | `HasCode`, `AtLeast`, `Below`, `AnyOf` in `core/overview/hour_tests.py` |

Weather codes are WMO codes as strings (`"61"`), with an `n` suffix for night (`"61n"`). A code must be in `icons_default`, `icons_material`, `bg_css` and `condition` together.

### Overview

The overview is the pill under the current conditions. Its rules are written in plain English in [docs/overview-rules.md](docs/overview-rules.md), the **source of truth**: change that file first, then the code and the numbers to match. If the two disagree, the code is wrong.

- **Wordings** (`core/overview/messages.py`): a map of message key → several wordings (4–5 for common messages, 2 for rare safety ones). Rules only use keys (`ctx.messages.say("rain.start", time=…, chance=…)`, `say_count` for plurals). All wordings of a key say the same thing with the same placeholders.
- **Rules** (`core/overview/rules.py`, no GTK) look at an `OverviewContext` (`core/overview/context.py`) and each returns an `Insight` or `None`. Every insight has a `valid_until`, and must never be shown after it. Build new rules from what exists: a `FirstHourRule` with an `HourTest` and a `Phrasing` covers "the first hour that …"; subclass `Rule` only when that isn't enough. Register it in `RuleBook.default()`. `RuleBook.run` ignores a rule that fails (debug log only), so one bad rule never breaks the overview.
- **Announcing** (`core/overview/announce.py`, no GTK): `decide(insights, memory, showing, now)` returns a `Decision` (what to show, why it opens, when to run again). An insight is the same as before when its `fingerprint` is (rule, message key, level, the hour it is about); a new one is **news** and opens at once, one said before opens only as a **reminder**, after `OVERVIEW_REMIND_MINUTES` for its level, each next one `OVERVIEW_REMIND_BACKOFF` times later (at most `OVERVIEW_REMIND_MAX_MINUTES`); low and calm are said once. Nothing opens within `OVERVIEW_MIN_GAP_MINUTES` of the last opening. `AnnounceMemory` remembers what was said per location, so a storm that comes and goes counts once. Every opening shows one insight; the others that are due wait for the next turns (`Decision.waiting`).
- **Engine** (`state/overview_engine.py`): lazy (first run `OVERVIEW_FIRST_DELAY` s after the first data load), runs again at the decision's `wake_at` (before any insight stops being true, or when a reminder is due). Its memory survives refreshes (a refresh never opens the pill or resets the reminders); only a location change or turning the setting off starts over. Each opening draws a new wording seed; silent updates keep it, so the phrasing never changes under the reader. It only ever uses one-shot `GLib.timeout_add_seconds` timers, and does nothing while the `show-overview` setting is off.
- **Where it goes** (one place at a time): while the main window can be seen (`is_on_screen`: visible and not suspended), the pill opens; while it is minimized or hidden by compact mode, the app (`app.py`) sends it as a notification (`OverviewNotifications` in `ui/notifications.py`) when `should_notify` says so: news of medium or above, reminders of extreme ones. Each topic has its own ID (`overview-<topic>`), and a notification is withdrawn when its topic is no longer true, the location changes, notifications are turned off, or the main window comes into view. The engine runs while either `show-overview` or `show-notifications` is on; with both off it does nothing. There is no other notification: don't add one per refresh.
- **Section** (`ui/sections/current.py`): subscribes to `overview-changed` and `changed::show-overview` on `map`, disconnects on `unmap`. It shows the engine's heading (coloured by level), the insight's icon and message, and stays open for `insight.show_seconds`.
- **Numbers** (thresholds, priorities, open times, republish intervals) live in `config.py` under "Overview", in metric; rules convert imperial data before comparing.
- Test rules on made-up forecasts: they are plain Python, so build an `OverviewContext` by hand (`Clock`, `Units`, `HourlySeries`, …) and call `RuleBook.default().run(ctx)`. The tests in [tests/test_overview_rules.py](tests/test_overview_rules.py) do this; add a case there when you add or change a rule.

---

## Design Principles

How to structure new code so it stays reusable and testable. Some existing code doesn't follow these yet; don't rewrite it as a side effect of another task. Bring it in line in a separate `refactor` commit, one area at a time.

### The rules the layers depend on

1. **One source of truth.** `weather_store` holds the selected city's data and its loading status. The UI reads it and asks it to refresh; nothing else keeps fetched data.
2. **Threads stay inside the store.** It fetches on a worker thread and hands the result to the main loop before it sets a property or emits. UI code never sees a thread.
3. **Services are pure functions.** Inputs as arguments (`lat`, `lon`, `unit`), JSON or `None` out, with a timeout and `@cached`.
4. **Widgets are given data**, and windows and dialogs move their layout into `Gtk.Template` `.ui` files (`ui/templates/`) over time.

### Choosing the right tool

| What it is | Use |
| --- | --- |
| A calculation or decision (units, levels, drop count) | a plain function |
| Data with no behaviour (a forecast, a location) | `@dataclass` (`frozen=True` for new models) |
| State plus behaviour (cache, planner) | a class |
| State the UI must react to | a `GObject.Object` with properties and signals |
| Something on screen | a GTK widget subclass, or a class that owns one |
| A seam tests need to swap (an HTTP client) | a `typing.Protocol`, not an ABC |

A class with one method and no state is a function. Avoid catch-all "Manager", "Helper" or "Utils" classes for unrelated things.

### SOLID, the small version

- **Single responsibility:** a module changes for one reason. The API module changes when Open-Meteo does, the levels module when thresholds do, a widget when the look does.
- **Open/closed:** add behaviour by adding a piece (a rule in `RuleBook.default()`, a `visual` passed to a card), not by growing an `if/elif` on a type.
- **Liskov:** a subclass works wherever its base is expected. Every `Rule` returns an `Insight` or `None`.
- **Interface segregation:** ask for the smallest thing you need. A card takes the air-quality model, not the whole store.
- **Dependency inversion:** pass dependencies in (`WeatherStore(client=…)`), so tests can pass fakes. No containers or frameworks.

### Refactoring

- **Fix behaviour in place first, then extract logic, then move files.** Never mix them in one commit.
- A file move is mechanical: `git mv` plus import updates, with no code changes in the same commit, so review stays small and `git blame` keeps working.
- A move updates everything that lists paths: the `meson.build` of each folder involved, `mousam.in`, `po/POTFILES`, `mousam.gresource.xml` (a moved `.ui` keeps its resource path with an `alias`), the tests' imports and this file. Then check that the Flatpak and Snap builds still start: lint and tests don't see resource paths.
- A temporary alias that keeps old imports working (`old_name = new_name`) is fine for one step. Remove it once the callers are updated.
- No UI or behaviour change inside a refactor commit. A bug you find along the way gets its own `fix` commit.
- Still to do, each as its own refactor: move `AutoRefreshTimer` to `state/`; move window and dialog layouts into `ui/templates/`.

### Composition over inheritance

- Build behaviour from small parts rather than subclass trees. The model is the overview: `FirstHourRule` is a `HourTest` (which hour?) plus a `Phrasing` (how to say it), not one subclass per rule. Subclass only to fill in a real extension point (`Rule.evaluate`), and keep hierarchies shallow: one level, two at most (`Below(AtLeast)`).
- No mixins, and no abstract base class "in case we need it": add one when a second implementation exists.
- Share code with a plain function or a small helper class, not a common base class for unrelated widgets.

### Components

- **Sections and cards that have state, timers or signal handlers** subclass a GTK widget (`Gtk.Box`, `Gtk.Grid`), as `CurrentCondition` and `Forecast` (`ui/sections/`) do. Their lifetime is then the widget's: connect on `map`, disconnect and remove sources on `unmap`.
- **Drawing pieces** use composition: the class owns its `Gtk.DrawingArea`, sets the draw function with `safe_set_draw_func`, builds everything in `__init__`, and hands it out as `.widget` (`PollutionBar` is the one that subclasses `Gtk.DrawingArea` instead).
- A component is ready to use when its constructor returns: no separate `create_card()` step.

### Pass data in

- A component gets its data through its constructor (`CardAirPollution(air)`, `Forecast(daily, hourly)`), from the window that builds the grid. It doesn't import `weather_store` or read `settings` deep inside itself to find it. This makes components reusable (main and compact window), buildable with test data, and removes the lazy imports that only exist to dodge import cycles.
- Reading `settings` for display preferences (units, clock, icon theme) at build time is fine; reacting to a change is the owner's job (rebuild, or a `changed::` handler on `map`).
- The shared instances (`settings`, `weather_store`, `overview_engine`, `log_manager`) stay. The problem is reaching for them from everywhere, not that they exist.

### Separate logic from widgets

- Anything that is a decision rather than a widget goes in a plain function in `core/`: classifying a level, how many drops a rain chance gets, today's high and low, whether a code is snow. Widgets call it; tests test it.
- Level classification belongs in `core/levels.py` (`classify_*`), not in `ui/`; forecast decisions in `core/forecast.py`. A new set of GTK-free helpers can get its own module in `core/`.
- The API modules in `services/` stay pure: take every input as an argument (coordinates, unit), return JSON. They don't read `settings`. Expose module functions or public methods; never call a `_private` method from another module.
- Don't mix layers in one helper module: GTK helpers (toasts, widgets) go in `ui/gtk_utils.py`, not next to network or time-zone helpers.

### Signals and threads

- A signal is emitted on the main loop. Code running on a worker thread hands its result over with `GLib.idle_add` and emits from there, so subscribers never need to know about threads (as `WeatherStore._finish` does).
- One emit per real change. If a value is built in several steps, emit once at the end, not per step.

### Reuse, don't copy

- When the same block appears a second time, extract it into a helper; a third copy is a bug waiting to happen. For example, "which hour is now" is one function (`nearest_hour_index` in `core/forecast.py`), not a loop in each module.
- A helper that connects to a signal on someone's behalf does the hard parts once: it doesn't capture widgets, it disconnects itself, and it does nothing if the widget is gone.

### Keep it small

- No dependency-injection frameworks, event buses, plugin systems or MVVM frameworks. The store is the only "view model"; plain classes, functions and GObject properties and signals are enough.
- Prefer a 20-line function anyone can read over a generic abstraction that saves 10 lines.

---

## UI Implementation Rules (VERY IMPORTANT)

For any UI-related task:

- The goal is to **replicate the provided design exactly**
- Match the UI **pixel-perfectly**

When the user provides a design image or screenshot, you MUST:

- match layout exactly
- match spacing and margins
- match font sizes and hierarchy
- match colors and opacity
- match border radius
- match alignment and positioning
- match proportions of elements
- replicate all visible UI elements

Do not approximate. Do not simplify unless explicitly asked.

### Mousam design rules

- Follow libadwaita and the GNOME HIG first. Use stock widgets and style classes (`card`, `view`, `pill`, `suggested-action`, `flat`, `linked`, `dim-label`, …) before custom CSS.
- Content sits in `card` boxes inside an `Adw.Clamp` (max 1400px). Cards keep the spacing the grid uses today (3–12px margins, 6px between rows inside a card).
- Text hierarchy comes from the utility classes in `style.css`: titles `text-lg opacity-80 font-medium`, values `text-3xl font-medium`, units `text-sm opacity-80`, levels `text-base opacity-90 font-semibold` (see the `CSS_TEXT_*` lists in `ui/cards/metric.py`).
- Pair every number with its unit, and every level colour with words ("Moderate", "High"). Levels come from the `classify_*` functions in `core/levels.py`; AQI colours from `THRESHOLDS` in `config.py`.
- Icons: symbolic icons from the icon theme for buttons (`view-refresh-symbolic`, …); weather icons only through `ui/icons.py`. Both icon themes must look right; Material icons are drawn smaller (`get_icon_pixel_size`).
- One `suggested-action` button per page, for the main action (Add Location, Retry).
- Every screen must work in light and dark, with dynamic backgrounds on and off, in metric and imperial, and in both 12h and 24h.
- With dynamic backgrounds on, cards add `bg-dark-overlay` so text stays readable on any weather gradient.
- Window sizes from about 360px wide to full screen must not clip or overflow. Long translated strings must wrap or ellipsize.

### Loading states

- The main window has one view state at a time in `main_stack`: `loader`, `welcome` (no locations), `error_no_internet`, `error_api`, `content`. Switch with `_update_view_state(state, message)`; don't add separate spinners on top.
- The window shows the loader, calls `weather_store.refresh()`, and switches on `notify::status`: `ready` rebuilds `content`, `offline` shows `error_no_internet`, `error` shows `error_api` with `weather_store.error`. There are no fetch callbacks.
- Sections get their data when they are built, so they never wait for it. `HourlyDetails` and `Forecast` build a tab's page the first time it is chosen. If a page ever gets heavy enough to slow the first paint, show a spinner in it and fill it with `GLib.idle_add`.
- Errors the user can fix say how ("Please check your connection.") and offer Retry.

---

## Styling Rules

All custom styling lives in [src/css/style.css](src/css/style.css), loaded once in `WeatherApplication.do_activate`. Apply it with `add_css_class` / `set_css_classes`.

- Reuse the utility classes already there: typography (`text-xs` … `text-8xl`, `font-light` … `font-bold`), spacing (`m-*`, `mt-*`, `mb-*`, `my-*`, …), opacity, borders, `btn-sm` / `btn-md` / `btn-lg`, `bg-weather-*` backgrounds, `compact-*` for the compact window.
- Sizes use `rem` so they follow the user's text scaling. Keep it that way.
- Use libadwaita's named colours (`@accent_color`, `@window_fg_color`, `@card_bg_color`, …) or `currentColor` and opacity instead of hardcoded hex, so light, dark and high contrast work. The weather gradients are the exception.
- If a pattern repeats and no class exists, add one to `style.css` rather than repeating widget calls.
- Margins and sizes can also be set from code (`set_margin_*`, `set_size_request`); match the surrounding component.

### When to use code instead of CSS

| Scenario | Why | Use instead |
| --- | --- | --- |
| Graphs, gauges, arcs, rotated icons | CSS can't draw them | Cairo in a `Gtk.DrawingArea` via `safe_set_draw_func` (`ui/drawing/`) |
| Size of a drawing area | It decides the drawing's layout | `set_size_request` |
| Layout (expand, align, grid spans) | Not CSS properties in GTK | `set_hexpand`, `set_halign`, `Gtk.Grid.attach` |
| A value known only at runtime (e.g. a level's position) | Changes per fetch | Pass it into the drawing class |
| A colour for a level | Picked from data | A CSS class chosen in code (`success`, `warning`, `error`) |
| Icon size | Depends on the icon theme | `get_icon_pixel_size` / `set_pixel_size` |

Cairo colours are `[r, g, b]` floats from 0 to 1. Prefer the existing blue `[0.38, 0.7, 1]` and the level colours already used, so drawings match the CSS.

---

## UI Quality Bar

The app should feel:

- native to GNOME
- calm and glanceable (the answer to "what's the weather?" in one look)
- polished
- fast to open and refresh

Use:

- libadwaita widgets and patterns
- cards with clear hierarchy, not heavy borders
- toasts for short confirmations
- `Adw.StatusPage` for empty and error states
- keyboard shortcuts for main actions (listed in `ui/templates/shortcuts.ui`)
- simple crossfade transitions when useful

---

## State Management Rules

- **Saved values** live in GSettings. Add a key to [data/io.github.amit9838.mousam.gschema.xml](data/io.github.amit9838.mousam.gschema.xml), a property to `Settings` in `services/settings.py`, and (if the user can change it) a row in `ui/dialogs/preferences.py`. Never rename or retype an existing key: users' saved values would be lost.
- **Fetched data** lives only in `weather_store`. Its fields change only in `_start_loading` and `_finish`, on the main loop; nothing else writes them.
- **Temporary UI state** (selected tab, page, dialog contents) stays on the widget.
- React to changes with signals: `settings.connect("changed::<key>", ...)`, `weather_store.connect("notify::status", ...)` (or `notify::is-ready`). Don't poll.
- Locations are stored in `added-cities` as JSON strings; the selected one in `selected-city` as `"lat,lon"`. Use `JsonProcessor`, `LocationData` and `get_cords()`, not your own parsing.

---

## Threading and Performance Rules

- **Never touch GTK from a worker thread.** Network calls run on threads (`weather_store.refresh()`, the city search); hand results back to the main loop with `GLib.idle_add`.
- **`weather_store` changes on the main loop, once per change.** Its worker downloads and builds the models, then hands them over with `GLib.idle_add`: `status` goes `loading` (data cleared, `is-ready` false) and then `ready` (`is-ready` true, one `data-updated`), `offline` or `error`. Handlers may build widgets directly (see `_on_store_status` in `ui/window.py`). A new field is built in the worker (`_download`) and set in `_finish`.
- **One fetch at a time.** `weather_store.refresh()` joins a running fetch for the same city instead of starting another (for another city, it fetches that one when the running fetch ends and drops the old result); go through it, don't start threads of your own for weather data. The Locations window's list uses `weather_store.refresh_saved_locations(coords, on_done)`; use that, not a new thread. The internet check is part of `refresh()` (on its worker), so callers never block on it.
- **Don't wait on the main thread.** No `threading.Event`/`join` or blocking network call there: it freezes the UI. If you need a lock for data shared with a thread, hold it only while assigning or reading, never while calling the network, emitting or calling `GLib`.
- **Every request has a timeout** (`TIMEOUT` from `config.py`), and every API function logs and returns `None` on failure instead of raising.
- **API calls are cached** with `@cached` (TTL `DATA_CACHE_TTL`). A new API call uses it too.
- **No leaks across refreshes.** The content grid is rebuilt on every refresh, so widgets must not be kept alive by their own handlers. Connect handlers on rebuilt widgets with `weak_connect`, set draw functions with `safe_set_draw_func`, remove `GLib.timeout_add` sources when the widget goes, and disconnect `settings` handlers you connect from short-lived widgets. Check with `test_memory_leak.py` after touching refresh or widget lifetime.
- **Never poll the main loop.** Don't write a `GLib.idle_add` / `GLib.timeout_add` callback that returns `SOURCE_CONTINUE` while it waits for UI state (a width, a mapped widget, data). Widgets are often built hidden (the content grid is built behind the `loader` page) and may be thrown away before they are ever shown, so such a callback can spin at 100% CPU forever and keep the old widget tree alive. Wait for the signal that reports the change instead: `Gtk.Adjustment` `changed` for a scrolled size, `map` / `realize` for being shown, `notify::<property>` for data. Disconnect a one-shot handler once it has run. The only repeating timers are real clocks and intervals (the compact clock, `AutoRefreshTimer`), and they must be removed when their widget goes.
- **Handlers must not keep widgets alive.** A closure connected to a signal keeps everything it captures. Capture plain values (an index, a string) rather than `self` or other widgets, or use `weak_connect`. Never pass widgets as extra arguments to `GLib.idle_add` / `timeout_add` for a source that can outlive them. An object passed to `safe_set_draw_func` is kept alive by its drawing area, so it must not also keep the area's parent container (no `self.box = Gtk.Box(); self.box.append(self.area)`): hand out the drawing area itself.
- **Keep draw functions light.** They run on every frame: compute in `__init__`, only draw in `draw`.
- **Long lists**: today's lists are short (hours of two days, 7 days). If you add one that can grow, use `Gtk.ListView` rather than appending hundreds of widgets.

---

## Python Rules

- Follow the style of the file you are in (PEP 8, 4 spaces).
- Target **Python 3.12** (`target-version` in `ruff.toml`): no syntax or stdlib API newer than that, even if your machine or the GNOME runtime has a newer Python.
- Imports inside `src/` are relative (`from ..services.settings import settings` in `ui/window.py`): the sources are installed and imported as the `mousam` package. Never `import settings` or add `sys.path` hacks.
- Singletons are module instances: import `settings`, `weather_store`, `overview_engine`, `log_manager`; never construct `Settings()` or a `WeatherStore()` yourself (tests do, with fakes).
- Add type hints to new functions; keep them simple. In a file that already uses `typing.List` / `Optional`, keep using them; in new files prefer `list[str]` and `str | None`.
- Data from the API goes into the `core/models.py` classes and is read as attributes (`cw.temperature_2m.data`, `.unit`, `.level_str`), not as raw dicts.
- No bare `except:` in new code; catch the specific exception and log it (`requests.RequestException` in `API_*`, `(KeyError, TypeError, ValueError)` when parsing JSON). A broad `except Exception` is only for boundaries that must not crash the app (a worker thread's top level, `RuleBook.run`); log it there.
- No mutable default arguments (`def f(items=None)`, then `items = items or []`), and no module-level state other than the singletons above and constants.
- Times are unix timestamps from the API. Turn them into local times with `datetime.fromtimestamp(ts, ZoneInfo(tz))` using the city's time zone, never naive `datetime.now()` / `fromtimestamp(ts)`.
- Each module gets `_` with `from gettext import gettext as _` (and `pgettext as C_`, `ngettext`); don't rely on the builtin `_` that `gettext.install` adds in the launcher.
- Use `get_logger("<area>")` from `core/log.py`, never `print`. Logging is silent unless debug mode is on. Importing `core/log.py` needs no GTK and it never reads `settings`: `app.main()` calls `log_manager.setup(debug)` once at start-up, and Preferences calls `update_level(debug)`.
- Keep `gi.require_version(...)` before importing from `gi.repository`, as the files already do.
- New logic that doesn't need GTK (classification, conversions, parsing) should be a plain function or `@staticmethod` so it stays easy to test.

---

## Code Style

The codebase has no formatter. Its conventions are below; when a file differs, follow the file.

**Naming**

- Modules: lowercase `snake_case` in the folder of their layer (`ui/cards/metric.py`, `services/open_meteo.py`, `core/levels.py`); the folder says the layer, so the name doesn't repeat it.
- Classes are `PascalCase`; functions, methods and variables are `snake_case`; constants are `UPPER_SNAKE` (in `config.py`, or at the top of a module for local ones such as `CSS_TEXT_TITLE`).
- Anything not used outside its class or module starts with `_` (`_render_weather_grid`, `_finish`).
- Signal handlers are `_on_<source>_<what>` (`_on_store_status`, `_on_enabled_changed`). Idle and timeout callbacks get a name that says what they do (`_start_loading`), not `_callback`.
- Names say what they hold, with the unit when it matters: `delay_seconds`, `week_min`, `sunrise_ts`, not `d`, `tmp`, `data2`.

**Layout**

- Double quotes for strings.
- Lines up to about 100 characters (ruff doesn't check length). Wrap long calls inside the brackets, one argument per line if they don't fit; no backslash continuations.
- Two blank lines between top-level definitions, one between methods.
- Long classes are split with section comments: `# ---------- Data ----------`.
- Imports: standard library, then `gi` with `gi.require_version(...)`, then `gi.repository`, then local relative imports. Import names (`from ..icons import bg_css`), not `*`.

**Functions**

- Keep functions short and flat: return early instead of nesting `if`s, and split out a helper once a function does two separate things (build vs. fill, fetch vs. parse).
- Pass values in, don't reach for globals: a drawing class takes its numbers in `__init__`, it doesn't read `weather_store`.
- GLib callbacks return `GLib.SOURCE_REMOVE` / `GLib.SOURCE_CONTINUE` explicitly, never `True` / `False` / `None`.
- Build widgets with constructor keyword arguments when there are only a few (`Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)`), then setters for the rest, as the surrounding code does.

**Strings**

- f-strings for strings that aren't translated (logs, CSS class names, debug output).
- Translated strings with values use named placeholders and `.format()`: `_("Material icons: {name}").format(name=…)`. Never `_(f"…")`: gettext can't extract it, and translators need the placeholder names.
- Log messages say what happened and the value that matters: `logger.error(f"Air quality fetch failed: {e}")`. Log only coordinates and city names, nothing else about the user.

**Comments and docstrings**

- Public classes and functions get a docstring: a one-line summary, then a short paragraph if the behaviour isn't obvious (see `DrawTempRange`, `DrawTickGauge`).
- Comments explain *why* (a thread, a GTK quirk, a leak being avoided), not what the next line does.
- Comments are plain English, in full sentences, and readable by a newcomer.
- Don't leave commented-out code, `print` calls or notes like "moved to …". Git keeps the history.

**Diffs**

- Change only what the task needs. Don't reformat, rename or reorder code you aren't otherwise touching: it hides the real change in review and breaks other contributors' branches.
- Fix typos in names only in a separate refactor commit, and update every caller.

---

## Data Rules

- Open-Meteo is the only data source: forecast (`OPEN_METEO_BASE_URL`), air quality (`AIR_QUALITY_BASE_URL`) and geocoding (`GEOCODING_BASE_URL`), all in `config.py`. It needs no API key; never add one to the app.
- Request `timeformat=unixtime`, and handle time zones through `get_time_difference` / the selected city's `timezone`. Never assume the city is in the system time zone.
- Units: imperial is requested from the API where it supports it (`temperature_unit`, `wind_speed_unit`); pressure (hPa → inHg, `HPA_TO_INHG`) and visibility (m → km / miles) are converted by us. Keep conversions in the API layer, `core/units.py` or the store's model building, not in widgets.
- A new field means: add it to the request list in the API module (`services/open_meteo.py`, `services/air_quality.py`), to the model's annotations in `core/models.py`, and (if it gets a level) a `classify_*` function in `core/levels.py`.
- Don't send anything about the user to any service except the coordinates and city name needed for the request.

---

## Translation Rules

- Wrap every user-visible string in `_()`. When a word is ambiguous out of context ("Low", "Moderate"), use `C_("context", "...")`, as the level classifiers do.
- Counts use plural forms: `ngettext("{n} minute", "{n} minutes", n)` (extracted by `./update-pot` and the Meson `glib` preset).
- Add a `# Translators:` comment right above a string with placeholders, saying what each one holds.
- Never translate **Mousam**.
- Don't build sentences by joining translated pieces; translate the whole sentence with placeholders.
- After adding or changing strings, run `./update-pot`. Don't edit `po/*.po` files by hand or machine-translate them: translators maintain them (including through Weblate).
- A new language goes in `po/LINGUAS` along with its `.po` file.

---

## Feature Implementation Rules

When the user asks to build a feature:

1. Read this file first.
2. Identify files to change (including `meson.build`, `POTFILES`, the gschema and appdata when needed).
3. Keep changes focused.
4. Do not rewrite unrelated code.
5. Follow existing patterns.
6. Ensure the feature works end to end in the installed app.
7. Fix errors before finishing.

---

## Packaging & Release Rules

- The Flatpak manifest is [io.github.amit9838.mousam.json](io.github.amit9838.mousam.json); keep its sandbox permissions (`finish-args`) as small as they are. A new permission needs a strong reason and user approval.
- Snap (`snap/snapcraft.yaml`, built from the checkout) is maintained too; a change to dependencies or installed files must be reflected there.
- The version lives in two places: `meson.build` (Meson fills it into `VERSION` in `src/config.py`) and a new `<release>` in `data/io.github.amit9838.mousam.appdata.xml.in` (with release notes, shown on the About dialog's What's New page). Change them together, and only when asked to prepare a release.
- User-visible changes to the app's look should come with updated `docs/screenshots/` when the user asks for it; the appdata, README and website point at them.

---

## Testing

- Unit tests live in `tests/`, one file per area (`test_levels.py`, `test_forecast.py`, `test_locations.py`, `test_api.py`, `test_weather_store.py`, `test_overview_rules.py`, `test_notifications.py`), use `unittest` (no pytest dependency) and are registered in [tests/meson.build](tests/meson.build), so `meson test` and CI run them.
- They import from the source tree as the `mousam` package (see the shim at the top of `tests/test_overview_rules.py`), so they need no install, no display and no network. Only test GTK-free modules this way, plus the store (`tests/test_weather_store.py`, PyGObject's GLib and GObject) and the notifications (`tests/test_notifications.py`, Gio, with a fake app), which need no display; CI installs `python3-gi` for them. `tests/fakes.py` holds the fakes: `FakeRequests` stands in for `requests` in the API tests (`tests/test_api.py`), `FakeForecastClient` for the forecast API, and `FakeSettings` for the GSettings wrapper, which needs the installed schema.
- When you add GTK-free logic (a rule, a classifier, a conversion, a parser), add a test for it. A new test file must be added to `tests/meson.build`.
- Tests use fixed clocks and hand-built data, never the real time or Open-Meteo.

---

## Linting and Validation

Run before declaring any task done:

```bash
ruff check src tests
python3 -m compileall -q src
for t in tests/test_*.py; do python3 "$t"; done
```

`src/` is free of ruff findings, and the Checks workflow (`.github/workflows/checks.yml`) keeps it that way, along with `compileall` and `meson test` (which validates the gschema, appdata and desktop file). Fix a finding rather than silencing it; change `ruff.toml` only for a rule that doesn't fit the whole codebase. If you touched the gschema, appdata or desktop file, run their validators too (see "Commands").

Then build, install and run the app, and check the change in light and dark, metric and imperial.

If you touched refresh, rendering, signals or main-loop sources, also check CPU and memory across several refreshes, including quick back-to-back ones (Ctrl+R several times, or switching location): `top -p <pid>` must settle near 0% CPU once loading ends, and RSS must not keep climbing. In the Flatpak, the app process is `python3 /app/bin/mousam`, not the `bwrap` wrappers.

---

## Communication Style

Be concise. Explain what changed and how to test it.

---

## Final Reminder

Before every feature implementation:

- Read this file
- Follow it strictly
- Build clean, simple, readable code
- Replicate UI exactly when designs are provided

## git

- Never commit until asked
- Do commits phasewise
- Do not co-author Claude
- Commit messages follow Conventional Commits: `type(scope): subject` (`feat`, `fix`, `refactor`, `chore`, `style`; e.g. `fix(render): …`, `chore(po): …`)
- Always name plan documents with the `-plan.md` suffix (e.g. `docs/abc-plan.md`), so `.gitignore` catches them
- Never commit plan documents. They stay local and are gitignored (`*-plan.md`)
- `.gitignore` ignores `test*` everywhere except `tests/`: files under `tests/` are tracked, but a `test*` file anywhere else (like `src/test_memory_leak.py`) is not
