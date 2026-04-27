import bg from "../assets/weather_bg.jpg";
import Navbar from "./Navbar";
import Button from "./Button";
export default function Hero() {
  return (
    <section id="home" className="relative blueprint-grid bg-zinc-900 overflow-hidden min-h-screen w-full">
      {/* Background Image - Full Width Cover */}
      <div
        className="absolute inset-0 z-0"
        style={{
          backgroundImage: `url(${bg})`,
          backgroundPosition: 'right center',
          backgroundSize: 'cover'
        }}
      ></div>

      {/* Dark Gradient Overlay for readability */}
      <div className="absolute inset-0 z-0 bg-gradient-to-r from-zinc-950 via-zinc-950/70 to-transparent"></div>

      <div className="relative z-10 col-span-12 flex items-center justify-start pt-28 pb-20 md:pt-36 px-6 md:px-16 lg:px-24">
        <div className="flex items-center">
          {/* Left Content */}
          <div className="max-w-2xl text-left">
            <div className="inline-flex items-center gap-3 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-500/20 text-sky-400 text-[10px] font-bold tracking-[0.2em] uppercase mb-8 md:mb-6">
              <span className="relative flex h-1.5 w-1.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-sky-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-sky-500"></span>
              </span>
              Mousam 2.0 is out
            </div>

            <h1 className="text-4xl md:text-6xl font-bold text-white mb-10 md:mb-6 leading-[1.2] tracking-tight font-['Outfit']">
              Elevate your <br className="hidden md:block" />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#4d94a5] to-sky-600">weather</span> experience.
            </h1>

            <p className="text-base md:text-lg text-neutral-400 mb-12 md:mb-10 max-w-lg font-['Inter'] leading-relaxed">
              Displays real-time temperature, humidity, wind speed, UV index, pressure along with weather and AQI forecasts
            </p>
            <div className="flex flex-wrap items-center justify-start gap-3">
              <Button
                className="gap-1 px-3"
                onClick={() => {
                  const element = document.getElementById("installation");
                  element.scrollIntoView({ behavior: "smooth" });
                }}
              >
                <i className="fa-solid fa-download text-sm"></i>
                Install Now
              </Button>

              <Button
                href="https://github.com/amit9838/mousam"
                target="_blank"
                variant="secondary"
                className="gap-1 px-3"
              >
                <i className="fa-brands fa-github text-sm"></i>
                View Source
              </Button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
