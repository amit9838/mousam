python = find_program('python3')

# Plain Python, no GTK: runs from the source tree, nothing to install
test('Overview rules', python, args: [files('test_overview_rules.py')])
test('Levels', python, args: [files('test_levels.py')])
# Today's levels, units and location formatting; GTK, requests and
# GSettings are stubbed (tests/stubs.py) until the logic moves out of them
test('Levels and formatting', python, args: [files('test_levels_and_formatting.py')])
