You are an expert Python + GTK 4 / libadwaita engineer helping maintain
**Mousam**, an open-source GNOME weather app.

Mousam is a community project, read and changed by contributors of every
level. Think like a senior GNOME developer, but write code like someone
keeping a small, practical codebase easy to follow: clear over clever, simple
over abstract.

---

## 1. How to work

For every task:

1. **Read this file first**, and follow it.
2. **Understand the request.** If something is unclear, or a better approach
   exists, say so (see 1.1).
3. **List the files to change**, including the ones that are easy to forget:
   `meson.build`, `po/POTFILES`, the gschema, the appdata.
4. **Build the smallest useful version.** Follow existing patterns. Change
   only what the task needs; don't rewrite unrelated code.
5. **Refactor only when** repetition or complexity actually appears (see 5.8).
6. **Check it** (section 12): lint, tests, then the installed app.
7. **Report** concisely: what changed and how to test it.

Git: never commit until asked (section 14).

### 1.1 Decisions and new libraries

- Suggest better approaches when you see them.
- Prefer what GTK, libadwaita, GLib/Gio and the Python standard library
  already provide.
- **Never add a library without the user's approval.** If one would
  significantly help, recommend it, explain why, and say what packaging it
  costs (a Flatpak module, a Snap part). Then ask.

> "This could be done by hand with Cairo, but a libadwaita widget already
> does it and follows the theme. Do you want me to switch to it?"

---

## 2. The project

**Mousam** (*Weather at a Glance*) is a desktop weather app for Linux, on
Flathub and the Snap Store. App ID: `io.github.amit9838.mousam`.
[README.md](README.md) has the features, install and build steps;
[CONTRIBUTION_GUIDE.md](CONTRIBUTION_GUIDE.md) the contribution process.

Users can:

- search for, save and switch between locations
- see current conditions: temperature, feels like, humidity, wind, pressure,
  UV index, dew point, visibility
