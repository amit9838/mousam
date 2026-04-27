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
    <header className="fixed top-0 inset-x-0 z-[1000] w-full bg-zinc-950/70  border-b border-white/5">
      {/* Container restricted to max-w-7xl to align with main content sections */}
      <nav className="max-w-7xl mx-auto px-6 lg:px-24 h-16 flex items-center justify-between">
        
        {/* Brand Logo */}
        <div 
          className="flex items-center gap-3 group cursor-pointer" 
          onClick={() => scrollTo('home')}
        >
          <img src={logo} alt="Mousam" className="h-8 transition-transform group-hover:scale-105" />
          <span className="text-xl font-bold font-['Outfit'] tracking-tight text-white">Mousam</span>
        </div>

        {/* Desktop Menu */}
        <div className="hidden md:flex items-center gap-6">
          {MENU_ITEMS.map((item) => (
            <button
              key={item}
              onClick={() => scrollTo(item)}
              className="text-[11px] font-bold text-neutral-400 hover:text-white transition-colors uppercase tracking-[0.2em]"
            >
              {item}
            </button>
          ))}
          
          <div className="w-px h-4 bg-white/10"></div>
          
          <Button
            href="https://github.com/amit9838/mousam"
            target="_blank"
            variant="white"
            size="sm"
            className="px-4 py-1.5 text-[11px] uppercase tracking-widest gap-2"
          >
            <i className="fa-brands fa-github text-sm"></i>
            GitHub
          </Button>
        </div>

        {/* Mobile Toggle */}
        <button
          className="md:hidden text-neutral-400 hover:text-white p-2"
          onClick={() => setshowNav(true)}
        >
          <i className="fa-solid fa-bars-staggered text-lg"></i>
        </button>
      </nav>

      {/* Mobile Menu Overlay */}
      {showNav && (
        <div className="fixed inset-0 h-full w-full bg-zinc-950/95 z-[1100] flex flex-col p-6 animate-in fade-in duration-300">
          <div className="flex items-center justify-between mb-16">
            <span className="text-xl font-bold font-['Outfit']">Menu</span>
            <button className="text-white p-2" onClick={() => setshowNav(false)}>
              <i className="fa-solid fa-xmark text-2xl"></i>
            </button>
          </div>

          <div className="flex flex-col gap-8">
            {MENU_ITEMS.map((item) => (
              <button
                key={item}
                onClick={() => scrollTo(item)}
                className="text-3xl font-bold text-left text-white uppercase font-['Outfit']"
              >
                {item}
              </button>
            ))}
            
            <div className="mt-auto pt-10 border-t border-white/5">
              <Button
                href="https://github.com/amit9838/mousam"
                target="_blank"
                variant="secondary"
                size="md"
                className="w-full py-4 uppercase tracking-widest"
              >
                View Source Code
              </Button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}