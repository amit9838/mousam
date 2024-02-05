application_id = 'io.github.amit9838.mousam'

scalable_dir = join_paths('hicolor', 'scalable', 'apps')

install_data(
  join_paths(scalable_dir, ('@0@.svg').format(application_id)),
  install_dir: join_paths(get_option('datadir'), 'icons', scalable_dir),
)

scalable_dir = join_paths('hicolor','scalable', 'mousam_icons')

fs = import('fs')
source_svgs = []
source_svgs += files(
  run_command(
    'find',
    meson.current_source_dir() / scalable_dir,
    '-name', '*.svg',
    check: true
  ).stdout().strip().split('\n')
)

foreach i : range(source_svgs.length())
  svg = source_svgs[i]
  install_data(
    join_paths(scalable_dir, fs.name(svg)),
	  install_dir: join_paths(get_option('datadir'), 'icons', scalable_dir)
  )
endforeach

symbolic_dir = join_paths('hicolor', 'symbolic', 'apps')
install_data(
  join_paths(symbolic_dir, ('@0@-symbolic.svg').format(application_id)),
  install_dir: join_paths(get_option('datadir'), 'icons', symbolic_dir)
)
