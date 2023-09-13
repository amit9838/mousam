application_id = 'io.github.amit9838.weather'

scalable_dir = join_paths('hicolor', 'scalable', 'apps')

install_data(
  join_paths(scalable_dir, ('@0@.svg').format(application_id)),
  install_dir: join_paths(get_option('datadir'), 'icons', scalable_dir),
)
scalable_dir2 = join_paths('hicolor','scalable', 'weather_icons')

install_data(
	join_paths(scalable_dir2, 'clear-day.svg'),
	join_paths(scalable_dir2, 'partly-cloudy-day.svg'),
	join_paths(scalable_dir2, 'cloudy.svg'),
	join_paths(scalable_dir2, 'partly-cloudy-day-rain.svg'),
	join_paths(scalable_dir2, 'thunderstorms-day-rain.svg'),
	join_paths(scalable_dir2, 'fog.svg'),
	join_paths(scalable_dir2, 'snowflake.svg'),
	join_paths(scalable_dir2, 'clear-night.svg'),
	join_paths(scalable_dir2, 'partly-cloudy-night.svg'),
	join_paths(scalable_dir2, 'partly-cloudy-night-rain.svg'),
	join_paths(scalable_dir2, 'thunderstorms-night-rain.svg'),

	install_dir: join_paths(get_option('datadir'), 'icons', scalable_dir2),

)

symbolic_dir = join_paths('hicolor', 'symbolic', 'apps')
install_data(
  join_paths(symbolic_dir, ('@0@-symbolic.svg').format(application_id)),
  install_dir: join_paths(get_option('datadir'), 'icons', symbolic_dir)
)
