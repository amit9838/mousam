css = """
.condition_label {
    font-size: 30px;
}
.main_temp_label {
    font-size: 4rem;
}

.btn_sm{
    font-size:1rem;
    padding:0.2rem .9rem;
}


.text-l1{
    font-size: 4rem;
}
.text-l2{
    font-size: 3.5rem;
}
.text-l3{
    font-size: 3rem;
}
.text-l4{
    font-size: 2.5rem;
}
.text-1{
    font-size: 2rem;
}
.text-2a{
    font-size: 1.8rem;
}
.text-2b{
    font-size: 1.5rem;
}
.text-3{
    font-size: 1.3rem;
}
.text-3a{
    font-size: 1.2rem;
}
.text-4{
    font-size: 1.1rem;
}
.text-5{
    font-size: 1.05rem;
}
.text-6{
    font-size: .95rem;
}
.text-7{
    font-size: 9rem;
}
.text-8{
    font-size: .85rem;
}
.text-9{
    font-size: .8rem;
}

.title-xl{
    font-size:76px;
}
.title-l{
    font-size:42px;
}
.title-m{
    font-size:22px;
}
.title-s{
    font-size:18px;
}

.light-1{
    opacity: .95;
}
.light-2{
    opacity: .9;
}
.light-3{
    opacity: .8;
}
.light-4{
    opacity: .75;
}
.light-5{
    opacity: .7;
}
.light-6{
    opacity: .6;
}


.bold-1{
    font-weight: 700;
}
.bold-2{
    font-weight: 600;
}
.bold-3{
    font-weight: 500;
}


.dark{
    color:#141414;
}

.main_window{
    border-radius:13px;
    border : 1px solid rgba(100, 100, 100,.3);
}


.overcast, .showers_scattered{
    background: linear-gradient(127deg, rgba(155, 155, 155, 1), rgba(0, 134, 215, 0) 100%),
                linear-gradient(217deg, rgba(155, 155, 155, 1), rgba(0, 134, 215, 1) 100%),
                linear-gradient(336deg, rgba(155, 155, 155, 1), rgba(0, 134, 218, 1) 100%);
}

.gradient-bg{
    background:linear-gradient(0deg, rgba(237,237,237,1) 0%, rgb(203, 221, 225) 100%);
}

.bg-white{
    background-color: rgb(240, 240, 240);
}

.custom_card{
    padding:.5rem 1rem;
}

.bar_container{
    border-radius: 1rem;
    background-color: rgb(240, 240, 240);

}

.custom_card_forecast_item{
    padding: .15rem 1.5rem;
    border-radius: .7rem;
}

.custom_card_hourly{
    border-radius: .5rem;
    padding: .7rem .7rem;
    margin-top: .3rem;
    background-color: rgba(100, 100, 100, .06);
}

.custom_card_hourly_now{
    padding: .7rem 1.2rem;
    margin-top: 0rem;
    background-color: rgba(100, 100, 100, .15);

}
.bg_light_grey{
    background-color: #9a9a9a13;
}





.body{
    padding:20px;

}
/* .card{
    padding-left:20px;
    padding-right:20px;
    padding-top:16px;
    padding-bottom:16px;
} */


.card_info{
    background-color: #F6635C;
}
.bold{
    font-weight:600;
}
.title-xl{
    font-size:76px;
}
.title-m{
    font-size:22px;
}
.title-s{
    font-size:18px;
}
.bg-green {
    background-color: #00ff00; /* Replace with your desired color */
}
.bg-orange {
    background-color: #F6635C; /* Replace with your desired color */
}
.bg-pink {
    background-color: #FE7BE5; /* Replace with your desired color */
}

.clear_sky, .few_clouds {
    background: linear-gradient(127deg, rgba(187, 188, 179, 1), rgba(0, 134, 218, 0) 100%),
                linear-gradient(217deg, rgba(187, 188, 179, 1), rgba(0, 174, 258, 1) 100%),
                linear-gradient(136deg, rgba(187, 188, 179, 1), rgba(0, 174, 258, 1) 100%);


} .overcast, .showers_scattered{
    background: linear-gradient(127deg, rgba(155, 155, 155, 1), rgba(0, 134, 215, 0) 100%),
                linear-gradient(217deg, rgba(155, 155, 155, 1), rgba(0, 134, 215, 1) 100%),
                linear-gradient(336deg, rgba(155, 155, 155, 1), rgba(0, 134, 218, 1) 100%);

} .showers_large {
    background: linear-gradient(127deg, rgba(134, 137, 154, 1), rgba(134, 137, 154, 0) 100%),
                linear-gradient(217deg, rgba(134, 137, 154, 1), rgba(0, 134, 218, 1) 100%),
                linear-gradient(336deg, rgba(134, 137, 154, 1), rgba(0, 134, 218, 1) 100%);

} .storm{
    background: linear-gradient(127deg, rgb(108, 123, 152), rgb(92, 92, 92)),
                linear-gradient(217deg, rgb(108, 123, 152), rgb(92, 92, 92)),
                linear-gradient(336deg, rgb(108, 123, 152), rgb(92, 92, 92));

} .snow{
    background: linear-gradient(135deg, rgb(40, 60, 87) 0%, rgb(80, 104, 133) 30%, rgb(137, 166, 181) 60%, rgb(187, 195, 202) 80%, rgb(187, 195, 202) 100%),
                linear-gradient(45deg, rgb(200, 203, 207), rgb(212, 213, 215) 50%, rgba(255, 255, 255, 0.9));

} .fog{
   background: linear-gradient(49deg, transparent 0%, rgba(212,195,156,0.43) 100%) 68% 73%/194% 147%,
                linear-gradient(137deg, #9cafb0 0%, #c4c3be 70%, #c5c8b5 100%) 72% 55%/174% 123%;

}

/* ------------- night --------------- */

.clear_sky_night{
    background: linear-gradient(127deg, rgba(45, 48, 72, 1), rgba(23, 27, 60, 0) 100%),
                linear-gradient(217deg, rgba(45, 48, 72, 1), rgba(23, 27, 60, 1) 100%);

}.few_clouds_night{
    background: linear-gradient(to right bottom, #777777, #69696c, #5b5c62, #4d5057, #3e444d, #353c47, #2b3440, #222d3a, #1c2735, #172130, #121b2b, #0e1526);

} .overcast_night, .showers_scattered_night {
    background: linear-gradient(127deg, rgba(27, 29, 40, 1), rgba(23, 27, 60, 0) 100%),
                linear-gradient(217deg, rgba(27, 29, 40, 1), rgba(46, 46, 46, 1) 100%);

} .showers_large_night {
    background: linear-gradient(127deg, rgba(27, 29, 40, 1), rgba(23, 27, 60, 0) 100%),
                linear-gradient(237deg, rgba(27, 29, 40, 1), rgba(46, 46, 46, 1) 100%);

} .storm_night{
    background: linear-gradient(127deg, rgba(50, 50, 50, 1), rgba(54, 55, 37, 1) 100%),
                linear-gradient(237deg, rgba(50, 50, 50, 1), rgba(54, 55, 37, 1) 100%);

} .snow_night{
    background: linear-gradient(127deg, rgba(50, 50, 50, 1), rgba(98, 98, 98, 1) 100%),
                linear-gradient(217deg, rgba(50, 50, 50, 1), rgba(98, 98, 98, 1) 100%),
                linear-gradient(336deg, rgba(50, 50, 50, 1), rgba(98, 98, 98, 1) 100%);

} .fog_night{
    background: linear-gradient(127deg, rgba(28, 27, 38, 1), rgba(50, 50, 50, 0) 100%),
                linear-gradient(217deg, rgba(50, 50, 50, 1), rgba(28, 27, 38, 1) 100%);
}
"""
