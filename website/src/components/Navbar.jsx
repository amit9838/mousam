import { useState } from "react";
import logo from "../assets/weather.png";
import Button from "./Button";

const MENU_ITEMS = ["home", "installation", "contribute", "about"];

export default function Navbar() {
  const [showNav, setshowNav] = useState(false);

  const scrollTo = (id) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: "smooth" });
      setshowNav(false);
    }
  };

  return (
    <header className="fixed top-4 inset-x-0 z-[1000] px-4">
      <nav className="max-w-5xl mx-auto bg-zinc-900/70 backdrop-blur-xl border border-white/10 rounded-xl px-5 py-3 flex items-center justify-between shadow-[0_15px_40px_rgba(0,0,0,0.4)]">
        <div className="flex items-center gap-2 group cursor-pointer" onClick={() => scrollTo('home')}>
          <img src={logo} alt="logo" className="h-7 md:h-8 transition-transform group-hover:scale-110" />
          <h1 className="text-lg md:text-xl font-bold font-['Outfit'] tracking-tight">Mousam</h1>
        </div>

        {/* Desktop Menu */}
        <div className="hidden md:flex items-center gap-1">
          {MENU_ITEMS.map((item) => (
            <button
              key={item}
              onClick={() => scrollTo(item)}
              className="px-4 py-1.5 text-xs font-semibold text-neutral-400 hover:text-white transition-colors rounded-lg hover:bg-white/5 uppercase tracking-widest"
            >
              {item}
            </button>
          ))}
          <div className="w-px h-5 bg-white/10 mx-3"></div>
          <Button
            href="https://github.com/amit9838/mousam"
            target="_blank"
            rel="noreferrer"
            variant="white"
            size="sm"
            className="gap-2 px-4 py-1.5"
          >
            <i className="fa-brands fa-github text-sm"></i>
            GitHub
          </Button>
        </div>

        {/* Mobile Toggle */}
        <button
          className="md:hidden text-white p-2"
          onClick={() => setshowNav(true)}
        >
          <i className="fa-solid fa-bars-staggered text-xl"></i>
        </button>
      </nav>

      {/* Mobile Menu Overlay */}
      {showNav && (
        <div className="fixed inset-0 bg-zinc-950/90 backdrop-blur-2xl z-[1100] flex flex-col items-center justify-center p-8 animate-in fade-in duration-300">
          <button
            className="absolute top-8 right-8 text-white p-4"
            onClick={() => setshowNav(false)}
          >
            <i className="fa-solid fa-xmark text-3xl"></i>
          </button>

          <div className="flex flex-col items-center gap-8">
            {/* <img src={logo} alt="logo" className="h-20 mb-4" /> */}
            {MENU_ITEMS.map((item) => (
              <button
                key={item}
                onClick={() => scrollTo(item)}
                className="text-4xl font-bold text-white font-['Outfit'] hover:text-sky-400 transition-colors uppercase"
              >
                {item}
              </button>
            ))}
            <Button
              href="https://github.com/amit9838/mousam"
              target="_blank"
              rel="noreferrer"
              variant="white"
              size="lg"
              className="mt-8 gap-3 px-12 py-4"
            >
              <i className="fa-brands fa-github text-2xl"></i>
              GitHub
            </Button>
          </div>
        </div>
      )}
    </header>
  );
}
