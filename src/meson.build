pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'mousam')
gnome = import('gnome')

gnome.compile_resources('mousam',
  'mousam.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'mousam.in',
  output: 'mousam',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x'
)

mousam_sources = [
  'main.py',
  'mousam.py',
  'weatherData.py',
  'Models.py',

  'backendAirPollution.py',
  'backendFindCity.py',
  'backendWeather.py',

  'frontendForecast.py',
  'frontendCardAirPollution.py',
  'frontendCardDayNight.py',
  'frontendCardSquare.py',
  'frontendCurrentCond.py',
  'frontendHourlyDetails.py',

  'frontendUiDrawBar.py',
  'frontendUiDrawbarLine.py',
  'frontendUiDrawDayNight.py',
  'frontendUiDrawImageIcon.py',
  'frontendUiDrawPollutionBar.py',

  'application.css',
  'constants.py',
  'units.py',
  'utils.py',
  'css.py',
  'windowAbout.py',
  'windowPreferences.py',
  'windowLocations.py'
]

install_data(mousam_sources, install_dir: moduledir)

icon_conf = configuration_data()
icon_conf.set('icon_location', get_option('prefix'))

configure_file(
  input: 'constants.py',
  output: 'constants.py',
  configuration: icon_conf,
  install: true,
  install_dir: moduledir
)
