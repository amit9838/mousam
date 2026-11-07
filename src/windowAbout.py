from gettext import gettext as _

import gi

from .configs import (
    BUY_ME_A_COFFEE_URL,
    CC_BY_4_0_URL,
    CONTRIBUTORS_URL,
    GOOGLE_WEATHER_ICONS_URL,
    ISSUE_URL,
    METEOCONS_URL,
    OPEN_METEO_URL,
    SOURCE_CODE_URL,
    VERSION,
    WEBSITE_URL,
)

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw  # noqa: E402


def show_about_window(parent_window: Gtk.Widget | None = None) -> None:
    """Present the app's about dialog over parent_window."""
    about = Adw.AboutDialog(
        application_name="Mousam",
        application_icon="io.github.amit9838.mousam",
        version=VERSION,
        comments=_("Weather at a glance"),
        developer_name="Amit Chaudhary",
        developers=["Amit Chaudhary https://github.com/amit9838"],
        copyright=_("Copyright © 2023–2026 Mousam Developers"),
        license_type=Gtk.License.GPL_3_0,
        website=WEBSITE_URL,
        issue_url=ISSUE_URL,
        translator_credits=_("translator-credits"),
    )
    about.add_link(_("Source Code"), SOURCE_CODE_URL)
    about.add_link(_("Contributors"), CONTRIBUTORS_URL)
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
