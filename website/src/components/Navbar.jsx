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
    <header className="fixed top-0 inset-x-0 z-[1000] w-full bg-zinc-950/60  border-b border-white/5">
      <nav className="max-w-7xl mx-auto px-4 md:px-6 h-12 md:h-16 flex items-center justify-between">
        <div className="flex items-center gap-2 group cursor-pointer shrink-0" onClick={() => scrollTo('home')}>
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
          className="md:hidden text-white p-2 shrink-0"
          onClick={() => setshowNav(true)}
        >
          <i className="fa-solid fa-bars-staggered text-xl"></i>
        </button>
      </nav>

      {/* Mobile Menu Overlay */}
      {showNav && (
        <div className="fixed inset-0 bg-zinc-950 z-[1100] flex flex-col p-6 animate-in fade-in slide-in-from-top-4 duration-300">
          <div className="flex items-center justify-between mb-12">
            <div className="flex items-center gap-2">
              <img src={logo} alt="logo" className="h-7" />
              <h1 className="text-lg font-bold font-['Outfit']">Mousam</h1>
            </div>
            <button
              className="text-white p-2"
              onClick={() => setshowNav(false)}
            >
              <i className="fa-solid fa-xmark text-2xl"></i>
            </button>
          </div>

          <div className="flex flex-col gap-6">
            {MENU_ITEMS.map((item) => (
              <button
                key={item}
                onClick={() => scrollTo(item)}
                className="text-2xl font-bold text-left text-neutral-400 hover:text-white transition-colors uppercase tracking-widest font-['Outfit']"
              >
                {item}
              </button>
            ))}
            
            <div className="mt-8 pt-8 border-t border-white/10">
              <p className="text-xs font-bold text-neutral-500 uppercase tracking-widest mb-4">Community</p>
              <Button
                href="https://github.com/amit9838/mousam"
                target="_blank"
                rel="noreferrer"
                variant="secondary"
                size="md"
                className="w-full gap-3 py-4"
              >
                <i className="fa-brands fa-github text-xl"></i>
                GitHub Source
              </Button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
