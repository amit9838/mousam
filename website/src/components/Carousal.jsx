// src/Carousel.js
import { useState } from "react";
import ImageSlide from "./ImageSlide";
import Button from "./Button";

// const images = [
//   "https://raw.githubusercontent.com/amit9838/mousam/master/screenshots/ss5-overcast.png?raw=true#gh-dark-mode-only",
//   "https://raw.githubusercontent.com/amit9838/mousam/master/screenshots/ss1-dark_mode.png?raw=true#gh-dark-mode-only",
//   "https://raw.githubusercontent.com/amit9838/mousam/master/screenshots/ss4-light_mode.png?raw=true#gh-light-mode-only",
// ];

const images = [
  {
    title: "Main Dashboard",
    description: "Real-time weather conditions with high-fidelity icons and dynamic background.",
    link: "https://raw.githubusercontent.com/amit9838/mousam/master/screenshots/ss1.png",
  },
  {
    title: "Detailed Forecast",
    description: "Deep insights into hourly temperature, precipitation, and wind patterns.",
    link: "https://raw.githubusercontent.com/amit9838/mousam/master/screenshots/ss2.png",
  },
  {
    title: "Night Mode",
    description: "Dark mode optimized interface with celestial tracking for sun and moon.",
    link: "https://raw.githubusercontent.com/amit9838/mousam/master/screenshots/ss3.png",
  },
  {
    title: "Air Quality Index",
    description: "Comprehensive tracking of air pollutants like PM2.5, PM10, and Ozone.",
    link: "https://raw.githubusercontent.com/amit9838/mousam/master/screenshots/air_pollutents.png",
  },
  {
    title: "Compact Mode",
    description: "A sleek, minimal interface for essential weather data at a glance.",
    link: "https://raw.githubusercontent.com/amit9838/mousam/master/screenshots/compact_mode.png",
  },
  {
    title: "Advanced Settings",
    description: "Granular control over notifications, units, and debugging tools.",
    link: "https://raw.githubusercontent.com/amit9838/mousam/master/screenshots/preferences.png",
  },
];

const Carousel = () => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);

  const goToNextSlide = () => {
    setLoading(true);
    setCurrentIndex((prev) => (prev + 1) % images.length);
  };

  const goToPrevSlide = () => {
    setLoading(true);
    setCurrentIndex((prev) => (prev - 1 + images.length) % images.length);
  };

  return (
    <section id="showcase" className="relative blueprint-grid bg-neutral-900/40 border-y border-white/5 w-full overflow-hidden">
      <div className="relative z-10 col-span-12 py-10 px-2 md:px-16 lg:px-24 max-w-7xl mx-auto">
        <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-white/90 mb-6 text-center lg:text-left px-6 md:px-0">Showcase</h2>

        <div className="relative">
          {/* Subtle Background Glow behind the image */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full bg-sky-500/[0.02] blur-[100px] rounded-full pointer-events-none"></div>

          <div className="relative z-10">
            {/* Loader */}
            {loading && (
              <div className="absolute inset-0 z-20 flex items-center justify-center bg-zinc-900/40 rounded-xl">
                <div className="w-10 h-10 border-4 border-sky-500/20 border-t-sky-500 rounded-full animate-spin"></div>
              </div>
            )}

            {/* Main Image Container */}
            <div className="flex items-center justify-center relative">
              <img
                src={images[currentIndex].link}
                alt={images[currentIndex].title}
                onLoad={() => setLoading(false)}
                className={`w-full md:max-w-4xl md:max-h-[550px] h-auto object-contain md:mx-auto rounded-xl md:rounded-3xl shadow-2xl transition-all duration-700 ${loading ? "opacity-0" : "opacity-100"}`}
              />
            </div>

            {/* Minimal Info & Controls */}
            <div className="mt-6 flex flex-col lg:flex-row lg:items-end justify-between gap-6 text-center lg:text-left px-6 md:px-0">
              <div className="max-w-xl animate-in fade-in slide-in-from-left-4 duration-700" key={`info-${currentIndex}`}>
                <h3 className="text-xl md:text-2xl font-bold text-white mb-3 font-['Outfit']">{images[currentIndex].title}</h3>
                <p className="text-sm md:text-base text-neutral-400 font-['Inter'] leading-relaxed">{images[currentIndex].description}</p>
              </div>

              <div className="flex items-center gap-5 self-center lg:self-end bg-white/5 p-2.5 rounded-2xl border border-white/10 backdrop-blur-md">
                <div className="flex gap-2 mr-1">
                  {images.map((_, i) => (
                    <button
                      key={i}
                      onClick={() => { setLoading(true); setCurrentIndex(i); }}
                      className={`h-1 rounded-full transition-all duration-300 ${i === currentIndex ? "w-6 bg-sky-500" : "w-1.5 bg-white/10 hover:bg-white/20"}`}
                    />
                  ))}
                </div>
                <div className="flex gap-2">
                  <Button
                    onClick={goToPrevSlide}
                    variant="secondary"
                    size="icon"
                  >
                    <i className="fa-solid fa-chevron-left text-xs"></i>
                  </Button>
                  <Button
                    onClick={goToNextSlide}
                    variant="primary"
                    size="icon"
                  >
                    <i className="fa-solid fa-chevron-right text-xs"></i>
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Carousel;
