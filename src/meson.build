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
  'CORE_Models.py',
  'CORE_weatherData.py',

  'API_AirPollution.py',
  'API_FindCity.py',
  'API_Weather.py',

  'UI_Forecast.py',
  'UI_CardAirPollution.py',
  'UI_CardDayNight.py',
  'UI_CardSquare.py',
  'UI_CurrentCond.py',
  'UI_HourlyDetails.py',

  'UI_CompDrawBar.py',
  'UI_CompDrawbarLine.py',
  'UI_CompDrawDayNight.py',
  'UI_CompDrawImageIcon.py',
  'UI_CompDrawPollutionBar.py',

  'constants.py',
  'utils.py',
  'config.py',
  'windowAbout.py',
  'windowPreferences.py',
  'windowLocations.py',
  'shortcutsDialog.py'
]

install_emptydir(moduledir / 'css')
install_data('css/style.css',install_dir: join_paths(moduledir,'css'))
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
