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

.rain_summ_box {
        background-color:rgba(255, 255, 255, 0.06);
        padding:2px 8px;
        border-radius: 5px;
        font-size:14px;
}

.forecast_box {
        border-radius: 5px;
    }


.f-sm {
        font-size: 14px;
    }
.f-m {
        font-size: 16px;
    }

.f-lg {
        font-size: 18px;
    }
.f-lg2 {
        font-size: 20px;
    }

.bold{
    font-weight:500;
}

.bolder{
    font-weight:600;
}

.secondary{
    opacity:.65;
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

.btn_sm{
    font-size:14px;
    padding:0px 12px;
}

.main_window{
    border-radius:13px;
    border : 1px solid rgba(100, 100, 100,.3);
}

.clear_sky, .few_clouds {
    background: linear-gradient(127deg, alpha(rgb(187, 188, 179), 1), alpha(rgb(0, 134, 218), 0) 100%),
    linear-gradient(217deg, alpha(rgb(187, 188, 179), 1), alpha(rgb(0, 174, 258), 1) 100%),
    linear-gradient(136deg, alpha(rgb(187, 188, 179), 1), alpha(rgb(0, 174, 258), 1) 100%);

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
    background: linear-gradient(49deg, transparent 0%, rgba(212,195,156,0.43) 100%) 68% 73%/194% 147%,
            linear-gradient(137deg, #9cafb0 0%, #c4c3be 70%, #c5c8b5 100%) 72% 55%/174% 123%;
}

/* ------------- night --------------- */

.clear_sky_night{
    background: linear-gradient(127deg, alpha(rgb(45, 48, 72), 1), alpha(rgb(23, 27, 60), 0) 100%),
    linear-gradient(217deg, alpha(rgb(45, 48, 72), 1), alpha(rgb(23, 27, 60), 1) 100%);
}
.few_clouds_night{
    background: linear-gradient(to right bottom, #777777, #69696c, #5b5c62, #4d5057, #3e444d, #353c47, #2b3440, #222d3a, #1c2735, #172130, #121b2b, #0e1526);
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
