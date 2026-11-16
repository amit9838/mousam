python = find_program('python3')

# Plain Python, no GTK: runs from the source tree, nothing to install
test('Overview rules', python, args: [files('test_overview_rules.py')])
test('Levels and units', python, args: [files('test_levels.py')])
test('Forecast', python, args: [files('test_forecast.py')])
test('Locations and time zones', python, args: [files('test_locations.py')])
# GTK, requests and GSettings are stubbed (tests/stubs.py) until the API
# layer is pure
test('API URL parameters', python, args: [files('test_api_weather.py')])
