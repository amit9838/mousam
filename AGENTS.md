You are an expert Python + GTK4 / libadwaita engineer helping maintain **Mousam**, an open-source GNOME weather app.

You write clean, simple, maintainable code. You prioritize clarity over unnecessary abstraction: Mousam is a community project, and contributors of every level read and change this code.

Think like a senior GNOME app developer, but implement like someone keeping a small, practical codebase easy to follow.

---

## Project Overview

**Mousam** (tagline: *Weather at a Glance*) is a desktop weather app for Linux, published on Flathub, the Snap Store and (unofficially) Debian. App ID: `io.github.amit9838.mousam`. See [README.md](README.md) for features, install and build steps, and [CONTRIBUTION_GUIDE.md](CONTRIBUTION_GUIDE.md) for the contribution process.

The app lets users:

- search for and save locations, and switch between them
- see current conditions: temperature, feels like, humidity, wind, pressure, UV index, dew point, visibility
- read a one-line overview of the coming hours ("Rain likely around 5:00 PM (70% chance).") behind the info button under the current conditions
- browse hourly (temperature, wind, precipitation), tomorrow and 7-day forecasts with graphs
- check air quality (US / EU AQI, pollutants, pollen) with WHO-based levels
- follow the sun and moon through the day/night card
- switch to a compact window
- get a desktop notification when data refreshes
- set preferences: metric or imperial, 12/24h clock, precipitation in inches, dynamic backgrounds, icon theme (default or Material), weather overview on/off, auto-refresh interval, debug mode

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
- Flatpak (GNOME runtime), Snap and Debian packaging

Do not introduce other libraries unless there is a strong reason (see "Decision Making"). Every new Python dependency must also be packaged for Flatpak, Snap and Debian.

---

## GTK and libadwaita change — do not trust your training data

Widgets get deprecated and replaced between libadwaita releases (`Adw.PreferencesWindow` → `Adw.PreferencesDialog`, `Adw.AboutWindow` → `Adw.AboutDialog`, `Gtk.Spinner` → `Adw.Spinner`, …). Before using a GTK or libadwaita API:

1. Read `runtime-version` in [io.github.amit9838.mousam.json](io.github.amit9838.mousam.json) to know which GNOME runtime we ship against. CI ([.github/workflows/flatpak.yml](.github/workflows/flatpak.yml)) builds on an older GNOME image, so don't rely on an API newer than both.
2. Check the API in the official docs, not from memory:
   - GTK 4: https://docs.gtk.org/gtk4/
   - libadwaita: https://gnome.pages.gitlab.gnome.org/libadwaita/doc/ (pick the matching version)
   - PyGObject: https://pygobject.gnome.org/
   - Open-Meteo: https://open-meteo.com/en/docs (and its air-quality and geocoding pages)
