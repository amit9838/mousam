"""Wordings of the overview messages.

Each message has a key ("rain.start") and a few wordings that say the same
thing, so the overview does not read the same every time. Common messages
have 4-5 wordings, rare safety messages 2. A MessageBook picks one at random
and fills in the values.

The rules (CORE_OverviewRules.py) only use keys; what each rule means is in
docs/overview-rules.md. When adding or changing a wording:

- every wording of a key says the same thing, with the same placeholders
- follow "Writing messages" in docs/overview-rules.md (whole sentences,
  hedged times, no "a"/"an" before a number, under about 90 characters)
- plural wordings (counts) are functions of n, built with ngettext
- run ./update-pot
"""

import random
from gettext import gettext as _, ngettext
from typing import Callable, Dict, List, Union

# A wording: a template, or for counts a function of n returning one
Wording = Union[str, Callable[[int], str]]


def overview_messages() -> Dict[str, List[Wording]]:
    """Every message key and its wordings, translated with the language in use."""
    return {
        # ---------- Safety ----------
        "storm.now": [
            _("Thunderstorms are likely right now. Stay indoors if you can."),
            _("Expect thunderstorms right now. Stay indoors if you can."),
        ],
        "storm.later": [
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("Thunderstorms are likely around {time}. Plan to be indoors by then."),
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("Expect thunderstorms around {time}. Plan to be indoors by then."),
        ],
        "freezing.now": [
            _("Freezing rain is likely right now. Roads and paths may be icy."),
            _("Expect freezing rain right now. Watch for icy roads and paths."),
        ],
        "freezing.later": [
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("Freezing rain is likely around {time}. Roads and paths may turn icy."),
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("Expect freezing rain around {time}. Roads may turn icy."),
        ],
        "heavy_rain.now": [
            _("Heavy rain is likely right now. Expect puddles and slow roads."),
            _("Expect heavy rain right now. Allow extra travel time."),
        ],
        "heavy_rain.later": [
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("Heavy rain is likely around {time}. Keep an umbrella close."),
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("Expect heavy rain around {time}. Allow extra travel time."),
        ],
        "heavy_snow.now": [
            _("Heavy snow is likely right now. Travel may be slow."),
            _("Expect heavy snow right now. Allow extra travel time."),
        ],
        "heavy_snow.later": [
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("Heavy snow is likely around {time}. Travel may be slow after that."),
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("Expect heavy snow around {time}. Allow extra travel time."),
        ],
        "heat.now": [
            # Translators: {temp} is a temperature, like "14°"
            _("It feels like {temp} right now. Stay hydrated and seek shade."),
            # Translators: {temp} is a temperature, like "14°"
            _("It feels as hot as {temp} right now. Drink water and stay cool."),
        ],
        "heat.later": [
            # Translators: {temp} is a temperature, like "14°"; {time} is a rounded time of day, like "6:30 PM"
            _("It will feel like {temp} by around {time}. Stay hydrated and seek shade."),
            # Translators: {temp} is a temperature, like "14°"; {time} is a rounded time of day, like "6:30 PM"
            _("Expect it to feel like {temp} by around {time}. Drink water and stay cool."),
        ],
        "cold.now": [
            # Translators: {temp} is a temperature, like "14°"
            _("It feels like {temp} right now. Dress warmly, in layers."),
            # Translators: {temp} is a temperature, like "14°"
            _("It feels as cold as {temp} right now. Bundle up."),
        ],
        "cold.later": [
            # Translators: {temp} is a temperature, like "14°"; {time} is a rounded time of day, like "6:30 PM"
            _("It will feel like {temp} by around {time}. Dress warmly, in layers."),
            # Translators: {temp} is a temperature, like "14°"; {time} is a rounded time of day, like "6:30 PM"
            _("Expect it to feel like {temp} by around {time}. Bundle up."),
        ],
        "air.now": [
            _("Air quality is unhealthy right now. Limit time outdoors if you can."),
            _("The air is unhealthy right now. Consider staying indoors."),
        ],
        "air.later": [
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("Air quality turns unhealthy around {time}. Consider limiting time outdoors."),
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("Expect unhealthy air from around {time}. Limit time outdoors."),
        ],
        "uv.now": [
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("UV is very high until about {time}. Use sunscreen and cover up."),
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("The sun is very strong until about {time}. Use sunscreen and seek shade."),
        ],
        "uv.later": [
            # Translators: {start} and {end} are rounded times of day, like "11:00 AM" and "3:00 PM"
            _("UV will be very high from about {start} to {end}. Use sunscreen outdoors."),
            # Translators: {start} and {end} are rounded times of day, like "11:00 AM" and "3:00 PM"
            _("Expect very high UV from about {start} to {end}. Cover up outdoors."),
        ],
        # ---------- Rain and snow ----------
        "rain.start": [
            # Translators: {time} is a rounded time of day, like "6:30 PM"; {chance} is a percentage, like "70"
            _("Rain is likely to start around {time} with {chance}% chance."),
            # Translators: {time} is a rounded time of day, like "6:30 PM"; {chance} is a percentage, like "70"
            _("Expect rain from around {time}, with {chance}% chance."),
            # Translators: {time} is a rounded time of day, like "6:30 PM"; {chance} is a percentage, like "70"
            _("Rain may move in around {time} with {chance}% chance."),
            # Translators: {time} is a rounded time of day, like "6:30 PM"; {chance} is a percentage, like "70"
            _("Showers could begin around {time} with {chance}% chance. Keep an umbrella handy."),
            # Translators: {time} is a rounded time of day, like "6:30 PM"; {chance} is a percentage, like "70"
            _("There is {chance}% chance of rain starting around {time}."),
        ],
        "snow.start": [
            # Translators: {time} is a rounded time of day, like "6:30 PM"; {chance} is a percentage, like "70"
            _("Snow is likely to start around {time} with {chance}% chance."),
            # Translators: {time} is a rounded time of day, like "6:30 PM"; {chance} is a percentage, like "70"
            _("Expect snow from around {time}, with {chance}% chance."),
            # Translators: {time} is a rounded time of day, like "6:30 PM"; {chance} is a percentage, like "70"
            _("Snow may move in around {time} with {chance}% chance."),
            # Translators: {time} is a rounded time of day, like "6:30 PM"; {chance} is a percentage, like "70"
            _("Snowfall could begin around {time} with {chance}% chance. Dress warmly."),
        ],
        "rain.easing": [
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("Rain is likely right now, easing off around {time}."),
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("Rain should ease off around {time}."),
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("Expect rain for now, clearing around {time}."),
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("It is wet for now, but the rain should stop around {time}."),
        ],
        "snow.easing": [
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("Snow is likely right now, easing off around {time}."),
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("Snow should ease off around {time}."),
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("Expect snow for now, clearing around {time}."),
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("It is snowy for now, but it should stop around {time}."),
        ],
        "rain.through": [
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("Rain is likely to keep falling until about {time}."),
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("Expect rain on and off until about {time}."),
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("It looks wet until about {time}. Keep an umbrella close."),
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("Rain should stick around until about {time}."),
        ],
        "snow.through": [
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("Snow is likely to keep falling until about {time}."),
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("Expect snow on and off until about {time}."),
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("It looks snowy until about {time}. Travel may be slow."),
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("Snow should stick around until about {time}."),
        ],
        # ---------- Wind and fog ----------
        "wind.now": [
            # Translators: {speed} is a wind speed with its unit, like "45 km/h"
            _("Strong wind right now, around {speed}. Secure loose items outdoors."),
            # Translators: {speed} is a wind speed with its unit, like "45 km/h"
            _("It is windy right now, around {speed}. Hold on to your hat."),
            # Translators: {speed} is a wind speed with its unit, like "45 km/h"
            _("Wind is strong right now, around {speed}."),
            # Translators: {speed} is a wind speed with its unit, like "45 km/h"
            _("Expect strong wind for now, around {speed}. Secure loose items outdoors."),
        ],
        "wind.later": [
            # Translators: {speed} is a wind speed with its unit, like "45 km/h"; {time} is a rounded time of day, like "6:30 PM"
            _("Wind picks up to {speed} around {time}. Secure loose items outdoors."),
            # Translators: {speed} is a wind speed with its unit, like "45 km/h"; {time} is a rounded time of day, like "6:30 PM"
            _("Expect stronger wind, up to {speed}, around {time}."),
            # Translators: {speed} is a wind speed with its unit, like "45 km/h"; {time} is a rounded time of day, like "6:30 PM"
            _("It gets windy around {time}, up to {speed}."),
            # Translators: {speed} is a wind speed with its unit, like "45 km/h"; {time} is a rounded time of day, like "6:30 PM"
            _("Wind should strengthen to {speed} around {time}."),
        ],
        "fog.now": [
            _("It is foggy right now, with low visibility. Drive with care."),
            _("Fog is cutting visibility right now. Take it slow on the roads."),
            _("Visibility is low in the fog right now. Drive with care."),
        ],
        "fog.later": [
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("Fog is likely around {time}, with low visibility. Drive with care."),
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("Expect fog around {time}. Visibility may drop."),
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("Fog may roll in around {time}. Take care on the roads."),
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("Visibility could drop in fog around {time}."),
        ],
        "fog.sunrise": [
            _("Fog is likely around sunrise, with low visibility. Drive with care."),
            _("Expect fog around sunrise. Visibility may drop."),
            _("A foggy start is likely around sunrise. Take care on the roads."),
            _("Fog may form around sunrise, cutting visibility."),
        ],
        # ---------- Temperature ----------
        "temperature.warming": [
            # Translators: {temp} is a temperature, like "14°"; {time} is a rounded time of day, like "6:30 PM"
            _("Expect it to warm up to {temp} by around {time}."),
            # Translators: {temp} is a temperature, like "14°"; {time} is a rounded time of day, like "6:30 PM"
            _("Temperatures climb to {temp} by around {time}."),
            # Translators: {temp} is a temperature, like "14°"; {time} is a rounded time of day, like "6:30 PM"
            _("It should reach {temp} by around {time}."),
            # Translators: {temp} is a temperature, like "14°"; {time} is a rounded time of day, like "6:30 PM"
            _("Warming up to {temp} by around {time}."),
        ],
        "temperature.cooling": [
            # Translators: {temp} is a temperature, like "14°"; {time} is a rounded time of day, like "6:30 PM"
            _("Expect it to cool down to {temp} by around {time}. Keep a layer handy."),
            # Translators: {temp} is a temperature, like "14°"; {time} is a rounded time of day, like "6:30 PM"
            _("Temperatures drop to {temp} by around {time}."),
            # Translators: {temp} is a temperature, like "14°"; {time} is a rounded time of day, like "6:30 PM"
            _("It should cool to {temp} by around {time}. A jacket may help."),
            # Translators: {temp} is a temperature, like "14°"; {time} is a rounded time of day, like "6:30 PM"
            _("Cooling down to {temp} by around {time}."),
        ],
        # ---------- Tomorrow ----------
        "tomorrow.rain": [
            # Translators: {chance} is a percentage, like "70"
            _("Rain is likely tomorrow with {chance}% chance, so plan ahead."),
            # Translators: {chance} is a percentage, like "70"
            _("Tomorrow looks wet, with {chance}% chance of rain."),
            # Translators: {chance} is a percentage, like "70"
            _("Expect rain tomorrow, with {chance}% chance. Keep an umbrella ready."),
            # Translators: {chance} is a percentage, like "70"
            _("There is {chance}% chance of rain tomorrow."),
        ],
        "tomorrow.warmer": [
            # Translators: {temp} is a temperature, like "14°"
            _("Tomorrow will be warmer than today, with a high of {temp}."),
            # Translators: {temp} is a temperature, like "14°"
            _("A warmer day tomorrow, reaching {temp}."),
            # Translators: {temp} is a temperature, like "14°"
            _("Tomorrow heats up, with a high of {temp}."),
            # Translators: {temp} is a temperature, like "14°"
            _("Expect a warmer tomorrow, up to {temp}."),
        ],
        "tomorrow.cooler": [
            # Translators: {temp} is a temperature, like "14°"
            _("Tomorrow will be cooler than today, with a high of {temp}."),
            # Translators: {temp} is a temperature, like "14°"
            _("A cooler day tomorrow, reaching only {temp}."),
            # Translators: {temp} is a temperature, like "14°"
            _("Tomorrow cools off, with a high of {temp}."),
            # Translators: {temp} is a temperature, like "14°"
            _("Expect a cooler tomorrow, topping out at {temp}."),
        ],
        # ---------- Sunset and sunrise ----------
        "sunset.minutes": [
            # Translators: {n} is a number of minutes
            lambda n: ngettext(
                "The sun sets in about {n} minute.",
                "The sun sets in about {n} minutes.",
                n,
            ),
            # Translators: {n} is a number of minutes
            lambda n: ngettext(
                "Sunset is about {n} minute away.",
                "Sunset is about {n} minutes away.",
                n,
            ),
            # Translators: {n} is a number of minutes
            lambda n: ngettext(
                "About {n} minute of daylight left.",
                "About {n} minutes of daylight left.",
                n,
            ),
            # Translators: {n} is a number of minutes
            lambda n: ngettext(
                "The sun goes down in about {n} minute.",
                "The sun goes down in about {n} minutes.",
                n,
            ),
        ],
        "sunrise.minutes": [
            # Translators: {n} is a number of minutes
            lambda n: ngettext(
                "The sun rises in about {n} minute.",
                "The sun rises in about {n} minutes.",
                n,
            ),
            # Translators: {n} is a number of minutes
            lambda n: ngettext(
                "Sunrise is about {n} minute away.",
                "Sunrise is about {n} minutes away.",
                n,
            ),
            # Translators: {n} is a number of minutes
            lambda n: ngettext(
                "Daylight returns in about {n} minute.",
                "Daylight returns in about {n} minutes.",
                n,
            ),
            # Translators: {n} is a number of minutes
            lambda n: ngettext(
                "The sun comes up in about {n} minute.",
                "The sun comes up in about {n} minutes.",
                n,
            ),
        ],
        "sunset.hours": [
            # Translators: {n} is a number of hours; {time} the exact time of day, like "6:12 PM"
            lambda n: ngettext(
                "The sun sets in about {n} hour, at {time}.",
                "The sun sets in about {n} hours, at {time}.",
                n,
            ),
            # Translators: {n} is a number of hours; {time} the exact time of day, like "6:12 PM"
            lambda n: ngettext(
                "Sunset is about {n} hour away, at {time}.",
                "Sunset is about {n} hours away, at {time}.",
                n,
            ),
            # Translators: {n} is a number of hours; {time} the exact time of day, like "6:12 PM"
            lambda n: ngettext(
                "About {n} hour of daylight left. Sunset is at {time}.",
                "About {n} hours of daylight left. Sunset is at {time}.",
                n,
            ),
            # Translators: {n} is a number of hours; {time} the exact time of day, like "6:12 PM"
            lambda n: ngettext(
                "The sun goes down at {time}, in about {n} hour.",
                "The sun goes down at {time}, in about {n} hours.",
                n,
            ),
        ],
        "sunrise.hours": [
            # Translators: {n} is a number of hours; {time} the exact time of day, like "6:12 PM"
            lambda n: ngettext(
                "The sun rises in about {n} hour, at {time}.",
                "The sun rises in about {n} hours, at {time}.",
                n,
            ),
            # Translators: {n} is a number of hours; {time} the exact time of day, like "6:12 PM"
            lambda n: ngettext(
                "Sunrise is about {n} hour away, at {time}.",
                "Sunrise is about {n} hours away, at {time}.",
                n,
            ),
            # Translators: {n} is a number of hours; {time} the exact time of day, like "6:12 PM"
            lambda n: ngettext(
                "Daylight returns at {time}, in about {n} hour.",
                "Daylight returns at {time}, in about {n} hours.",
                n,
            ),
            # Translators: {n} is a number of hours; {time} the exact time of day, like "6:12 PM"
            lambda n: ngettext(
                "The sun comes up at {time}, in about {n} hour.",
                "The sun comes up at {time}, in about {n} hours.",
                n,
            ),
        ],
        # ---------- Calm ----------
        "calm": [
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("Conditions should stay steady until about {time}."),
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("No big changes expected until about {time}."),
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("A quiet spell ahead, with little change until about {time}."),
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("Things look settled until about {time}."),
            # Translators: {time} is a rounded time of day, like "6:30 PM"
            _("The weather should hold steady until about {time}."),
        ],
    }


class MessageBook:
    """Picks a wording for a message key and fills in its values.

    The choice depends on `seed` and the key only, so the same seed always
    gives the same wordings: the engine keeps a seed between announcements
    (the text stays put while it is updated) and draws a new one each time
    the overview is announced (the wording changes).
    """

    def __init__(self, seed: int = 0, messages: Dict[str, List[Wording]] = None):
        self.seed = seed
        self.messages = messages if messages is not None else overview_messages()

    def _wording(self, key: str) -> Wording:
        return random.Random(f"{self.seed}:{key}").choice(self.messages[key])

    def say(self, key: str, **values) -> str:
        """A message, with its placeholders filled in."""
        return self._wording(key).format(**values)

    def say_count(self, key: str, n: int, **values) -> str:
        """A message about a count ({n}), in the right plural form."""
        return self._wording(key)(n).format(n=n, **values)
