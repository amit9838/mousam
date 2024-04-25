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
            <Button
              onClick={() => {
                const element = document.getElementById("installation");
                element.scrollIntoView({
                  behavior: "smooth",
                });
              }}
              myStyle="bg-gradient-to-r from-[#166EAE] to-[#7B8389]  px-5 py-2  font-semibold rounded-full mt-20 text-white border-[1px] border-gray-400/70 hover:border-gray-300 "
            >
              INSTALL
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}
