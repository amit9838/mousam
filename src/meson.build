pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'mousam')
gnome = import('gnome')

# The appdata is generated in data/, so look for it there too
gnome.compile_resources('mousam',
  'mousam.gresource.xml',
  gresource_bundle: true,
  source_dir: [meson.current_source_dir(), meson.project_build_root() / 'data'],
  dependencies: [appstream_file],
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
  'CORE_Overview.py',
  'CORE_OverviewMessages.py',
  'CORE_OverviewRules.py',
  'CORE_Icons.py',
  'CORE_Logging.py',

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
  'UI_CompDrawLineGraph.py',
  'UI_CompDrawTickGauge.py',
  'UI_CompDrawTempRange.py',
  'UI_CompactWeather.py',

  'configs.py',
  'CORE_Cache.py',
  'CORE_Helpers.py',
  'CORE_Networking.py',
  'CORE_GTKUtils.py',
  'settings.py',
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
icon_conf.set('VERSION', meson.project_version())

configure_file(
  input: 'configs.py',
  output: 'configs.py',
  configuration: icon_conf,
  install: true,
  install_dir: moduledir
)

configure_file(
  input: 'CORE_Icons.py',
  output: 'CORE_Icons.py',
  configuration: icon_conf,
  install: true,
  install_dir: moduledir
)
