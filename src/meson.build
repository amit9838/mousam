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
  'CORE_GTKUtils.py',
  'CORE_Overview.py',
  'CORE_weatherData.py',
  'UI_CardAirPollution.py',
  'UI_CardDayNight.py',
  'UI_CardSquare.py',
  'UI_CompDrawBar.py',
  'UI_CompDrawDayNight.py',
  'UI_CompDrawImageIcon.py',
  'UI_CompDrawLineGraph.py',
  'UI_CompDrawPollutionBar.py',
  'UI_CompDrawRainDrop.py',
  'UI_CompDrawTempRange.py',
  'UI_CompDrawTickGauge.py',
  'UI_CompDrawbarLine.py',
  'UI_CompactWeather.py',
  'UI_CurrentCond.py',
  'UI_Forecast.py',
  'UI_HourlyDetails.py',
  'main.py',
  'mousam.py',
  'shortcutsDialog.py',
  'windowAbout.py',
  'windowAirQuality.py',
  'windowLocations.py',
  'windowPreferences.py',
]

install_emptydir(moduledir / 'css')
install_data('css/style.css', install_dir: moduledir / 'css')
install_data(mousam_sources, install_dir: moduledir)

# Filled in by Meson: the icon folder and the version
icon_conf = configuration_data()
icon_conf.set('icon_location', get_option('prefix'))
icon_conf.set('VERSION', meson.project_version())

configure_file(
  input: 'CORE_Icons.py',
  output: 'CORE_Icons.py',
  configuration: icon_conf,
  install: true,
  install_dir: moduledir
)

configure_file(
  input: 'config.py',
  output: 'config.py',
  configuration: icon_conf,
  install: true,
  install_dir: moduledir
)

subdir('core')
subdir('services')