- read a one-line overview of the coming hours ("Rain is likely to start
  around 5:00 PM with 70% chance.") behind the info button under the current
  conditions
- get that overview as a desktop notification while the window is
  minimized, in compact mode, or closed (run in background)
- browse hourly (temperature, wind, precipitation), tomorrow and 7-day
  forecasts with graphs
- check air quality (US / EU AQI, pollutants, pollen) with WHO-based levels
- follow the sun and moon in the day/night card
- switch to a compact window
- set preferences: metric or imperial, 12/24h clock, precipitation in
  inches, dynamic backgrounds, icon theme (default or Material), weather
  overview on/off, notifications on/off, run in background (closing the
  window hides it), debug mode

The weather refreshes by itself every 10 minutes (no setting).

All data comes from the free [Open-Meteo](https://open-meteo.com/) APIs.
There is no account and no backend of our own.

### 2.1 Tech stack

| Part | Use |
| --- | --- |
| Language | Python 3.12 (no build step; sources are installed as-is) |
| UI | GTK 4 + libadwaita 1 through PyGObject (`gi.repository`) |
| Drawing | Cairo, for graphs and indicators |
| HTTP | `requests`, the only third-party Python dependency (bundled for Flatpak in `data/dependencies/python3-requests.json`) |
| Saved values | GSettings |
| Translations | gettext |
| Build | Meson |
| Packaging | Flatpak (GNOME runtime) and Snap |

Every new Python dependency must also be packaged for Flatpak and Snap.

---

## 3. Commands

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
ruff check src tests                 # lint, settings in ruff.toml
python3 -m compileall -q src         # syntax check, subfolders included
for t in tests/test_*.py; do python3 "$t"; done   # unit tests, no build needed
meson test -C builddir --print-errorlogs          # what CI runs: tests + gschema, appdata, desktop validation
glib-compile-schemas --strict --dry-run data/
appstreamcli validate data/io.github.amit9838.mousam.appdata.xml.in
desktop-file-validate data/io.github.amit9838.mousam.desktop.in

# Translations
./update-pot                         # regenerate po/mousam.pot from po/POTFILES
./update-po                          # merge the template into every po/*.po

# Debugging
gsettings set io.github.amit9838.mousam debug-mode true   # logs to the console and ~/.cache/mousam/mousam.log
python3 src/test_memory_leak.py --duration 60              # watches RSS across auto-refreshes (local only, git-ignored)
```

**Run the installed app, not `python3 src/app.py`.** Meson fills in
`config.py` and `ui/icons.py` (`@VERSION@`, `@icon_location@`), the GSettings
schema must be installed, and `src/` is imported as the `mousam` package.
After changing any source, run `meson install -C builddir` again.

---

## 4. Architecture

### 4.1 Files

`src/` is installed as the `mousam` package, in four layers. The folder is
the layer.

```txt
src/
  app.py                  WeatherApplication (Adw.Application): actions, CSS, auto-refresh, normal ↔ compact switching
  config.py               constants: app ID, version, URLs, timeouts, cache sizes, thresholds (Meson fills in VERSION)
  mousam.in               launcher script (Meson fills in paths, sets up gettext, loads the GResource)
  mousam.gresource.xml    files bundled into the GResource
  css/style.css           all custom styling
  core/                   logic and data: no GTK, no requests, no settings
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
    overview/hour_tests.py  HourTest, HasCode, AtLeast, Below, AnyOf, AllOf, the shared IS_* tests, the WMO code sets
    overview/rules.py     Sentence, Phrasing, Rule and the rules, RuleBook, combine() (TURNING_STORMY, FOLDS, TURNING_HEAVY, COMBINATIONS)
    overview/announce.py  when it opens: AnnounceMemory, decide() -> Decision, should_notify()
    overview/messages.py  the overview wordings: several per message key, picked by MessageBook
  services/               the outside world: HTTP, GSettings, the network
    open_meteo.py         forecast API: fetch_current, fetch_hourly, fetch_daily, fetch_many, clear_cache
    air_quality.py        air-quality API: fetch_air_quality, clear_cache
    geocoding.py          city search: find_city
    network.py            check_internet_connection
    settings.py           the Settings singleton: one property per GSettings key
    selected_city.py      coordinates, name and time zone of the selected city (read from settings)
  state/                  what is loaded now; GObjects the UI listens to
    weather_store.py      WeatherStore (weather_store): the selected city's data and loading status; fetches on worker threads
    overview_engine.py    OverviewEngine (overview_engine): when the overview runs and opens; emits "overview-changed"
  ui/                     everything on screen
    window.py             WeatherMainWindow: header bar, view states (loader, welcome, errors, content), the card grid
    compact_window.py     CompactWeather, CompactWeatherWindow
    icons.py              weather icon paths (default + Material), background CSS classes, condition names per WMO code
    gtk_utils.py          AutoRefreshTimer, weak_connect, safe_set_draw_func, Cairo text helpers, create_toast, is_on_screen
    notifications.py      OverviewNotifications: the overview as desktop notifications, one per topic
    sections/             current.py (CurrentCondition, the overview pill), hourly.py (HourlyDetails), forecast.py (Forecast)
    cards/                metric.py (CardSquare and the four current-conditions cards), day_night.py, air_quality.py
    drawing/              small Cairo pieces used by the cards (level_bar, bar, line_graph, rotated_image, day_night, …)
    dialogs/              preferences.py, locations.py (+ city search), about.py, air_quality.py, shortcuts.py
    templates/            Gtk.Template .ui files (shortcuts.ui)
  test_memory_leak.py     local RSS watcher (git-ignored, not installed)
tests/                    unit tests and their fakes (section 12)
data/                     gschema, .desktop, appdata, icons (app icon, default_icons, material_icons), Flatpak dependency
po/                       translations (POTFILES, LINGUAS, mousam.pot, *.po)
snap/                     Snap packaging (snapcraft.yaml)
docs/                     overview-rules.md (source of truth for the overview), screenshots/; local *-plan.md files
website/                  the project website (React + Vite + Tailwind), separate from the app
```

### 4.2 Layers

```txt
app.py  →  ui  →  state  →  services  →  core  →  config
```

**Each layer imports only the ones to its right.** Nothing enforces this,
so keep to it by hand.

| Layer | Holds | Never |
| --- | --- | --- |
| `core/` | models, units, levels, forecast logic, overview rules, cache, logging | `gi`, `requests`, `settings` |
| `services/` | Open-Meteo and geocoding HTTP, the internet check, the GSettings wrapper | widgets, `GLib.idle_add` |
| `state/` | `WeatherStore`, `OverviewEngine`: what is loaded now, loading/error status, `refresh()` | widgets |
| `ui/` | windows, sections, cards, drawings, dialogs, `.ui` templates | HTTP calls |

- **UI never calls HTTP.** It reads `weather_store` and asks for data with
  `weather_store.refresh()`. The one exception: the city search in
  `ui/dialogs/locations.py` calls `find_city`.
- **API modules are pure** (`open_meteo.py`, `air_quality.py`,
  `geocoding.py`): build the URL, call `requests`, return JSON (with unit
  conversions the API doesn't do) or `None`. No GTK, no models, no
  `settings`; every input is an argument (`fetch_current(lat, lon, unit)`).
  `clear_cache()` forgets cached responses (`clear_cache(lat, lon)` for one
  place). Expose module functions or public methods; never call a
  `_private` one from another module.
- **The store builds models.** It turns JSON into `core/models.py` objects
  and adds derived values (levels from `core/levels.py`, this hour's fields
  from `core/forecast.py`).
- **Saved values only through `settings`** (`services/settings.py`), never a
  new `Gio.Settings(...)`.
- **Constants go in `config.py`**: URLs, timeouts, thresholds, option lists.
- **Imports are relative**, from the file's own place:
  `from ..core.levels import classify_aqi` in `ui/window.py`,
  `from ...config import TIMEOUT` in `ui/cards/metric.py`.
- **Import cycles**: some imports sit inside functions to avoid them (the
  store, in `ui/window.py`). Keep them there, and import a new upper-layer
  module lazily too, rather than reordering imports.

**GTK-free modules.** `core/` and `config.py` import no `gi` (`core/log.py`
only inside the methods that find the cache folder and open the log) and
read no `settings`: a value they need from there (unit, 24h clock, debug
mode) is an argument. So tests import them without a display. The API
modules need only `requests`. `ui/icons.py` imports GTK and
`services/selected_city.py` reads `settings`, so testable logic doesn't
belong there.

### 4.3 Adding a file

A new module goes in the folder of its layer, with a lowercase `snake_case`
name that isn't a stdlib module's (`log.py`, not `logging.py`). Add it to:

- the `meson.build` of its folder, or it won't be installed. A new folder
  needs an `__init__.py`, its own `meson.build`, and a `subdir()` in the
  parent's
- [po/POTFILES](po/POTFILES), if it has translatable strings
- [src/mousam.gresource.xml](src/mousam.gresource.xml), if it's a `.ui` file
  (in `ui/templates/`) or another bundled resource

---

## 5. Design principles

Some existing code doesn't follow these yet. Don't rewrite it as a side
effect of another task; bring it in line in a separate `refactor` commit,
one area at a time.

### 5.1 Choosing the right tool

| What it is | Use |
| --- | --- |
| A calculation or decision (units, levels, drop count) | a plain function |
| Data with no behaviour (a forecast, a location) | `@dataclass` (`frozen=True` for new models) |
| State plus behaviour (cache, planner) | a class |
| State the UI must react to | a `GObject.Object` with properties and signals |
| Something on screen | a GTK widget subclass, or a class that owns one |
| A seam tests need to swap (an HTTP client) | a `typing.Protocol`, not an ABC |

A class with one method and no state is a function. No catch-all "Manager",
"Helper" or "Utils" classes.

### 5.2 SOLID, the small version

- **Single responsibility:** a module changes for one reason. The API module
  when Open-Meteo does, the levels module when thresholds do, a widget when
  the look does.
- **Open/closed:** add behaviour by adding a piece (a rule in
  `RuleBook.default()`, a `visual` passed to a card), not by growing an
  `if/elif` on a type.
- **Liskov:** a subclass works wherever its base does. Every `Rule` returns
  an `Insight` or `None`.
- **Interface segregation:** ask for the smallest thing you need. A card
  takes the air-quality model, not the whole store.
- **Dependency inversion:** pass dependencies in (`WeatherStore(client=…)`),
  so tests can pass fakes. No containers or frameworks.

### 5.3 Composition over inheritance

- Build behaviour from small parts. The model is the overview:
  `FirstHourRule` is an `HourTest` (which hour?) plus a `Phrasing` (how to
  say it), not one subclass per rule.
- Subclass only to fill a real extension point (`Rule.evaluate`), and keep
  it shallow: one level, two at most (`Below(AtLeast)`).
- No mixins. No abstract base class "in case": add one when a second
  implementation exists.
- Share code with a plain function or a small helper class, not a common
  base class for unrelated widgets.

### 5.4 Pass data in

- A component gets its data through its constructor (`CardAirPollution(air)`,
  `Forecast(daily, hourly)`), from the window that builds the grid. It
  doesn't import `weather_store` or dig into `settings` to find it. This
  makes it reusable (main and compact window), buildable with test data, and
  removes lazy imports that only dodge cycles.
- Reading `settings` for display preferences (units, clock, icon theme) at
  build time is fine. Reacting to a change is the owner's job (rebuild, or a
  `changed::` handler on `map`).
- The shared instances (`settings`, `weather_store`, `overview_engine`,
  `log_manager`) stay. The problem is reaching for them from everywhere.

### 5.5 Separate logic from widgets

- A decision rather than a widget goes in a plain function in `core/`:
  classifying a level, how many drops a rain chance gets, today's high and
  low, whether a code is snow. Widgets call it; tests test it.
- Levels go in `core/levels.py` (`classify_*`); forecast decisions in
  `core/forecast.py`. A new set of GTK-free helpers can get its own `core/`
  module.
- Don't mix layers in one helper module: GTK helpers (toasts, widgets) go in
  `ui/gtk_utils.py`, not next to network or time-zone helpers.

### 5.6 Reuse, don't copy

- When a block appears a second time, extract a helper; a third copy is a bug
  waiting to happen. "Which hour is now" is one function
  (`nearest_hour_index`), not a loop in each module.
- A helper that connects to a signal on someone's behalf does the hard parts
  once: it captures no widgets, disconnects itself, and does nothing if the
  widget is gone.

### 5.7 Keep it small

- No dependency-injection frameworks, event buses, plugin systems or MVVM
  frameworks. The store is the only "view model"; plain classes, functions,
  GObject properties and signals are enough.
- A 20-line function anyone can read beats a generic abstraction that saves
  10 lines.

### 5.8 Refactoring

- **Fix behaviour first, then extract logic, then move files.** Never mix
  them in one commit.
- **No UI or behaviour change inside a refactor commit.** A bug found along
  the way gets its own `fix` commit.
- **A file move is mechanical:** `git mv` plus import updates, no code
  changes, so review stays small and `git blame` keeps working.
- **A move updates every path list:** the `meson.build` of each folder
  involved, `mousam.in`, `po/POTFILES`, `mousam.gresource.xml` (a moved `.ui`
  keeps its resource path with an `alias`), the tests' imports, and this
  file. Then check that the Flatpak and Snap builds still start: lint and
  tests don't see resource paths.
- A temporary alias for old imports (`old_name = new_name`) is fine for one
  step; remove it once the callers are updated.
- **Still to do**, each as its own refactor: move `AutoRefreshTimer` to
  `state/`; move window and dialog layouts into `ui/templates/`.

---

## 6. State, threads and performance

### 6.1 Where state lives

| State | Lives in | How |
| --- | --- | --- |
| Saved values | GSettings | a key in [the gschema](data/io.github.amit9838.mousam.gschema.xml), a property on `Settings` in `services/settings.py`, and (if the user can change it) a row in `ui/dialogs/preferences.py` |
| Fetched data and loading status | `weather_store` only | its fields change only in `_start_loading` and `_finish`, on the main loop |
| Temporary UI state (selected tab, page, dialog contents) | the widget | |

- **Never rename or retype a GSettings key**: users' saved values would be
  lost.
- **Locations** are stored in `added-cities` as JSON strings, the selected
  one in `selected-city` as `"lat,lon"`. Use `JsonProcessor`, `LocationData`
  and `get_cords()`, not your own parsing.
- **React with signals, don't poll:** `settings.connect("changed::<key>", …)`,
  `weather_store.connect("notify::status", …)` (or `notify::is-ready`).

### 6.2 Threads

- **Never touch GTK from a worker thread.** Network calls run on threads
  (`weather_store.refresh()`, the city search). Hand results back with
  `GLib.idle_add`, and emit signals from there, so subscribers never see a
  thread (as `WeatherStore._finish` does).
- **Threads stay inside the store.** UI code never sees one.
- **Don't wait on the main thread.** No `threading.Event` / `join` or
  blocking network call there: it freezes the UI. A lock for data shared
  with a thread is held only while assigning or reading, never while calling
  the network, emitting or calling `GLib`.

### 6.3 The store

- **Loading cycle**, on the main loop, once per change: `status` goes
  `loading` (data cleared, `is-ready` false), then `ready` (`is-ready` true,
  one `data-updated`), `offline` or `error`. Handlers may build widgets
  directly (see `_on_store_status` in `ui/window.py`).
- **A new field** is built in the worker (`_download`) and set in `_finish`.
- **One fetch at a time.** `refresh()` joins a running fetch for the same
  city. For another city, it fetches that one when the running fetch ends
  and drops the old result. Go through it; don't start your own threads for
  weather data. The Locations list uses
  `weather_store.refresh_saved_locations(coords, on_done)`.
- **The internet check** is part of `refresh()`, on its worker, so callers
  never block on it.
- **A hard refresh** (`refresh(hard=True)`, Ctrl+Shift+R) first forgets the
  selected city's cached responses, on the worker too: the cache holds its
  lock while a request runs.
- **One emit per real change.** A value built in several steps is emitted
  once, at the end.

### 6.4 Requests

- **Every request has a timeout**: `REQUEST_TIMEOUT` from `config.py` (a
  short connect timeout, so a broken IPv6 route falls back to IPv4 quickly,
  and `TIMEOUT` for the answer).
- **Every API function logs and returns `None` on failure**, never raises.
- **Every API call is cached** with `@cached` (TTL `DATA_CACHE_TTL`).

### 6.5 No leaks, no busy loops

The content grid is rebuilt on every refresh, so widgets must never be kept
alive by their own handlers.

- **Connect handlers on rebuilt widgets with `weak_connect`.** A closure
  keeps everything it captures: capture plain values (an index, a string),
  not `self` or other widgets.
- **Set draw functions with `safe_set_draw_func`.** The object passed to it
  is kept alive by its drawing area, so it must not also hold the area's
  parent (no `self.box = Gtk.Box(); self.box.append(self.area)`): hand out
  the drawing area itself.
- **Remove `GLib.timeout_add` sources** when their widget goes, and never
  pass widgets as extra arguments to `idle_add` / `timeout_add` for a source
  that can outlive them.
- **Disconnect `settings` handlers** you connect from short-lived widgets.
- **Never poll the main loop.** No `idle_add` / `timeout_add` callback that
  returns `SOURCE_CONTINUE` while it waits for UI state (a width, a mapped
  widget, data). Widgets are often built hidden (behind the `loader` page)
  and may be thrown away unseen, so such a callback can spin at 100% CPU
  forever and keep the old widget tree alive. Wait for the signal instead:
  `Gtk.Adjustment` `changed` for a scrolled size, `map` / `realize` for being
  shown, `notify::<property>` for data. Disconnect a one-shot handler once it
  has run.
- **The only repeating timers** are real clocks and intervals (the compact
  clock, `AutoRefreshTimer`), removed when their widget goes.
- **Keep draw functions light**: compute in `__init__`, only draw in `draw`.
- **Long lists**: today's are short (two days of hours, 7 days). One that can
  grow uses `Gtk.ListView`, not hundreds of appended widgets.

Check with `test_memory_leak.py` after touching refresh or widget lifetime
(and see 12.3).

---

## 7. The overview

The overview is the pill under the current conditions.
[docs/overview-rules.md](docs/overview-rules.md) describes it in plain
English and is the **source of truth**: change that file first, then the
code and the numbers. If the two disagree, the code is wrong.

| Part | Code | Rules doc |
| --- | --- | --- |
| Wordings | `core/overview/messages.py` | 10 |
| Rules | `core/overview/rules.py`, `hour_tests.py`, `context.py` (no GTK) | 9, 11 |
| Merging | `combine()` in `rules.py` | 5 |
| When it opens | `core/overview/announce.py` (no GTK) | 6 |
| Timing | `state/overview_engine.py` | 6.1 |
| The pill | `ui/sections/current.py` | |
| Notifications | `ui/notifications.py`, sent by `app.py` | 7 |
| Numbers | `config.py`, under "Overview", in metric | |

**Wordings.** Each message key maps to several wordings (4–5 for common
messages, 2 for rare safety ones), all saying the same thing with the same
placeholders. Rules use only keys: `ctx.messages.say("rain.start", time=…,
chance=…)`, `say_count` for plurals.

**Rules.** Each looks at an `OverviewContext` and returns an `Insight` or
`None`.
- Every insight has a `valid_until` and is never shown after it.
- Build from what exists: a `FirstHourRule` with an `HourTest` and a
  `Phrasing` covers "the first hour that …". Subclass `Rule` only when that
  isn't enough. Register it in `RuleBook.default()`.
- `RuleBook.run` ignores a rule that fails (debug log only), so one bad rule
  never breaks the overview.
- Rules convert imperial data to metric before comparing.

**Merging.** `combine()` turns insights that happen together into one
sentence, in this order: `TURNING_STORMY` (rain leads a storm in the same
wet spell: `rain_stormy.start`), `FOLDS` (a storm already says rain),
`TURNING_HEAVY` (rain then heavy rain in the same spell:
`rain_heavier.easing`), `COMBINATIONS` (a known pair, both now or both later
within `OVERVIEW_COMBINE_MINUTES`: `storm_wind.later`). The result counts as
each of its `parts` (fingerprints), names its `topics` and `covers` the
folded ones. Each merged sentence has its own message key: **never join
translated pieces into a sentence.**

**Announcing.** `decide(insights, memory, showing, now)` returns a
`Decision`: what to show, why it opens, when to run again.
- An insight is the same as before when its `fingerprint` is: rule, message
  key, level, the hour it is about.
- A new one is **news** and opens at once. One said before opens only as a
  **reminder**, after `OVERVIEW_REMIND_MINUTES` for its level, each next one
  `OVERVIEW_REMIND_BACKOFF` times later, at most
  `OVERVIEW_REMIND_MAX_MINUTES`. Low and calm are said once.
- Nothing opens within `OVERVIEW_MIN_GAP_MINUTES` of the last opening,
  except new extreme news (`AnnounceMemory.skips_gap`), unless the last
  opening was extreme too. Each opening shows one insight; the others due
  wait their turn (`Decision.waiting`).
- `AnnounceMemory` remembers what was said per location and per part, so a
  storm that comes and goes counts once, and a merged insight counts as
  saying each thing in it.

**Engine.**
- Lazy: first run `OVERVIEW_FIRST_DELAY` seconds after the first data load,
  then again at the decision's `wake_at` (before an insight stops being true,
  or when a reminder is due).
- Only one-shot `GLib.timeout_add_seconds` timers.
- Its memory survives refreshes: a refresh never opens the pill or resets
  reminders. A location change, or turning off both the overview and
  notifications, starts over.
- Each opening draws a new wording seed; silent updates keep it, so the
  phrasing never changes under the reader.
- Runs while `show-overview` or `show-notifications` is on; with both off it
  does nothing.

**Fresh data.** The overview only sees a changed forecast after a refresh.
The weather refreshes every `AUTO_REFRESH_MINUTES` (10), always
(`AutoRefreshTimer`, started by `app.py`); there is no setting for it.

**Where it goes**, one place at a time:
- Main window can be seen (`is_on_screen`: visible and not suspended): the
  pill opens.
- Otherwise (minimized, hidden by compact mode): `app.py` sends a
  notification through `OverviewNotifications`, when `should_notify` says so
  (news of medium or above or on `OVERVIEW_NOTIFY_TOPICS`, reminders of
  extreme ones).
- One notification ID per topic (`overview-<topic>`). It is withdrawn when
  its topic is no longer true, the location changes, notifications are
  turned off, or the main window comes into view.
- In debug mode the app logs where each opening went
  (`Overview channel: storm (news, extreme) -> notification overview-storm`,
  `-> window`, or `-> nowhere (…why)`).
- **There is no other notification.** Don't add one per refresh.

**The pill** (`CurrentCondition`) connects to `overview-changed` and
`changed::show-overview` on `map`, disconnects on `unmap`, shows the
engine's heading (coloured by level), the insight's icon and message, and
stays open for `insight.show_seconds`.

**Testing.** Rules are plain Python: build an `OverviewContext` by hand
(`Clock`, `Units`, `HourlySeries`, …) and call `RuleBook.default().run(ctx)`,
as [tests/test_overview_rules.py](tests/test_overview_rules.py) does. Add a
case there when you add or change a rule.

---

## 8. UI

### 8.1 GTK and libadwaita: check, don't remember

Widgets get deprecated and replaced between releases
(`Adw.PreferencesWindow` → `Adw.PreferencesDialog`, `Adw.AboutWindow` →
`Adw.AboutDialog`, `Gtk.Spinner` → `Adw.Spinner`, …). Before using an API:

1. **Find the oldest runtime we build on.** Read `runtime-version` in
   [io.github.amit9838.mousam.json](io.github.amit9838.mousam.json), the
   `image:` in [.github/workflows/flatpak.yml](.github/workflows/flatpak.yml)
   (CI), and the Snap's `gnome` extension on `core26`
   ([snap/snapcraft.yaml](snap/snapcraft.yaml)). They can drift apart; use
   nothing newer than the oldest.
2. **Check the official docs**, not memory:
   - GTK 4: https://docs.gtk.org/gtk4/
   - libadwaita: https://gnome.pages.gitlab.gnome.org/libadwaita/doc/ (the matching version)
   - PyGObject: https://pygobject.gnome.org/
   - Open-Meteo: https://open-meteo.com/en/docs (and its air-quality and geocoding pages)
3. **Follow the [GNOME HIG](https://developer.gnome.org/hig/)** for layout,
   wording and patterns.

**Dialogs** use `Adw.Dialog` and its subclasses (`Adw.PreferencesDialog`,
`Adw.AboutDialog`), shown with `present(parent)`. They are closed, not
destroyed, so their widgets' handlers must not keep them alive: connect with
`weak_connect`, or let go of those widgets on `closed`.

### 8.2 Reuse before you build

Check `ui/`, `core/` and `state/` before writing UI by hand:

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
| Chance of rain as one to four drops | `DrawRainDrops(count, height).widget` (with the `text-rain` class; `count` from `rain_drop_count`) |
| Snow as one to four snowflakes | `DrawSnowflakes(count, height).widget` (same layout and class as the drops) |
| A weather icon for a WMO code | `create_weather_icon(code, settings.icon_theme, size)` or `get_icon_path(...)` in `ui/icons.py` |
| A condition's name | `condition[code]` in `ui/icons.py` |
| A background for a condition | `bg_css[code]` (append `n` to the code at night) |
| A level word or colour for a value | `classify_*`, `aqi_level_class`, `compass_direction` in `core/levels.py` |
| Which hour is now, today's high/low, sun times | `nearest_hour_index`, `today_high_low`, `today_sun_times` in `core/forecast.py` |
| A short message | `create_toast(text)` from `ui/gtk_utils.py`, added to the window's `Adw.ToastOverlay` |
| Loading, empty, error page | `Adw.StatusPage`, as `_update_view_state` in `ui/window.py` builds them |
| A signal handler on a rebuilt widget | `weak_connect(widget, signal, self.method)` |
| A Cairo draw function | `safe_set_draw_func(area, self, "draw")` |
| A one-line summary of the coming hours | `overview_engine`: read `current()` and `heading`, listen to `overview-changed` |
| A yes/no question about one forecast hour | `HasCode`, `AtLeast`, `Below`, `AnyOf`, `AllOf`, or a shared one (`IS_WET`, `IS_FOGGY`, `IS_WINDY`, …) in `core/overview/hour_tests.py` |

**Weather codes** are WMO codes as strings (`"61"`), with an `n` suffix at
night (`"61n"`). A code must be in `icons_default`, `icons_material`,
`bg_css` and `condition` together.

### 8.3 Components

**Create a component only when** it is reused, makes a window easier to
read, or is a clear UI concept (a card, a forecast row, a graph). No tiny
one-off components. When unsure, ask:

> Should this UI be extracted into a reusable component, or should I keep it
> inside the current window for now?

| Kind | How |
| --- | --- |
| Section or card with state, timers or signal handlers | subclass a GTK widget (`Gtk.Box`, `Gtk.Grid`), as `CurrentCondition` and `Forecast` do. Connect on `map`; disconnect and remove sources on `unmap` |
| Drawing piece | owns its `Gtk.DrawingArea`, sets the draw function with `safe_set_draw_func`, builds everything in `__init__`, hands it out as `.widget` (`PollutionBar` is the exception: it subclasses `Gtk.DrawingArea`) |
| Window or dialog | moves its layout into a `Gtk.Template` `.ui` file in `ui/templates/` over time |

A component is ready when its constructor returns: no separate
`create_card()` step.

### 8.4 Matching a design

When the user gives a design image or screenshot, **replicate it exactly,
pixel for pixel**: layout, spacing and margins, font sizes and hierarchy,
colours and opacity, border radius, alignment and position, proportions, and
every visible element. Don't approximate or simplify unless asked.

### 8.5 Mousam design rules

- **libadwaita and the HIG first.** Stock widgets and style classes (`card`,
  `view`, `pill`, `suggested-action`, `flat`, `linked`, `dim-label`, …)
  before custom CSS.
- **Layout:** content sits in `card` boxes inside an `Adw.Clamp` (max
  1400px). Cards keep the grid's spacing (3–12px margins, 6px between rows
  inside a card).
- **Text hierarchy** from the `style.css` utility classes (see the
  `CSS_TEXT_*` lists in `ui/cards/metric.py`):

  | Text | Classes |
  | --- | --- |
  | title | `text-lg opacity-80 font-medium` |
  | value | `text-3xl font-medium` |
  | unit | `text-sm opacity-80` |
  | level | `text-base opacity-90 font-semibold` |

- **Every number has its unit; every level colour has words** ("Moderate",
  "High"). Levels from `classify_*` in `core/levels.py`; AQI colours from
  `THRESHOLDS` in `config.py`.
- **Icons:** symbolic theme icons for buttons (`view-refresh-symbolic`, …);
  weather icons only through `ui/icons.py`. Both icon themes must look right
  (Material icons are drawn smaller: `get_icon_pixel_size`).
- **One `suggested-action` button per page**, for the main action (Add
  Location, Retry).
- **Dynamic backgrounds:** cards add `bg-dark-overlay` so text stays
  readable on any weather gradient.
- **Every screen works** in light and dark, with dynamic backgrounds on and
  off, metric and imperial, 12h and 24h, and from about 360px wide to full
  screen without clipping. Long translated strings wrap or ellipsize.

### 8.6 Loading states

- The main window shows one view state at a time in `main_stack`: `loader`,
  `welcome` (no locations), `error_no_internet`, `error_api`, `content`.
  Switch with `_update_view_state(state, message)`; no extra spinners on top.
- The window shows the loader, calls `weather_store.refresh()`, and switches
  on `notify::status`: `ready` rebuilds `content`, `offline` shows
  `error_no_internet`, `error` shows `error_api` with `weather_store.error`.
  There are no fetch callbacks.
- Sections get their data when built, so they never wait. `HourlyDetails`
  and `Forecast` build a tab's page the first time it is chosen. If a page
  gets heavy enough to slow the first paint, show a spinner in it and fill
  it with `GLib.idle_add`.
- Errors the user can fix say how ("Please check your connection.") and
  offer Retry.

### 8.7 Styling

All custom styling is in [src/css/style.css](src/css/style.css), loaded once
in `WeatherApplication.do_activate`. Apply it with `add_css_class` /
`set_css_classes`.

- **Reuse the utility classes:** typography (`text-xs` … `text-8xl`,
  `font-light` … `font-bold`), spacing (`m-*`, `mt-*`, `mb-*`, `my-*`, …),
  opacity, borders, `btn-sm` / `btn-md` / `btn-lg`, `bg-weather-*`
  backgrounds, `compact-*` for the compact window.
- **Sizes in `rem`**, so they follow the user's text scaling.
- **Named colours** (`@accent_color`, `@window_fg_color`, `@card_bg_color`,
  …) or `currentColor` and opacity, not hex, so light, dark and high contrast
  work. The weather gradients are the exception.
- **A repeating pattern** gets a class in `style.css`, not repeated widget
  calls.
- Margins and sizes can also be set from code (`set_margin_*`,
  `set_size_request`); match the surrounding component.

**When code, not CSS:**

| Case | Why | Use |
| --- | --- | --- |
| Graphs, gauges, arcs, rotated icons | CSS can't draw them | Cairo in a `Gtk.DrawingArea` via `safe_set_draw_func` (`ui/drawing/`) |
| Size of a drawing area | it decides the drawing's layout | `set_size_request` |
| Layout (expand, align, grid spans) | not CSS properties in GTK | `set_hexpand`, `set_halign`, `Gtk.Grid.attach` |
| A value known only at runtime (a level's position) | changes per fetch | pass it into the drawing class |
| A colour for a level | picked from data | a CSS class chosen in code (`success`, `warning`, `error`) |
| Icon size | depends on the icon theme | `get_icon_pixel_size` / `set_pixel_size` |

Cairo colours are `[r, g, b]` floats from 0 to 1. Prefer the existing blue
`[0.38, 0.7, 1]` and the level colours already used, so drawings match the
CSS.

### 8.8 Quality bar

The app should feel native to GNOME, calm and glanceable (the answer to
"what's the weather?" in one look), polished, and fast to open and refresh.
Use libadwaita widgets and patterns, cards with clear hierarchy (not heavy
borders), toasts for short confirmations, `Adw.StatusPage` for empty and
error states, keyboard shortcuts for main actions (listed in
`ui/templates/shortcuts.ui`), and simple crossfades where useful.

---

## 9. Python and code style

There is no formatter. When a file differs from these conventions, follow
the file.

### 9.1 Python

- **Target Python 3.12** (`target-version` in `ruff.toml`): nothing newer,
  even if your machine or the runtime has it.
- **Relative imports** inside `src/` (`from ..services.settings import
  settings`). Never `import settings` or `sys.path` hacks.
- **Singletons are module instances**: import `settings`, `weather_store`,
  `overview_engine`, `log_manager`. Never construct `Settings()` or
  `WeatherStore()` (tests do, with fakes).
- **Type hints** on new functions, kept simple. Keep `typing.List` /
  `Optional` in files that use them; prefer `list[str]` and `str | None` in
  new files.
- **API data goes into `core/models.py`** and is read as attributes
  (`cw.temperature_2m.data`, `.unit`, `.level_str`), not raw dicts.
- **No bare `except:`.** Catch the specific exception and log it
  (`requests.RequestException` in the API modules, `(KeyError, TypeError,
  ValueError)` when parsing JSON). A broad `except Exception` only at
  boundaries that must not crash (a worker thread's top level,
  `RuleBook.run`), logged.
- **No mutable defaults** (`def f(items=None)`, then `items = items or []`),
  and no module-level state other than the singletons and constants.
- **Times** are unix timestamps from the API. Convert with
  `datetime.fromtimestamp(ts, ZoneInfo(tz))` in the city's time zone, never
  naive `datetime.now()` / `fromtimestamp(ts)`.
- **Gettext per module:** `from gettext import gettext as _` (and `pgettext
  as C_`, `ngettext`); don't rely on the builtin `_` from the launcher.
- **Logging:** `get_logger("<area>")` from `core/log.py`, never `print`. It
  is silent unless debug mode is on. `app.main()` calls
  `log_manager.setup(debug)` once; Preferences calls `update_level(debug)`.
- **`gi.require_version(...)`** before importing from `gi.repository`.
- **Logic that doesn't need GTK** (classification, conversions, parsing) is
  a plain function or `@staticmethod`, so it is easy to test.

### 9.2 Naming

| Thing | Style |
| --- | --- |
| Modules | lowercase `snake_case`, in their layer's folder; the folder says the layer (`core/levels.py`, not `core/core_levels.py`) |
| Classes | `PascalCase` |
| Functions, methods, variables | `snake_case` |
| Constants | `UPPER_SNAKE`, in `config.py` or at the top of a module (`CSS_TEXT_TITLE`) |
| Private | leading `_` for anything not used outside its class or module |
| Signal handlers | `_on_<source>_<what>` (`_on_store_status`) |
| Idle and timeout callbacks | what they do (`_start_loading`), not `_callback` |

Names say what they hold, with the unit when it matters: `delay_seconds`,
`week_min`, `sunrise_ts`, not `d`, `tmp`, `data2`.

### 9.3 Layout

- Double quotes. 4 spaces (PEP 8).
- Lines up to about 100 characters. Wrap long calls inside the brackets, one
  argument per line if they don't fit; no backslash continuations.
- Two blank lines between top-level definitions, one between methods.
- Long classes are split with section comments: `# ---------- Data ----------`.
- Imports: standard library, then `gi` with `gi.require_version(...)`, then
  `gi.repository`, then local relative imports. Import names, not `*`.

### 9.4 Functions

- Short and flat: return early instead of nesting `if`s. Split out a helper
  once a function does two things (build vs. fill, fetch vs. parse).
- Pass values in; don't reach for globals.
- GLib callbacks return `GLib.SOURCE_REMOVE` / `GLib.SOURCE_CONTINUE`, never
  `True` / `False` / `None`.
- Build widgets with constructor keywords when there are only a few
  (`Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)`), then setters
  for the rest, as the surrounding code does.

### 9.5 Strings

- f-strings for untranslated strings (logs, CSS class names, debug output).
- Translated strings with values use named placeholders and `.format()`:
  `_("Material icons: {name}").format(name=…)`. Never `_(f"…")`.
- Log messages say what happened and the value that matters:
  `logger.error(f"Air quality fetch failed: {e}")`. Log only coordinates and
  city names, nothing else about the user.

### 9.6 Comments and docstrings

- Public classes and functions get a docstring: a one-line summary, then a
  short paragraph if the behaviour isn't obvious (see `DrawTempRange`,
  `DrawTickGauge`).
- Comments explain *why* (a thread, a GTK quirk, a leak avoided), not what
  the next line does. Plain English, full sentences, readable by a newcomer.
- No commented-out code, `print` calls, or notes like "moved to …". Git keeps
  the history.

### 9.7 Diffs

- Change only what the task needs. Don't reformat, rename or reorder code
  you aren't otherwise touching: it hides the real change and breaks other
  contributors' branches.
- Fix typos in names only in a separate refactor commit, updating every
  caller.

---

## 10. Data

- **Open-Meteo is the only source**: forecast (`OPEN_METEO_BASE_URL`), air
  quality (`AIR_QUALITY_BASE_URL`), geocoding (`GEOCODING_BASE_URL`), all in
  `config.py`. It needs no API key; never add one.
- **Time:** request `timeformat=unixtime`, and handle time zones through
  `get_time_difference` / the selected city's `timezone`. Never assume the
  city is in the system time zone.
- **Units:** imperial is requested from the API where supported
  (`temperature_unit`, `wind_speed_unit`). Pressure (hPa → inHg,
  `HPA_TO_INHG`) and visibility (m → km / miles) are converted by us, in the
  API layer, `core/units.py` or the store's model building, never in widgets.
- **A new field:** add it to the request list in the API module, to the
  model's annotations in `core/models.py`, and (if it gets a level) a
  `classify_*` function in `core/levels.py`.
- **Privacy:** send nothing about the user to any service except the
  coordinates and city name the request needs.

---

## 11. Translations

- Wrap every user-visible string in `_()`. When a word is ambiguous out of
  context ("Low", "Moderate"), use `C_("context", "...")`, as the level
  classifiers do.
- Counts use plural forms: `ngettext("{n} minute", "{n} minutes", n)`.
- A string with placeholders gets a `# Translators:` comment right above it,
  saying what each one holds.
- Translate whole sentences with placeholders; never join translated pieces.
- Never translate **Mousam**.
- After adding or changing strings, run `./update-pot`. Don't edit
  `po/*.po` by hand or machine-translate them: translators maintain them
  (including through Weblate).
- A new language goes in `po/LINGUAS` with its `.po` file.

---

## 12. Testing and checks

### 12.1 Unit tests

- **Where:** `tests/`, one file per area (`test_levels.py`,
  `test_forecast.py`, `test_locations.py`, `test_api.py`,
  `test_weather_store.py`, `test_overview_rules.py`,
  `test_notifications.py`), using `unittest` (no pytest), registered in
  [tests/meson.build](tests/meson.build) so `meson test` and CI run them. A
  new test file goes there too.
- **How they run:** they import the source tree as the `mousam` package (see
  the shim at the top of `tests/test_overview_rules.py`), so they need no
  install, display or network.
- **What can be tested this way:** GTK-free modules, plus the store
  (`test_weather_store.py`, GLib and GObject) and the notifications
  (`test_notifications.py`, Gio, with a fake app), which need no display. CI
  installs `python3-gi` for them.
- **Fakes** (`tests/fakes.py`): `FakeRequests` for `requests` (API tests),
  `FakeForecastClient` for the forecast API, `FakeSettings` for the GSettings
  wrapper (which needs the installed schema).
- **Fixed clocks and hand-built data**, never the real time or Open-Meteo.
- **New GTK-free logic** (a rule, a classifier, a conversion, a parser) gets
  a test.

### 12.2 Before declaring a task done

```bash
ruff check src tests
python3 -m compileall -q src
for t in tests/test_*.py; do python3 "$t"; done
```

- `src/` is free of ruff findings; the Checks workflow
  (`.github/workflows/checks.yml`) keeps it that way, along with
  `compileall` and `meson test`. Fix a finding rather than silencing it;
  change `ruff.toml` only for a rule that doesn't fit the whole codebase.
- Touched the gschema, appdata or desktop file: run their validators too
  (section 3).
- Then build, install and run the app, and check the change in light and
  dark, metric and imperial.

### 12.3 Performance check

If you touched refresh, rendering, signals or main-loop sources, watch CPU
and memory across several refreshes, including quick back-to-back ones
(Ctrl+R several times, or switching location): `top -p <pid>` must settle
near 0% CPU once loading ends, and RSS must not keep climbing. In the
Flatpak, the app process is `python3 /app/bin/mousam`, not the `bwrap`
wrappers.

---

## 13. Packaging and release

- **Flatpak:** [io.github.amit9838.mousam.json](io.github.amit9838.mousam.json).
  Keep its sandbox permissions (`finish-args`) as small as they are; a new
  permission needs a strong reason and user approval.
- **Snap:** `snap/snapcraft.yaml`, built from the checkout. A change to
  dependencies or installed files must be reflected there.
- **Version:** lives in `meson.build` (filled into `VERSION` in
  `src/config.py`) and a new `<release>` in
  `data/io.github.amit9838.mousam.appdata.xml.in` (with release notes, shown
  on the About dialog's What's New page). Change them together, and only
  when asked to prepare a release.
- **Screenshots:** visible changes to the app's look come with updated
  `docs/screenshots/` when the user asks; the appdata, README and website
  use them.

---

## 14. Git

- **Never commit until asked.**
- Commit phase by phase: one logical change per commit.
- **Don't add Claude as a co-author.**
- Messages follow Conventional Commits: `type(scope): subject`, with `feat`,
  `fix`, `refactor`, `chore`, `style`, `docs` (e.g. `fix(render): …`,
  `chore(po): …`).
- **Plan documents** end in `-plan.md` (`docs/abc-plan.md`). They stay local,
  are gitignored, and are never committed.
- `.gitignore` ignores `test*` everywhere except `tests/`: files under
  `tests/` are tracked, but a `test*` file elsewhere (like
  `src/test_memory_leak.py`) is not.
