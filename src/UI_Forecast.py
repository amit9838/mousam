"""
Forecast module for mousam.

Provides a GTK widget that displays weather forecasts in two modes:
- Tomorrow: Hourly forecast for the next 24 hours starting from midnight.
- Weekly: Daily forecast for the next 7 days.
"""

from datetime import datetime, timedelta
from enum import Enum, auto
from gettext import gettext as _
from typing import Any, Dict, List, Optional, Union

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk

from .constants import icons
from .config import settings
from .CORE_weatherData import fetch_hourly_forecast, fetch_daily_forecast



class ForecastPage(Enum):
    """Enum representing the available forecast pages."""
    TOMORROW = auto()
    WEEKLY = auto()


class Forecast(Gtk.Grid):
    """
    A custom Gtk.Grid widget that shows tomorrow's or weekly weather forecast.

    The widget contains a toggle button bar to switch between "Tomorrow"
    (hourly) and "Weekly" (daily) views. Forecast data is fetched lazily
    from the CORE_weatherData modules when a view is first activated.

    Attributes:
        ITEM_WIDTH_REQUEST (int): Width request for toggle buttons.
        ITEM_HEIGHT_REQUEST (int): Height request for toggle buttons.
        SCROLLED_WINDOW_WIDTH (int): Width of the scrolled window.
        SCROLLED_WINDOW_HEIGHT (int): Height of the scrolled window.
        ICON_SIZE (int): Pixel size for weather icons.
        FORECAST_ITEM_MARGIN (int): Margin between forecast items.
        LABEL_BOX_WIDTH (int): Width of the time/date label container.
        LABEL_BOX_HEIGHT (int): Height of the time/date label container.
        DAILY_ITEMS (int): Number of daily forecast items to display.
        HOURLY_ITEMS (int): Number of hourly forecast items to display.
    """

    # UI sizing constants
    ITEM_WIDTH_REQUEST: int = 120
    ITEM_HEIGHT_REQUEST: int = 16
    SCROLLED_WINDOW_WIDTH: int = 220
    SCROLLED_WINDOW_HEIGHT: int = 480
    ICON_SIZE: int = 50
    FORECAST_ITEM_MARGIN: int = 6
    LABEL_BOX_WIDTH: int = 80
    LABEL_BOX_HEIGHT: int = 60

    # Data range constants
    DAILY_ITEMS: int = 7
    HOURLY_ITEMS: int = 24

    # Page name to enum mapping
    _PAGE_NAME_MAP: Dict[str, ForecastPage] = {
        "tomorrow": ForecastPage.TOMORROW,
        "weekly": ForecastPage.WEEKLY,
    }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the Forecast widget.

        Sets margins, applies CSS classes, and builds the UI.
        """
        super().__init__(*args, **kwargs)

        self._setup_styling()
        self._build_ui()

    def _setup_styling(self) -> None:
        """Apply margins and CSS classes to the widget."""
        self.set_margin_top(10)
        self.set_margin_bottom(5)
        self.set_margin_start(6)
        self.set_margin_end(3)

        self.set_css_classes(["view", "card", "custom_card"])
        if settings.is_using_dynamic_bg:
            self.add_css_class("transparent_5")

    def _build_ui(self) -> None:
        """
        Construct the main UI elements.

        Creates:
        - A toggle button bar (Tomorrow / Weekly)
        - A Gtk.Stack that holds the forecast pages
        """
        # Top bar container
        top_bar = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            hexpand=True,
            halign=Gtk.Align.CENTER,
        )
        self.attach(top_bar, 0, 0, 1, 1)

        # Button bar (linked buttons)
        button_bar = self._create_button_bar()
        top_bar.append(button_bar)

        # Stack for forecast pages
        self._forecast_stack = Gtk.Stack.new()
        self._forecast_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.attach(self._forecast_stack, 0, 1, 1, 1)

        # Load initial page (Tomorrow)
        self._load_page(ForecastPage.TOMORROW)

    def _create_button_bar(self) -> Gtk.Box:
        """
        Create and return the toggle button bar.

        Returns:
            Gtk.Box: A horizontally oriented box containing the toggle buttons.
        """
        button_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_bar.add_css_class("linked")
        button_bar.set_margin_start(2)
        button_bar.set_valign(Gtk.Align.CENTER)

        # Tomorrow button
        tomorrow_btn = Gtk.ToggleButton.new_with_label(_("Tomorrow"))
        tomorrow_btn.set_size_request(self.ITEM_WIDTH_REQUEST, self.ITEM_HEIGHT_REQUEST)
        tomorrow_btn.set_css_classes(["btn_sm"])
        tomorrow_btn.set_active(True)
        tomorrow_btn.connect("clicked", self._on_tomorrow_clicked)
        button_bar.append(tomorrow_btn)

        # Weekly button (grouped with tomorrow)
        weekly_btn = Gtk.ToggleButton.new_with_label(_("Weekly"))
        weekly_btn.set_size_request(self.ITEM_WIDTH_REQUEST, self.ITEM_HEIGHT_REQUEST)
        weekly_btn.set_css_classes(["btn_sm"])
        weekly_btn.set_group(tomorrow_btn)
        weekly_btn.connect("clicked", self._on_weekly_clicked)
        button_bar.append(weekly_btn)

        return button_bar

    def _on_tomorrow_clicked(self, _widget: Gtk.ToggleButton) -> None:
        """Handle click on Tomorrow button."""
        self._switch_to_page(ForecastPage.TOMORROW)

    def _on_weekly_clicked(self, _widget: Gtk.ToggleButton) -> None:
        """Handle click on Weekly button."""
        self._switch_to_page(ForecastPage.WEEKLY)

    def _switch_to_page(self, page: ForecastPage) -> None:
        """
        Switch to the specified forecast page, loading it if necessary.

        Args:
            page: The ForecastPage enum value to switch to.
        """
        page_name = page.name.lower()
        if self._forecast_stack.get_child_by_name(page_name):
            self._forecast_stack.set_visible_child_name(page_name)
        else:
            self._load_page(page)

    def _load_page(self, page: ForecastPage) -> None:
        """
        Load (or reload) a forecast page and add it to the stack.

        Args:
            page: The ForecastPage enum value to load.
        """
        # Import data modules lazily to avoid circular imports
        daily_forecast_data = fetch_daily_forecast()
        hourly_forecast_data = fetch_hourly_forecast()

        page_name = page.name.lower()
        container = Gtk.Box(margin_top=0, margin_bottom=0)
        self._forecast_stack.add_named(container, page_name)
        self._forecast_stack.set_visible_child_name(page_name)

        # Scrolled window for vertical scrolling
        scrolled = Gtk.ScrolledWindow(margin_top=4, margin_bottom=4)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(self.SCROLLED_WINDOW_WIDTH, self.SCROLLED_WINDOW_HEIGHT)
        scrolled.set_kinetic_scrolling(True)
        container.append(scrolled)

        # Container for forecast items
        items_container = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            margin_top=0,
            margin_bottom=0,
        )
        scrolled.set_child(items_container)

        # Determine data source and range
        if page == ForecastPage.WEEKLY:
            data_source = daily_forecast_data
            count = self.DAILY_ITEMS
            offset = 0
        else:  # TOMORROW
            data_source = hourly_forecast_data
            count = self.HOURLY_ITEMS
            offset = self._get_hourly_offset(hourly_forecast_data)

        # Build forecast items
        for idx in range(count):
            item_widget = self._create_forecast_item(
                page=page,
                data_source=data_source,
                index=idx + offset,
                hourly_data=hourly_forecast_data,  # needed for night/day detection
            )
            items_container.append(item_widget)

    def _create_forecast_item(
        self,
        page: ForecastPage,
        data_source: Any,
        index: int,
        hourly_data: Any,
    ) -> Gtk.Grid:
        """
        Create a single forecast item widget.

        Args:
            page: The page type (determines data fields to use).
            data_source: The data object (daily or hourly forecast).
            index: The index into the data arrays.
            hourly_data: Hourly forecast data (used for is_day flag).

        Returns:
            Gtk.Grid: A grid widget containing the forecast item.
        """
        grid = Gtk.Grid(hexpand=True, margin_top=self.FORECAST_ITEM_MARGIN)
        grid.set_css_classes(["bg_light_grey", "custom_card_forecast_item"])

        # Extract common data
        timestamp = data_source.time.get("data")[index]
        dt = datetime.fromtimestamp(timestamp)

        # Prepare label and temperatures
        if page == ForecastPage.WEEKLY:
            label_text = self._format_weekly_label(dt)
            temp_max = data_source.temperature_2m_max.get("data")[index]
            temp_min = data_source.temperature_2m_min.get("data")[index]
            weather_code = data_source.weathercode.get("data")[index]
        else:  # TOMORROW
            label_text = self._format_hourly_label(dt)
            temp_max = data_source.temperature_2m.get("data")[index]
            temp_min = None  # No min temp for hourly
            weather_code = data_source.weathercode.get("data")[index]
            # Adjust for night if needed
            if hourly_data.is_day.get("data")[index] == 0:
                weather_code = f"{weather_code}n"

        # Build the grid columns
        self._add_label_column(grid, label_text)
        self._add_icon_column(grid, weather_code)
        self._add_placeholder_column(grid)
        self._add_temperature_column(grid, temp_max, temp_min)

        return grid

    def _format_hourly_label(self, dt: datetime) -> str:
        """Format datetime for hourly forecast (time only)."""
        if settings.is_using_24h_clock:
            return dt.strftime("%H:%M")
        return dt.strftime("%I:%M %p")

    def _format_weekly_label(self, dt: datetime) -> str:
        """Format datetime for weekly forecast (day name, with Today/Tomorrow)."""
        today = datetime.today().date()
        tomorrow = (datetime.today() + timedelta(days=1)).date()
        if dt.date() == today:
            return _("Today")
        if dt.date() == tomorrow:
            return _("Tomorrow")
        return dt.strftime("%A")

    def _add_label_column(self, grid: Gtk.Grid, text: str) -> None:
        """Add the time/date label column (col 0)."""
        box = Gtk.Box()
        box.set_size_request(self.LABEL_BOX_WIDTH, self.LABEL_BOX_HEIGHT)
        label = Gtk.Label(label=text, halign=Gtk.Align.START)
        label.set_css_classes(["text-5", "bold-4", "light-2"])
        box.append(label)
        grid.attach(box, 0, 0, 1, 1)

    def _add_icon_column(self, grid: Gtk.Grid, weather_code: Union[int, str]) -> None:
        """Add the weather icon column (col 1)."""
        icon_path = icons.get(str(weather_code))
        if not icon_path:
            # Fallback to unknown icon if not found
            icon_path = icons.get("unknown", "")

        image = Gtk.Image.new_from_file(icon_path)
        image.set_halign(Gtk.Align.END)
        image.set_hexpand(True)
        image.set_pixel_size(self.ICON_SIZE)
        grid.attach(image, 1, 0, 1, 1)

    def _add_placeholder_column(self, grid: Gtk.Grid) -> None:
        """Add an empty placeholder column (col 2) for layout balance."""
        placeholder = Gtk.Grid(valign=Gtk.Align.CENTER, margin_end=20)
        grid.attach(placeholder, 2, 0, 1, 1)

    def _add_temperature_column(
        self,
        grid: Gtk.Grid,
        temp_max: float,
        temp_min: Optional[float],
    ) -> None:
        """Add the temperature column (col 3)."""
        temp_grid = Gtk.Grid(valign=Gtk.Align.CENTER)
        grid.attach(temp_grid, 2, 0, 1, 1)

        # Max temperature
        max_label = Gtk.Label(label=f"{temp_max:.0f}° ", margin_start=4)
        max_label.set_css_classes(["text-4", "bold-2"])
        temp_grid.attach(max_label, 1, 0, 1, 1)

        # Min temperature (if provided)
        if temp_min is not None:
            min_label = Gtk.Label(label=f" {temp_min:.0f}°", margin_top=5)
            min_label.set_css_classes(["light-5"])
            temp_grid.attach(min_label, 1, 1, 1, 1)

    @staticmethod
    def _get_next_midnight_timestamp() -> float:
        """
        Return the Unix timestamp of the next midnight (00:00).

        Returns:
            float: Timestamp of the upcoming midnight.
        """
        now = datetime.now()
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if now >= midnight:
            midnight += timedelta(days=1)
        return midnight.timestamp()

    def _get_hourly_offset(self, hourly_data: Any) -> int:
        """
        Determine the starting index for the hourly forecast to begin at midnight.

        Args:
            hourly_data: The hourly forecast data object.

        Returns:
            int: Index offset into the time array.
        """
        target_ts = self._get_next_midnight_timestamp()
        time_series: List[float] = hourly_data.time.get("data")
        for idx, ts in enumerate(time_series):
            if ts > target_ts:
                return idx
        # Fallback (should not happen with proper data)
        return 0