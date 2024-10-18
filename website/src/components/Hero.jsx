import bg from "../assets/weather_bg.jpg";
import Navbar from "./Navbar";
import Button from "./Button";
export default function Hero() {
  return (
    <section id="home">
      <div
        className="relative h-screen bg-cover bg-right text-white"
        style={{ backgroundImage: `url(${bg})` }}
      >
        {/* Gradient overlay */}
        <div className="absolute inset-0 md:bg-gradient-to-r md:from-black  md:opacity-80 bg-gradient-to-b from-black  via-gray-800 opacity-80"></div>
        {/* Content inside the hero section */}
        <div className="relative">
          <Navbar />
          <div className=" p-8 mt-20 text-white z-100 ">
            <h1 className="text-lg font-mono mb-4 text-gray-200">
              THE ONLY WEATHER APP YOU NEED //
            </h1>
            <p className="text-5xl text-roboto max-w-[35rem] font-['Ubuntu']">
              Get
              <span className="font-semibold text-red-400]"> forecast </span>
              information at one place.
            </p>
            <p className="text-sm md:text-neutral-300/80 text-neutral-300 mx-1 mt-4 max-w-[24rem]">
              30k+ downloads from flathub, snapstore and other stores.
            </p>

            {/* <Button
              onClick={() => {
                const element = document.getElementById("installation");
                element.scrollIntoView({
                  behavior: "smooth",
                });
              }}
              myStyle="bg-gradient-to-r from-[#166EAE] to-[#7B8389]  px-5 py-2  font-semibold rounded-fullf mt-20 text-white border-[1px] border-gray-400/70 hover:border-gray-300 "
            >
              INSTALL
            </Button> */}
            <div className="grid grid-cols-[1fr_2fr_1fr] grid-rows-[1fr_2fr_1fr] h-20 w-40 gap-0 mt-20">
              {/* Top-left box */}
              <div className="border-r-[1px] border-b-[1px] border-gray-300"></div>
              {/* Top-center box */}
              <div className="border-b-[1px] border-gray-300"></div>
              {/* Top-right box */}
              <div className="border-l-[1px] border-b-[1px] border-gray-300"></div>

              {/* Middle-left box */}
              <div className="border-r-[1px] border-gray-300"></div>
              {/* Center box (Button) */}
              <div className="flex items-center justify-center">
                <button
                  onClick={() => {
                    const element = document.getElementById("installation");
                    element.scrollIntoView({
                      behavior: "smooth",
                    });
                  }}
                  className="bg-gradient-to-r from-[#166EAE] to-[#7B8389]  px-5 py-2  font-semibold  text-white hover:text-neutral-300"
                >
                  INSTALL
                </button>
              </div>
              {/* Middle-right box */}
              <div className="border-l-[1px] border-gray-300"></div>

              {/* Bottom-left box */}
              <div className="border-r-[1px] border-t-[1px] border-gray-300"></div>
              {/* Bottom-center box */}
              <div className="border-t-[1px] border-gray-300"></div>
              {/* Bottom-right box */}
              <div className="border-l-[1px] border-t-[1px] border-gray-300"></div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
