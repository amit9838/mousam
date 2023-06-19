css = """
.condition_label {
        font-size: 20px;
        font-weight: bold;
        opacity:.8;
    }
.temp_label {
        font-size: 48px;
        font-weight: bold;
    }
.f_box {
        background-color:rgba(255, 255, 255, 0.08);
        border-radius: 5px;
        border : 1px solid rgba(150, 150, 150,.2);

    }
.forecast_box {
        border-radius: 5px;
    }


.forecast_temp_label {
        font-size: 18px;
        font-weight: bold;
    }

.city_label {
    font-size: 18px;
    font-weight: bold;
}

.bold{
    font-weight:500;
}

.bolder{
    font-weight:500;
}

.secondary{
    opacity:.6;
}

.secondary-light{
    opacity:.85;
}

.secondary-lighter{
    opacity:.95;
}

.error_label {
    font-size: 26px;
    font-weight: bold;
}


.updated_at{
    font-size:.9rem;
    opacity:.6;
}

.grey_bg {
        background-color:rgba(100, 100, 100, 0.1);
    }


.main_window{
    border-radius:15px;
    border : 1px solid rgba(100, 100, 100,.3);
}

.clear_sky, .few_clouds {

    background: linear-gradient(127deg, alpha(rgb(197, 198, 189), 1), alpha(rgb(0, 134, 218), 0) 100%),
    linear-gradient(217deg, alpha(rgb(197, 198, 189), 1), alpha(rgb(0, 134, 218), 1) 100%),
    linear-gradient(336deg, alpha(rgb(197, 198, 189), 1), alpha(rgb(0, 134, 218), 1) 100%);

} .overcast, .showers_scattered{

    background: linear-gradient(127deg, alpha(rgb(155, 155, 155), 1), alpha(rgb(0, 134, 215), 0) 100%),
    linear-gradient(217deg, alpha(rgb(155, 155, 155), 1), alpha(rgb(0, 134, 215), 1) 100%),
    linear-gradient(336deg, alpha(rgb(155, 155, 155), 1), alpha(rgb(0, 134, 218), 1) 100%);

} .showers_large {

    background: linear-gradient(127deg, alpha(rgb(134, 137, 154), 1), alpha(rgb(134, 137, 154), 0) 100%),
    linear-gradient(217deg, alpha(rgb(134, 137, 154), 1), alpha(rgb(0, 134, 218), 1) 100%),
    linear-gradient(336deg, alpha(rgb(134, 137, 154), 1), alpha(rgb(0, 134, 218), 1) 100%);

} .storm{

    background: linear-gradient(127deg, alpha(rgba(108,123,152,1), 1), alpha(rgba(92,92,92,1), 1) 100%),
    linear-gradient(217deg, alpha(rgba(108,123,152,1), 1), alpha(rgba(92,92,92,1), 1) 100%),
    linear-gradient(336deg, alpha(rgba(108,123,152,1), 1), alpha(rgba(92,92,92,1), 1) 100%);

} .snow{

    background: linear-gradient(127deg, alpha(rgb(126, 126, 126), 1), alpha(rgba(92,92,92,1), 1) 100%),
    linear-gradient(217deg, alpha(rgb(126, 126, 126), 1), alpha(rgba(92,92,92,1), 1) 100%),
    linear-gradient(336deg, alpha(rgb(126, 126, 126), 1), alpha(rgba(92,92,92,1), 1) 100%);

} .fog{

    background: linear-gradient(127deg, alpha(rgb(126, 126, 126), 1), alpha(rgb(126, 126, 126), 1) 100%),
    linear-gradient(217deg, alpha(rgb(126, 126, 126), 1), alpha(rgb(126, 126, 126), 1) 100%),
    linear-gradient(336deg, alpha(rgb(126, 126, 126), 1), alpha(rgb(126, 126, 126), 1) 100%);

}

/* ------------- night --------------- */

.clear_sky_night, .few_clouds_night{

    background: linear-gradient(127deg, alpha(rgb(45, 48, 72), 1), alpha(rgb(23, 27, 60), 0) 100%),
    linear-gradient(217deg, alpha(rgb(45, 48, 72), 1), alpha(rgb(23, 27, 60), 1) 100%);

} .overcast_night, .showers_scattered_night {

    background: linear-gradient(127deg, alpha(rgb(27, 29, 40), 1), alpha(rgb(23, 27, 60), 0) 100%),
    linear-gradient(217deg, alpha(rgb(27, 29, 40), 1), alpha(rgb(46, 46, 46), 1) 100%);

} .showers_large_night {

    background: linear-gradient(127deg, alpha(rgb(27, 29, 40), 1), alpha(rgb(23, 27, 60), 0) 100%),
    linear-gradient(237deg, alpha(rgb(27, 29, 40), 1), alpha(rgb(46, 46, 46), 1) 100%);

} .storm_night{

    background: linear-gradient(127deg, alpha(rgba(50,50,50,1), 1), alpha(rgba(54,55,37,1), 1) 100%),
                linear-gradient(237deg, alpha(rgba(50,50,50,1), 1), alpha(rgba(54,55,37,1), 1) 100%);

} .snow_night{

    background: linear-gradient(127deg, alpha(rgba(50,50,50,1), 1), alpha(rgba(98,98,98,1), 1) 100%),
    linear-gradient(217deg, alpha(rgba(50,50,50,1), 1), alpha(rgba(98,98,98,1), 1) 100%),
    linear-gradient(336deg, alpha(rgba(50,50,50,1), 1), alpha(rgba(98,98,98,1), 1) 100%);

} .fog_night{

    background: linear-gradient(127deg, alpha(rgb(28, 27, 38), 1), alpha(rgb(50,50,50), 0) 100%),
    linear-gradient(217deg, alpha(rgb(50,50,50), 1), alpha(rgb(28, 27, 38), 1) 100%);

}

"""

# Thanks to https://github.com/SalaniLeo for this beautiful gradients collection
