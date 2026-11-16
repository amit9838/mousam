"""Stand-ins for GTK, requests and GSettings, so tests can import modules
that still mix pure logic with them (CORE_weatherData, API_Weather,
windowLocations).

The test machines have no display, no PyGObject, no requests and no installed
GSettings schema. Once the logic under test moves into GTK-free modules
(docs/architecture-plan.md, phase 2), its tests import those directly and
this file goes away. Tests of GTK-free modules must not use it.

Call install() before importing anything from the `mousam` package.
"""

import os
import sys
import types

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")


class _StubMeta(type):
    def __getattr__(cls, name):
        # Classes in a namespace (GObject.Object) and enum members
        # (Gtk.Orientation.VERTICAL): a fresh class, so it can be subclassed
        if name.startswith("__"):
            raise AttributeError(name)
        return type(name, (_Stub,), {})


class _Stub(metaclass=_StubMeta):
    """Accepts any call, attribute, subclass or decorator use."""

    def __init__(self, *args, **kwargs):
        pass

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return _Stub()

    def __call__(self, *args, **kwargs):
        # Used as a decorator (@GObject.Property(...)): keep the function
        if len(args) == 1 and callable(args[0]) and not kwargs:
            return args[0]
        return _Stub()


class _StubModule(types.ModuleType):
    """A module whose every name is a fresh stub class, so a class may
    subclass several of them (class X(Gtk.Box, Gtk.Orientable))."""

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        stub = type(name, (_Stub,), {})
        setattr(self, name, stub)
        return stub


class FakeSettings:
    """The few settings the tested code reads; tests change them freely."""

    def __init__(self):
        self.reset()

    def reset(self) -> None:
        self.unit = "metric"
        self.is_using_24h_clock = True
        self.added_cities = []
        self.selected_city = ""

    def connect(self, *_args):
        return 0


settings = FakeSettings()


def install() -> None:
    """Register the stubs and the `mousam` package (the source tree)."""
    gi = _StubModule("gi")
    gi.require_version = lambda *_args: None
    repository = _StubModule("gi.repository")
    gi.repository = repository
    sys.modules.setdefault("gi", gi)
    sys.modules.setdefault("gi.repository", repository)

    requests = _StubModule("requests")
    requests.exceptions = _StubModule("requests.exceptions")
    sys.modules.setdefault("requests", requests)
    sys.modules.setdefault("requests.exceptions", requests.exceptions)

    package = types.ModuleType("mousam")
    package.__path__ = [SRC]
    sys.modules.setdefault("mousam", package)

    settings_module = types.ModuleType("mousam.settings")
    settings_module.settings = settings
    sys.modules.setdefault("mousam.settings", settings_module)