3. Follow the [GNOME Human Interface Guidelines](https://developer.gnome.org/hig/) for layout, wording and patterns.

Existing windows still use `Adw.PreferencesWindow`, which is deprecated. Don't spread it to new dialogs; ask before migrating the existing ones.

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
ruff check <files you touched>      # lint (see "Linting and Validation")
python3 -m py_compile src/*.py      # syntax check
glib-compile-schemas --strict --dry-run data/
appstreamcli validate data/io.github.amit9838.mousam.appdata.xml.in
desktop-file-validate data/io.github.amit9838.mousam.desktop.in

# Translations
./update-pot                         # regenerate po/mousam.pot from po/POTFILES
./update-po                          # merge the template into every po/*.po

# Debugging
gsettings set io.github.amit9838.mousam debug-mode true   # logs to the console and ~/.cache/mousam/mousam.log
python3 src/test_memory_leak.py --duration 10              # watches RSS across auto-refreshes (local only, git-ignored)
```

Run the installed app, not `python3 src/main.py`: `configs.py` and `CORE_Icons.py` are filled in by Meson (`@icon_location@`), the GSettings schema must be installed, and `src/` is imported as the `mousam` package. After changing any source, run `meson install -C builddir` again.

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
  - Clearly explain why it is useful, and what packaging it costs (Flatpak module, Snap part, Debian dependency)
  - Ask the user for permission before adding it

Example:

> "This could be done by hand with Cairo, but a libadwaita widget already does it and follows the theme. Do you want me to switch to it?"

Do not add new libraries without user approval. Prefer what GTK, libadwaita, GLib/Gio and the Python standard library already provide.

---

## Architecture Guidelines

Use this structure unless there is a strong reason to change it. The file prefix tells you the layer.

```txt
src/
  main.py                 WeatherApplication (Adw.Application): actions, CSS, auto-refresh, normal ↔ compact switching
  mousam.py               WeatherMainWindow: header bar, view states (loader, welcome, errors, content), the card grid
  mousam.in               launcher script (Meson fills in paths, sets up gettext, loads the GResource)
  window*.py              secondary windows: Locations (+ city search), Preferences, About
  shortcutsDialog.py/.ui  keyboard shortcuts (Gtk.Template from the GResource)
  UI_*.py                 sections and cards: CurrentCond, HourlyDetails, Forecast, CardSquare, CardDayNight, CardAirPollution, CompactWeather
  UI_CompDraw*.py         small Cairo-drawn pieces used by the cards
  CORE_weatherData.py     WeatherDataManager: the one holder of fetched data, level classification, signals
  CORE_Overview.py        OverviewEngine: when the overview runs and is announced; publishes "overview-changed"
  CORE_OverviewRules.py   the overview rules: Insight, OverviewContext, HourTest, Phrasing, Rule, RuleBook (no GTK)
  CORE_OverviewMessages.py the overview wordings: several per message key, picked by MessageBook (no GTK)
  CORE_Networking.py      fetch_all_weather_data_async: runs every fetch on worker threads
  CORE_Models.py          WeatherField, CurrentWeather, HourlyWeather, DailyWeather, AirPollutionData, Location
  CORE_Icons.py           weather icon paths (default + Material), background CSS classes, condition names per WMO code
  CORE_GTKUtils.py        AutoRefreshTimer, weak_connect, safe_set_draw_func, show_notification
  CORE_Helpers.py         internet check, coordinates and timezone of the selected city, toasts, JSON helpers
  CORE_Cache.py           @cached: TTL + LRU cache for API calls
  CORE_Logging.py         LogManager and get_logger
  API_*.py                one module per Open-Meteo API: Weather, AirPollution, FindCity
  configs.py              constants: app ID, version, URLs, timeouts, cache sizes, refresh options, AQI thresholds
  settings.py             the Settings singleton: one property per GSettings key
  css/style.css           all custom styling
  mousam.gresource.xml    files bundled into the GResource
data/                     gschema, .desktop, appdata, icons (default_icons, material_icons), Flatpak dependency
po/                       translations (POTFILES, LINGUAS, mousam.pot, *.po)
build-aux/, snap/, debian/ packaging
docs/                     overview-rules.md (source of truth for the overview rules); local *-plan.md files
website/                  the project website (React + Vite + Tailwind), separate from the app
screenshots/              images for README and appdata
```

### Layers

Each layer may import only the ones below it:

```txt
main / mousam / window* → UI_* → UI_CompDraw* → CORE_GTKUtils, CORE_Icons, CORE_Overview → CORE_Networking → CORE_weatherData → API_* → CORE_Cache, CORE_Helpers, CORE_Models, CORE_OverviewRules, CORE_OverviewMessages, CORE_Logging → settings, configs
```

- UI code never calls `API_*` directly. It reads `weather_manager` (from `CORE_weatherData`) and asks for a refresh through `fetch_all_weather_data_async`. The one exception is the city search in `windowLocations.py`, which calls `find_city`.
- `API_*` modules only build URLs, call `requests` and return the JSON (with unit conversions the API doesn't do itself). No GTK, no models.
- `CORE_weatherData` turns raw JSON into models and adds derived values (levels, nearest-hour fields). No widgets.
- Read and write saved values only through `settings` (`src/settings.py`), never with a new `Gio.Settings(...)`.
- Constants (URLs, timeouts, thresholds, option lists) go in `configs.py`, not inline.

Nothing enforces these rules automatically, so keep to them by hand. Some imports are done inside functions to avoid import cycles; keep them that way.

### Adding a file

A new module under `src/` must be added to:

- `mousam_sources` in [src/meson.build](src/meson.build), or it won't be installed
- [po/POTFILES](po/POTFILES), if it has translatable strings
- [src/mousam.gresource.xml](src/mousam.gresource.xml), if it's a `.ui` or other bundled resource

### UI_* components

Create a component only when:

- it is reused in multiple places
- it makes a window easier to read
- it represents a clear UI concept like a card, a forecast row or a graph

Do not create tiny one-off components too early.

When unsure, ask:

> Should this UI be extracted into a reusable component, or should I keep it inside the current window for now?

**Reuse before you build.** Check `src/UI_*.py` and `src/CORE_*.py` before writing UI by hand. These already exist:

| Need | Use |
| --- | --- |
| A metric card (title, value, unit, level, sub line, gauge) | `CardSquare(...).card` |
| Sun / moon card | `CardDayNight().card` |
| Air quality card | `CardAirPollution().card` |
| Hourly graphs with tabs | `HourlyDetails` |
| Tomorrow / 7-day list | `Forecast` |
| Vertical level gauge | `DrawLevelBar` |
| Small bar | `DrawBar` |
| Line graph with "now" marker | `LineGraph` |
| Rotated icon (wind direction) | `DrawImage` |
| Day/night arc | `DrawDayNight` |
| Pollutant level bar | `PollutionBar` |
| A weather icon for a WMO code | `create_weather_icon(code, settings.icon_theme, size)` or `get_icon_path(...)` |
| A condition's name | `condition[code]` in `CORE_Icons` |
| A background for a condition | `bg_css[code]` (append `n` to the code at night) |
| A short message | `create_toast(text)` added to the window's `Adw.ToastOverlay` |
| Loading, empty, error page | `Adw.StatusPage`, as `_update_view_state` in `mousam.py` builds them |
| A signal handler on a rebuilt widget | `weak_connect(widget, signal, self.method)` |
| A Cairo draw function | `safe_set_draw_func(area, self, "draw")` |
| A one-line summary of the coming hours | `overview_engine` (`CORE_Overview`): read `current()` and `heading`, listen to `overview-changed` |
| A yes/no question about one forecast hour | `HasCode`, `AtLeast`, `Below`, `AnyOf` in `CORE_OverviewRules` |

Weather codes are WMO codes as strings (`"61"`), with an `n` suffix for night (`"61n"`). A code must be in `icons_default`, `icons_material`, `bg_css` and `condition` together.

### Overview

The overview is the pill under the current conditions. Its rules are written in plain English in [docs/overview-rules.md](docs/overview-rules.md), the **source of truth**: change that file first, then the code and the numbers to match. If the two disagree, the code is wrong.

- **Wordings** (`CORE_OverviewMessages.py`): a map of message key → several wordings (4–5 for common messages, 2 for rare safety ones). Rules only use keys (`ctx.messages.say("rain.start", time=…, chance=…)`, `say_count` for plurals). All wordings of a key say the same thing with the same placeholders.
- **Rules** (`CORE_OverviewRules.py`, no GTK) look at an `OverviewContext` and each returns an `Insight` or `None`. Every insight has a `valid_until`, and must never be shown after it. Build new rules from what exists: a `FirstHourRule` with an `HourTest` and a `Phrasing` covers "the first hour that …"; subclass `Rule` only when that isn't enough. Register it in `RuleBook.default()`. `RuleBook.run` ignores a rule that fails (debug log only), so one bad rule never breaks the overview.
- **Planner** (`AnnouncePlanner` in `CORE_OverviewRules.py`, no GTK): decides which insight to show and when the pill opens. The next opening is `OVERVIEW_ANNOUNCE_BASE_MINUTES ÷ (1 + score)` (score = sum of priorities ÷ 100), so a busy forecast opens it more often; each opening shows the insight whose turn it is (priority × time since last shown), so none is thrown away; something turning severe opens at once (once, not on every flicker).
- **Engine** (`CORE_Overview.py`): lazy (first run `OVERVIEW_FIRST_DELAY` s after the first data load), runs again before the shown insight stops being true (silent text update) or when the planner's next opening is due. Its memory survives refreshes (a refresh never opens the pill or resets the turns); only a location change or turning the setting off starts over. Each opening draws a new wording seed; silent updates keep it, so the phrasing never changes under the reader. It only ever uses one-shot `GLib.timeout_add_seconds` timers, and does nothing while the `show-overview` setting is off.
- **Section** (`UI_CurrentCond.py`): subscribes to `overview-changed` and `changed::show-overview` on `map`, disconnects on `unmap`. It shows the engine's heading (coloured by severity), the insight's icon and message, and stays open for `insight.show_seconds`.
- **Numbers** (thresholds, priorities, open times, republish intervals) live in `configs.py` under "Overview", in metric; rules convert imperial data before comparing.
- Test rules on made-up forecasts: they are plain Python, so build an `OverviewContext` by hand (`Clock`, `Units`, `HourlySeries`, …) and call `RuleBook.default().run(ctx)`.

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
- Text hierarchy comes from the utility classes in `style.css`: titles `text-lg opacity-80 font-medium`, values `text-3xl font-medium`, units `text-sm opacity-80`, levels `text-base opacity-90 font-semibold` (see the `CSS_TEXT_*` lists in `UI_CardSquare.py`).
- Pair every number with its unit, and every level colour with words ("Moderate", "High"). Levels come from the `classify_*` methods in `CORE_weatherData.py`; AQI colours from `THRESHOLDS` in `configs.py`.
- Icons: symbolic icons from the icon theme for buttons (`view-refresh-symbolic`, …); weather icons only through `CORE_Icons`. Both icon themes must look right; Material icons are drawn smaller (`get_icon_pixel_size`).
- One `suggested-action` button per page, for the main action (Add Location, Retry).
- Every screen must work in light and dark, with dynamic backgrounds on and off, in metric and imperial, and in both 12h and 24h.
- With dynamic backgrounds on, cards add `bg-dark-overlay` so text stays readable on any weather gradient.
- Window sizes from about 360px wide to full screen must not clip or overflow. Long translated strings must wrap or ellipsize.

### Loading states

- The main window has one view state at a time in `main_stack`: `loader`, `welcome` (no locations), `error_no_internet`, `error_api`, `content`. Switch with `_update_view_state(state, message)`; don't add separate spinners on top.
- `content` is rebuilt from `weather_manager` when it signals `notify::is-ready`. Don't build the grid from a fetch callback as well.
- Inside a section (hourly tabs, forecast pages), building heavy content after first paint is fine: show a spinner in that section and fill it with `GLib.idle_add`, as `HourlyDetails` and `Forecast` do.
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
| Graphs, gauges, arcs, rotated icons | CSS can't draw them | Cairo in a `Gtk.DrawingArea` via `safe_set_draw_func` (`UI_CompDraw*`) |
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
- keyboard shortcuts for main actions (listed in `shortcutsDialog.ui`)
- simple crossfade transitions when useful

---

## State Management Rules

- **Saved values** live in GSettings. Add a key to [data/io.github.amit9838.mousam.gschema.xml](data/io.github.amit9838.mousam.gschema.xml), a property to `Settings` in `settings.py`, and (if the user can change it) a row in `windowPreferences.py`. Never rename or retype an existing key: users' saved values would be lost.
- **Fetched data** lives only in the `weather_manager` singleton. Write to it only inside its `update_*` methods, under `self._lock`.
- **Temporary UI state** (selected tab, page, dialog contents) stays on the widget.
- React to changes with signals: `settings.connect("changed::<key>", ...)`, `weather_manager.connect("notify::is-ready", ...)`. Don't poll.
- Locations are stored in `added-cities` as JSON strings; the selected one in `selected-city` as `"lat,lon"`. Use `JsonProcessor`, `LocationData` and `get_cords()`, not your own parsing.

---

## Threading and Performance Rules

- **Never touch GTK from a worker thread.** Network calls run on threads (`fetch_all_weather_data_async`, the city search); hand results back to the main loop with `GLib.idle_add`.
- **One fetch at a time.** `fetch_all_weather_data_async` joins a running fetch instead of starting another; go through it, don't start threads of your own for weather data.
- **Every request has a timeout** (`TIMEOUT` from `configs.py`), and every API function logs and returns `None` on failure instead of raising.
- **API calls are cached** with `@cached` (TTL `DATA_CACHE_TTL`). A new API call uses it too.
- **No leaks across refreshes.** The content grid is rebuilt on every refresh, so widgets must not be kept alive by their own handlers. Connect handlers on rebuilt widgets with `weak_connect`, set draw functions with `safe_set_draw_func`, remove `GLib.timeout_add` sources when the widget goes, and disconnect `settings` handlers you connect from short-lived widgets. Check with `test_memory_leak.py` after touching refresh or widget lifetime.
- **Never poll the main loop.** Don't write a `GLib.idle_add` / `GLib.timeout_add` callback that returns `SOURCE_CONTINUE` while it waits for UI state (a width, a mapped widget, data). Widgets are often built hidden (the content grid is built behind the `loader` page) and may be thrown away before they are ever shown, so such a callback can spin at 100% CPU forever and keep the old widget tree alive. Wait for the signal that reports the change instead: `Gtk.Adjustment` `changed` for a scrolled size, `map` / `realize` for being shown, `notify::<property>` for data. Disconnect a one-shot handler once it has run. The only repeating timers are real clocks and intervals (the compact clock, `AutoRefreshTimer`), and they must be removed when their widget goes.
- **Handlers must not keep widgets alive.** A closure connected to a signal keeps everything it captures. Capture plain values (an index, a string) rather than `self` or other widgets, or use `weak_connect`. Never pass widgets as extra arguments to `GLib.idle_add` / `timeout_add` for a source that can outlive them. An object passed to `safe_set_draw_func` is kept alive by its drawing area, so it must not also keep the area's parent container (no `self.box = Gtk.Box(); self.box.append(self.area)`): hand out the drawing area itself.
- **Keep draw functions light.** They run on every frame: compute in `__init__`, only draw in `draw`.
- **Long lists**: today's lists are short (hours of two days, 7 days). If you add one that can grow, use `Gtk.ListView` rather than appending hundreds of widgets.

---

## Python Rules

- Follow the style of the file you are in (PEP 8, 4 spaces).
- Add type hints to new functions; keep them simple.
- Data from the API goes into `CORE_Models` classes and is read as attributes (`cw.temperature_2m.data`, `.unit`, `.level_str`), not as raw dicts.
- No bare `except:` in new code; catch the specific exception and log it.
- Use `get_logger("<area>")` from `CORE_Logging`, never `print`. Logging is silent unless debug mode is on.
- Keep `gi.require_version(...)` before importing from `gi.repository`, as the files already do.
- New logic that doesn't need GTK (classification, conversions, parsing) should be a plain function or `@staticmethod` so it stays easy to test.

---

## Data Rules

- Open-Meteo is the only data source: forecast (`OPEN_METEO_BASE_URL`), air quality (`AIR_QUALITY_BASE_URL`) and geocoding (`GEOCODING_BASE_URL`), all in `configs.py`. It needs no API key; never add one to the app.
- Request `timeformat=unixtime`, and handle time zones through `get_time_difference` / the selected city's `timezone`. Never assume the city is in the system time zone.
- Units: imperial is requested from the API where it supports it (`temperature_unit`, `wind_speed_unit`); pressure (hPa → inHg, `HPA_TO_INHG`) and visibility (m → km / miles) are converted by us. Keep conversions in the API layer or `WeatherDataManager`, not in widgets.
- A new field means: add it to the request list in the `API_*` module, to the model's annotations in `CORE_Models.py`, and (if it gets a level) a `classify_*` method in `CORE_weatherData.py`.
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
- Snap (`snap/snapcraft.yaml`, `build-aux/snapcraft.yaml`) and Debian (`debian/`) are maintained too; a change to dependencies or installed files must be reflected there.
- The version lives in three places: `meson.build`, `VERSION` in `src/configs.py`, and a new `<release>` in `data/io.github.amit9838.mousam.appdata.xml.in` (with release notes). Change them together, and only when asked to prepare a release.
- User-visible changes to the app's look should come with updated `screenshots/` when the user asks for it; the appdata points at them.

---

## Linting and Validation

Run before declaring any task done:

```bash
ruff check <files you touched>
python3 -m py_compile src/*.py
```

The codebase already has ruff findings. Don't add new ones in the code you change, and don't mass-fix unrelated ones in the same change. If you touched the gschema, appdata or desktop file, run their validators too (see "Commands").

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
- `.gitignore` also ignores `test*`, so a new test file won't be tracked unless you `git add -f` it or change that rule
