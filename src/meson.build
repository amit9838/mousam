pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'weather')
gnome = import('gnome')

gnome.compile_resources('weather',
  'weather.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'weather.in',
  output: 'weather',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr--r--'
)


weather_sources = [
  '__init__.py',
  'main.py',
  'weather.py',
  'uiCurrent_w.py',
  'uiForecast_w.py',
  'backendCurrent_w.py',
  'backendForecast_w.py',
  'constants.py',
  'units.py',
  'utils.py',
  'css.py',
  'windowAbout.py',
  'windowPreferences.py',
]



install_data(weather_sources, install_dir: moduledir)
