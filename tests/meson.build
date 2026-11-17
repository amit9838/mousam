python = find_program('python3')

# Plain Python, no GTK: runs from the source tree, nothing to install
test('Overview rules', python, args: [files('test_overview_rules.py')])
test('Levels and units', python, args: [files('test_levels.py')])
test('Forecast', python, args: [files('test_forecast.py')])
test('Locations and time zones', python, args: [files('test_locations.py')])
test('Open-Meteo API', python, args: [files('test_api.py')])
# Needs PyGObject (GLib and GObject, no display)
test('Weather store', python, args: [files('test_weather_store.py')])
# Needs PyGObject (Gio, no display)
test('Notifications', python, args: [files('test_notifications.py')])
