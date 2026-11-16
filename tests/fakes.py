"""Test doubles for the network: a fake `requests` for the API modules and a
fake forecast client for code that fetches through one.

Neither touches the network, so tests stay fast and give the same answer
every time.
"""

import types


class FakeResponse:
    def __init__(self, payload=None, status=200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise FakeRequests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


class FakeRequests(types.ModuleType):
    """Stands in for the `requests` module: records each get() and answers
    with `response`, or raises `error`."""

    class RequestException(Exception):
        pass

    class HTTPError(RequestException):
        pass

    class ConnectionError(RequestException):
        pass

    class Timeout(RequestException):
        pass

    def __init__(self):
        super().__init__("requests")
        self.exceptions = self
        self.reset()

    def reset(self):
        self.calls = []
        self.response = FakeResponse({})
        self.error = None

    def get(self, url, params=None, timeout=None):
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        if self.error is not None:
            raise self.error
        return self.response


class FakeForecastClient:
    """A ForecastClient (src/CORE_ForecastClient.py) that answers from
    `responses` (by function name) and records each call. A missing answer
    is None, as from a failed request."""

    def __init__(self, **responses):
        self.responses = responses
        self.calls = []

    def _answer(self, name, *args):
        self.calls.append((name, *args))
        return self.responses.get(name)

    def fetch_current(self, latitude, longitude, unit):
        return self._answer("fetch_current", latitude, longitude, unit)

    def fetch_hourly(self, latitude, longitude, unit):
        return self._answer("fetch_hourly", latitude, longitude, unit)

    def fetch_daily(self, latitude, longitude, unit):
        return self._answer("fetch_daily", latitude, longitude, unit)

    def fetch_many(self, coords, unit):
        return self._answer("fetch_many", coords, unit)
