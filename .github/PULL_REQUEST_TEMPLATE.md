## What does this change?

<!-- A short summary of the problem and how this fixes it. Link the issue, e.g. "Fixes #123". -->

## How was it tested?

<!-- What you ran, on which system, and what you saw. For visual changes, light and dark, metric and imperial. -->

## Checklist

- [ ] `ruff check src` and `python3 -m py_compile src/*.py` pass
- [ ] `meson test` passes after building (see the README)
- [ ] I ran the installed app and checked the change in light and dark mode
- [ ] New user-visible text is wrapped in `_()` and `./update-pot` was run (translations in `po/*.po` are left to translators)
- [ ] New files are added to `src/meson.build`, `po/POTFILES` and `src/mousam.gresource.xml` where needed
- [ ] Screenshots are attached if the look of the app changed
