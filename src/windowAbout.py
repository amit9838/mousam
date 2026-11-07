import os
import platform
from gettext import gettext as _

import gi

from .configs import (
    APPDATA_RESOURCE,
    BUY_ME_A_COFFEE_URL,
    CC_BY_4_0_URL,
    CONTRIBUTORS_URL,
    GOOGLE_WEATHER_ICONS_URL,
    METEOCONS_URL,
    OPEN_METEO_URL,
    SOURCE_CODE_URL,
    TRANSLATE_URL,
    VERSION,
)
from .settings import settings

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Adw, GLib, Gtk  # noqa: E402


def show_about_window(parent_window: Gtk.Widget | None = None) -> None:
    """Present the app's about dialog over parent_window."""
    # Name, icon, developer, website, issue link, licence and the release
    # notes for this version come from the appdata bundled in the GResource.
    about = Adw.AboutDialog.new_from_appdata(APPDATA_RESOURCE, VERSION)
    # The version of this build, not the latest release listed in the appdata
    about.set_version(VERSION)
    about.set_comments(_("Weather at a glance"))
    about.set_developers(["Amit Chaudhary https://github.com/amit9838"])
    about.set_copyright(_("Copyright © 2023–2026 Mousam Developers"))
    # Translators: replace with your name (and email or link), one per line
    about.set_translator_credits(_("translator-credits"))
    about.set_debug_info(build_debug_info())
    about.set_debug_info_filename("mousam-debug-info.txt")

    about.add_link(_("Source Code"), SOURCE_CODE_URL)
    about.add_link(_("Contributors"), CONTRIBUTORS_URL)
    about.add_link(_("Help Translate"), TRANSLATE_URL)
    about.add_link(_("Buy Me a Coffee"), BUY_ME_A_COFFEE_URL)

    about.add_acknowledgement_section(
        _("Weather Data"), [f"Open-Meteo {OPEN_METEO_URL}"]
    )
    about.add_acknowledgement_section(
        _("Weather Icons"),
        [
            f"Bas Milius (Meteocons) {METEOCONS_URL}",
            f"Darren Griffin (Google Weather Icons) {GOOGLE_WEATHER_ICONS_URL}",
        ],
    )

    about.add_legal_section(
        _("Weather Data"),
        "© Open-Meteo.com",
        Gtk.License.CUSTOM,
        # Translators: {open_meteo} and {license} are links, keep the tags as they are
        _("Weather data by {open_meteo}, licensed under {license}.").format(
            open_meteo=f'<a href="{OPEN_METEO_URL}">Open-Meteo.com</a>',
            license=f'<a href="{CC_BY_4_0_URL}">CC BY 4.0</a>',
        ),
    )
    about.add_legal_section(
        _("Default Weather Icons"),
        "© Bas Milius",
        Gtk.License.MIT_X11,
        None,
    )
    about.add_legal_section(
        _("Material Weather Icons"),
        "© Google",
        Gtk.License.CUSTOM,
        _("All rights belong to Google. Collected by Darren Griffin."),
    )

    about.present(parent_window)


def build_debug_info() -> str:
    """Versions and settings for bug reports, shown on the Troubleshooting page.

    Left untranslated so maintainers can read it. Never add locations,
    coordinates or anything else about the user.
    """
    if os.path.exists("/.flatpak-info"):
        packaging = "Flatpak"
    elif "SNAP" in os.environ:
        packaging = "Snap"
    else:
        packaging = "Native"

    lines = [
        f"Mousam {VERSION} ({packaging})",
        f"OS: {_host_os_name()}",
        f"Desktop: {os.environ.get('XDG_CURRENT_DESKTOP', 'Unknown')}",
        f"Python: {platform.python_version()}",
        f"PyGObject: {gi.__version__}",
        f"GTK: {Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}",
        f"libadwaita: {Adw.get_major_version()}.{Adw.get_minor_version()}.{Adw.get_micro_version()}",
        "",
        "Settings:",
        f"  Units: {settings.unit}",
        f"  Precipitation in inches: {settings.is_using_inch_for_prec}",
        f"  24-hour clock: {settings.is_using_24h_clock}",
        f"  Auto refresh: {settings.auto_refresh_interval} min",
        f"  Dynamic background: {settings.is_using_dynamic_bg}",
        f"  Icon theme: {settings.icon_theme}",
        f"  Weather overview: {settings.show_overview}",
        f"  Notifications: {settings.show_notifications}",
        f"  Debug mode: {settings.debug_mode}",
        f"  Saved locations: {len(settings.added_cities)}",
    ]
    return "\n".join(lines)


def _host_os_name() -> str:
    """The host's OS name; inside the Flatpak sandbox /etc is the runtime's."""
    try:
        with open("/run/host/os-release", encoding="utf-8") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    return line.split("=", 1)[1].strip().strip('"')
    except OSError:
        pass
    return GLib.get_os_info("PRETTY_NAME") or "Unknown"
