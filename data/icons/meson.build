application_id = 'io.github.amit9838.mousam'

scalable_dir = join_paths('hicolor', 'scalable', 'apps')

install_data(
  join_paths(scalable_dir, ('@0@.svg').format(application_id)),
  install_dir: join_paths(get_option('datadir'), 'icons', scalable_dir),
)

fs = import('fs')

# --- Default icons installed as default_icons ---
default_icons_source_dir = join_paths('hicolor', 'scalable', 'default_icons')
default_icons_install_dir = join_paths('hicolor', 'scalable', 'default_icons')

default_svgs = []
default_svgs += files(
  run_command(
    'find',
    meson.current_source_dir() / default_icons_source_dir,
    '-name', '*.svg',
    check: true
  ).stdout().strip().split('\n')
)

foreach i : range(default_svgs.length())
  svg = default_svgs[i]
  install_data(
    join_paths(default_icons_source_dir, fs.name(svg)),
    install_dir: join_paths(get_option('datadir'), 'icons', default_icons_install_dir)
  )
endforeach

# --- Material icons installed as material_icons ---
material_icons_source_dir = join_paths('hicolor', 'scalable', 'material_icons')
material_icons_install_dir = join_paths('hicolor', 'scalable', 'material_icons')

material_svgs = []
material_svgs += files(
  run_command(
    'find',
    meson.current_source_dir() / material_icons_source_dir,
    '-name', '*.svg',
    check: true
  ).stdout().strip().split('\n')
)

foreach i : range(material_svgs.length())
  svg = material_svgs[i]
  install_data(
    join_paths(material_icons_source_dir, fs.name(svg)),
    install_dir: join_paths(get_option('datadir'), 'icons', material_icons_install_dir)
  )
endforeach

symbolic_dir = join_paths('hicolor', 'symbolic', 'apps')
install_data(
  join_paths(symbolic_dir, ('@0@-symbolic.svg').format(application_id)),
  install_dir: join_paths(get_option('datadir'), 'icons', symbolic_dir)
)