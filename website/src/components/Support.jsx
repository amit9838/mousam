export default function Support() {
  return (
    <section id="support" className="relative blueprint-grid bg-neutral-900/30 w-full overflow-hidden">
      <div className="relative z-10 py-16 px-6 md:px-12 lg:px-24 max-w-7xl mx-auto w-full">
        
        {/* Layout container matching other sections */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          
          {/* Text Content */}
          <div className="lg:col-span-7 space-y-4">
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-white/90 font-['Outfit']">
              Support Development
            </h2>
            <p className="text-sm md:text-base text-neutral-400 leading-relaxed font-['Inter'] max-w-lg">
              I hope you ❤️ Mousam. If you find the application useful and would like to support 
              its continued development, your contribution is greatly appreciated. 
              Every bit helps keep this project open and evolving.
            </p>
          </div>

          {/* Action Column */}
          <div className="lg:col-span-5 flex lg:justify-end">
            <a 
              href="https://www.buymeacoffee.com/ami9838"
              target="_blank"
              rel="noreferrer"
              className="group relative inline-block transition-all hover:scale-105 active:scale-95"
            >
              {/* Optional: Add a subtle glow behind the button */}
              <div className="absolute -inset-2 bg-gradient-to-r from-red-500/20 to-orange-500/20 rounded-2xl blur-lg opacity-50 group-hover:opacity-100 transition-opacity"></div>
              
              <img 
                src="https://img.buymeacoffee.com/button-api/?text=Buy me a coffee&emoji=☕&slug=ami9838&button_colour=FF5F5F&font_colour=ffffff&font_family=Comic&outline_colour=000000&coffee_colour=FFDD00" 
                alt="Buy me a coffee"
                className="relative h-14 shadow-2xl rounded-xl border border-white/10"
              />
            </a>
          </div>

        </div>
      </div>
    </section>
  );
}