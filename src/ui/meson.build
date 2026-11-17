install_data(
  '__init__.py',
  'compact_window.py',
  'gtk_utils.py',
  'notifications.py',
  'window.py',
  install_dir: moduledir / 'ui',
)

# Filled in by Meson: the icon folder
configure_file(
  input: 'icons.py',
  output: 'icons.py',
  configuration: icon_conf,
  install: true,
  install_dir: moduledir / 'ui',
)

subdir('cards')
subdir('dialogs')
subdir('drawing')
subdir('sections')
