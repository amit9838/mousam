// src/Carousel.js
import { useState } from "react";
import ImageSlide from "./ImageSlide";

// const images = [
//   "https://raw.githubusercontent.com/amit9838/mousam/master/screenshots/ss5-overcast.png?raw=true#gh-dark-mode-only",
//   "https://raw.githubusercontent.com/amit9838/mousam/master/screenshots/ss1-dark_mode.png?raw=true#gh-dark-mode-only",
//   "https://raw.githubusercontent.com/amit9838/mousam/master/screenshots/ss4-light_mode.png?raw=true#gh-light-mode-only",
// ];

const images = [
  {
    title: "Clear Sky",
    lightingCondition: "Day",
    link: "https://raw.githubusercontent.com/amit9838/mousam/master/screenshots/ss1.png",
  },
  {
    title: "Snowfall",
    lightingCondition: "Day",
    link: "https://raw.githubusercontent.com/amit9838/mousam/master/screenshots/ss2.png",
  },
  {
    title: "Clear Sky",
    lightingCondition: "Night",
    link: "https://raw.githubusercontent.com/amit9838/mousam/master/screenshots/ss3.png",
  },
];

const Carousel = () => {
  const [currentIndex, setCurrentIndex] = useState(0);

  const goToNextSlide = () => {
    const newIndex = (currentIndex + 1) % images.length;
    setCurrentIndex(newIndex);
  };

  const goToPrevSlide = () => {
    const newIndex = (currentIndex - 1 + images.length) % images.length;
    setCurrentIndex(newIndex);
  };

  return (
    <div className="relative bg-primary">
      <h2 className="mx-8 pt-5 text-white text-xl border-b-[1px] border-slate-400">
        Screenshots
      </h2>
      <div className="overflow-hidden">
        <div className="flex transition-transform duration-300 ease-in-out transform translate-x-[-${currentIndex * 100}%]">
          <ImageSlide path={images[currentIndex].link} />
        </div>
      </div>

      <div className="py-2 px-10 w-full bg-[#15212b] text-neutral-300 flex items-center justify-center">
        <div className="controllor w-full max-w-[41rem] flex items-center justify-between font-['ubuntu']">
          <div className="title"><h1>{images[currentIndex].title}</h1>
          <p className="text-sm text-neutral-400">{images[currentIndex].lightingCondition}</p>
          </div>
          <div className="controls">
            <button
              className="bg-gray-800 w-[3rem] h-[3rem] rounded-full mx-2 hover:bg-gray-700"
              onClick={goToPrevSlide}
            >
              <i className="fa-solid fa-angle-left"></i>
            </button>
            <button
              className="bg-gray-800 w-[3rem] h-[3rem] rounded-full ml-2 hover:bg-gray-700"
              onClick={goToNextSlide}
            >
              <i className="fa-solid fa-angle-right"></i>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Carousel;
