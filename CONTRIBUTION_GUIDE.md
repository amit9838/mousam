# Contribution Guide

Thank you for taking the time to contribute to **Mousam** 🌦️
We truly appreciate your effort to help improve the project. This guide explains how you can contribute and what to expect during the review process.

---

## Reporting Bugs or Suggesting Features

If you’d like to report a bug or suggest a new feature or improvement (code, documentation, UI, or anything else):

1. **Check existing issues first** to avoid duplicates.
2. If the issue hasn’t been reported, feel free to **open a new issue**.
3. When reporting a bug, please:

   * Be as **specific** as possible.
   * Describe the **expected behavior** vs the **actual behavior**.
   * Clearly explain the **steps to reproduce** the issue.
   * Include logs, screenshots, or environment details if applicable.

Well-described issues help maintainers understand and fix problems faster.

---

## Submitting Changes (Pull Requests)

Once you’ve identified an issue or feature to work on, follow these steps:

1. **Fork** the repository.
2. Create a **new branch** for your change (recommended).
3. Make your changes and create **clear, focused commits**.

   * Write meaningful commit messages describing *what* and *why*.
4. **Test your changes thoroughly** to ensure:

   * Existing functionality still works.
   * Your new change integrates smoothly with the project.
5. Push your changes to your fork.
6. Open a **Pull Request (PR)** and include:

   * A clear summary of the problem.
   * The solution you implemented.
   * Any relevant screenshots or test details (if applicable).

After submission, your PR will be reviewed. You may receive feedback or requests for changes before it is approved and merged.

---

## Finding Your Way Around the Code

Mousam is a Python app built with GTK 4 and libadwaita. The code in `src/` is installed as the `mousam` package, in four layers. Each layer may use only the layers to its right:

```txt
app.py  →  ui  →  state  →  services  →  core  →  config.py
```

| Folder | What lives there | Example |
| --- | --- | --- |
| `src/core/` | Plain Python logic: models, levels, units, forecast decisions, the overview rules. No GTK, no network, no settings. | `core/levels.py` decides that 85% humidity is "High". |
| `src/services/` | Talking to the outside world: the Open-Meteo APIs, the internet check, the saved settings. | `services/open_meteo.py` fetches the forecast. |
| `src/state/` | What is loaded right now. The windows listen to it. | `state/weather_store.py` fetches a city's weather and reports `loading`, `ready` or `error`. |
| `src/ui/` | Everything on screen: the window, sections, cards, Cairo drawings and dialogs. | `ui/cards/metric.py` draws the Wind, Humidity, Pressure and UV cards. |

Where a change usually goes:

* **A new threshold, URL or option**: `src/config.py`.
* **A new weather value or level**: the request in `services/open_meteo.py`, the model in `core/models.py`, the level in `core/levels.py`, then a card in `ui/`.
* **A change to the overview pill's messages**: describe it in `docs/overview-rules.md` first, then change `core/overview/`.
* **A new file**: put it in the folder of its layer and list it in that folder's `meson.build`, or it won't be installed.

Before opening a PR, run the checks CI runs:

```bash
ruff check src tests
python3 -m compileall -q src
for t in tests/test_*.py; do python3 "$t"; done
```

Then build and run the app (see [README.md](README.md)) and try your change in light and dark mode, and in metric and imperial units.

[AGENTS.md](AGENTS.md) has the full set of rules: layers, threading, styling, translations and commit messages.

---

## Translation Contributions 🌍

We welcome translation contributions to help Mousam reach more users worldwide.

### How to Contribute Translations

1. Check the existing localization files to see if your language already exists.
2. If adding a new language:

   * Create a new translation file following the existing structure.
3. If improving an existing translation:

   * Ensure accuracy, clarity, and consistency.
4. Test the app to confirm translations display correctly.

### Important Translation Rules

* ❗ **Do NOT translate branding terms**, including:

  * **Mousam**
* Keep technical terms consistent with the rest of the project.
* Avoid machine-only translations without review.

If you’re unsure about wording or context, feel free to open an issue or ask for clarification before submitting.

---

## Code of Conduct

Please be respectful and constructive in all interactions. We aim to maintain a welcoming and inclusive community for everyone contributing to Mousam.

---
