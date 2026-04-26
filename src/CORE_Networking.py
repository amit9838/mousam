import threading
from threading import Lock
from gi.repository import GLib
from .CORE_Helpers import get_time_difference
from .CORE_Logging import get_logger

logger = get_logger("networking")

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
        logger.info("Starting background fetch for all weather data")
        
        # Reset ready state before starting fresh fetch
        weather_manager.clear()
        
        error_container = []

        def wrap_target(target, *args):
            try:
                logger.debug(f"Starting target: {target.__name__}")
                target(*args)
                logger.debug(f"Finished target: {target.__name__}")
            except Exception as e:
                logger.error(f"Error in target {target.__name__}: {e}")
                error_container.append(e)

        try:
            cwd = threading.Thread(target=wrap_target, args=(weather_manager.update_current_weather,), name="cwt")
            cwd.start()
            cwd.join(timeout=TIMEOUT)
            
            if cwd.is_alive():
                raise TimeoutError("Current weather fetch timed out")
            
            if error_container:
                raise error_container[0]

            logger.info("Current weather fetched successfully, starting forecasts and air pollution")
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
            
            logger.info("All background fetch targets completed successfully")
            with _fetch_lock:
                callbacks = _fetch_callbacks[:]
                _fetch_callbacks.clear()
            
            for cb in callbacks:
                GLib.idle_add(cb)
                
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            if on_error:
                GLib.idle_add(on_error, str(e))

    threading.Thread(target=_worker, name="fetch_all_worker", daemon=True).start()
