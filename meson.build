project('weather',
          version: '1.0.1',
    meson_version: '>= 0.61.0',
  default_options: [ 'warning_level=2', 'werror=false', ],
)

i18n = import('i18n')
gnome = import('gnome')



subdir('data')
subdir('src')
subdir('po')



install_subdir('data/weather_icons', install_dir: get_option('datadir') / 'icons/hicolor/scalable')

gnome.post_install(
     glib_compile_schemas: true,
    gtk_update_icon_cache: true,
  update_desktop_database: true,
)
