// src/Carousel.js
import { useState } from "react";
import ImageSlide from "./ImageSlide";

const images = [
  "https://raw.githubusercontent.com/amit9838/mousam/master/screenshots/ss5-overcast.png?raw=true#gh-dark-mode-only",
  "https://raw.githubusercontent.com/amit9838/mousam/master/screenshots/ss1-dark_mode.png?raw=true#gh-dark-mode-only",
  "https://raw.githubusercontent.com/amit9838/mousam/master/screenshots/ss4-light_mode.png?raw=true#gh-light-mode-only",
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
          <ImageSlide path={images[currentIndex]} />
        </div>
      </div>
      <button
        className="absolute top-1/2 left-4 transform -translate-y-1/2 bg-slate-800/60 hover:bg-slate-800/80 px-3 py-1 text-dimWhite hover:text-white rounded-full shadow-lg"
        onClick={goToPrevSlide}
      >
        <i className="fa-solid fa-angle-left"></i>
      </button>
      <button
        className="absolute top-1/2 right-4 transform -translate-y-1/2 bg-slate-800/60 hover:bg-slate-800/80 px-3 py-1 text-dimWhite hover:text-white rounded-full shadow-lg"
        onClick={goToNextSlide}
      >
        <i className="fa-solid fa-angle-right"></i>
      </button>
    </div>
  );
};

export default Carousel;
