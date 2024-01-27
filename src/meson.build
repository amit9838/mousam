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
  'main.py',
  'weather.py',
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



install_data(weather_sources, install_dir: moduledir)
