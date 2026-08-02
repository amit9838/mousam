export default function Support() {
  return (
    <section id="support" className="blueprint-grid bg-neutral-950/50">
      <div className="blueprint-col-sidebar min-h-[150px]">
        <div className="blueprint-marker -top-[3px] -right-[3px]" />
      </div>
      
      <div className="blueprint-col-content">
        <h2 className="text-4xl font-bold tracking-tight text-white/90 mb-8">Support</h2>
        <div className="max-w-2xl">
          <p className="text-base text-neutral-400 mb-8 font-['Inter'] leading-relaxed">
            I hope you ❤️ Mousam. If you find the application useful and would like to support its continued development, you can do so here. Your support is greatly appreciated!
          </p>

          <a 
            href="https://www.buymeacoffee.com/ami9838"
            target="_blank"
            className="inline-block transition-transform hover:scale-105 active:scale-95"
          >
            <img 
              src="https://img.buymeacoffee.com/button-api/?text=Buy me a coffee&emoji=☕&slug=ami9838&button_colour=FF5F5F&font_colour=ffffff&font_family=Comic&outline_colour=000000&coffee_colour=FFDD00" 
              alt="Buy me a coffee"
              className="h-12 shadow-lg rounded-xl"
            />
          </a>
        </div>
      </div>
    </section>
  );
}
