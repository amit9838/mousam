import threading
from threading import Lock
from gi.repository import GLib
from .CORE_Helpers import get_time_difference

_fetch_callbacks = []
_fetch_lock = Lock()

def fetch_all_weather_data_async(on_success=None, on_error=None):
    """
    Fetches all weather data in a thread-safe manner.
    """
    from .CORE_weatherData import weather_manager

    with _fetch_lock:
        if on_success:
            _fetch_callbacks.append(on_success)
        if any(t.name == "fetch_all_worker" for t in threading.enumerate()):
            return

    def _worker():
        from .CORE_Helpers import TIMEOUT
        
        # Reset ready state before starting fresh fetch
        weather_manager.clear()
        
        error_container = []

        def wrap_target(target, *args):
            try:
                target(*args)
            except Exception as e:
                error_container.append(e)

        try:
            cwd = threading.Thread(target=wrap_target, args=(weather_manager.update_current_weather,), name="cwt")
            cwd.start()
            cwd.join(timeout=TIMEOUT)
            
            if cwd.is_alive():
                raise TimeoutError("Current weather fetch timed out")
            
            if error_container:
                raise error_container[0]

            threads = [
                threading.Thread(target=wrap_target, args=(weather_manager.update_hourly_forecast,), name="hft"),
                threading.Thread(target=wrap_target, args=(weather_manager.update_daily_forecast,), name="dft"),
                threading.Thread(target=wrap_target, args=(weather_manager.update_air_pollution,), name="apt"),
                threading.Thread(target=wrap_target, args=(get_time_difference, "", True), name="local_time")
            ]
            
            for t in threads: t.start()
            
            # Join all with timeout
            for t in threads:
                t.join(timeout=TIMEOUT)
                if t.is_alive():
                    raise TimeoutError(f"{t.name} fetch timed out")
            
            if error_container:
                raise error_container[0]
            
            with _fetch_lock:
                callbacks = _fetch_callbacks[:]
                _fetch_callbacks.clear()
            
            for cb in callbacks:
                GLib.idle_add(cb)
                
        except Exception as e:
            print(f"Error fetching data: {e}")
            if on_error:
                GLib.idle_add(on_error, str(e))

    threading.Thread(target=_worker, name="fetch_all_worker", daemon=True).start()
