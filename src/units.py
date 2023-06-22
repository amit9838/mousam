from gi.repository import Gio,GLib

def get_measurement_type():
        settings = Gio.Settings.new("io.github.amit9838.weather")
        return str(settings.get_value("measure-type"))[1:-1]
    
measurement_type = get_measurement_type()

# Units and measurements
measurements = {
        "metric":{"temp_unit":"°C",
                  "speed_unit":'km/h',"speed_mul":3.6,   # convert speed from m/s to km/h
                  "dist_unit":'km',"dist_mul":0.001
                },   
        # "standard":{"temp_unit":"K","speed_unit":'km/h',"speed_mul":3.6},  # convert speed from m/s to km/h
        "imperial":{"temp_unit":"°F",
                    "speed_unit":'mph',"speed_mul":1,  #speed miles/hr 
                    "dist_unit":'miles',"dist_mul":0.0006213712,
                }

}


