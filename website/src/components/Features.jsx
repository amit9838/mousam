const FEATURES = [
  {
    icon: "fa-lightbulb",
    text: "Overview of the Coming Hours",
  },
  {
    icon: "fa-bell",
    text: "Overview Notifications",
  },
  {
    icon: "fa-wind",
    text: "Air Quality, Pollutants & Pollen",
  },
  {
    icon: "fa-sun",
    text: "Sun, Moon & Twilight Graphs",
  },
  {
    icon: "fa-location-dot",
    text: "Saved Locations with Local Time",
  },
  {
    icon: "fa-compress",
    text: "Minimalist Compact Mode",
  },
  {
    icon: "fa-power-off",
    text: "Runs in the Background",
  },
  {
    icon: "fa-palette",
    text: "Dynamic Backgrounds & Icon Themes",
  },
  {
    icon: "fa-ruler",
    text: "Metric & Imperial Units",
  },
  {
    icon: "fa-language",
    text: "Translated into 21 Languages",
  },
];

export default function Features() {
  return (
    <section className="blueprint-grid bg-neutral-950/50">
      <div className="blueprint-col-sidebar min-h-[200px]">
        <div className="blueprint-marker -top-[3px] -right-[3px]" />
      </div>
      
      <div className="blueprint-col-content">
        <h2 className="text-4xl font-bold tracking-tight text-white/90 mb-8">Features</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {FEATURES.map((item) => {
            return (
              <div
                className="group flex flex-col items-center text-center p-4 transition-all duration-300"
                key={item.icon}
              >
                <div className="w-14 h-14 flex items-center justify-center bg-white/[0.03] border border-white/5 rounded-2xl mb-4 group-hover:bg-sky-500/10 group-hover:border-sky-500/20 transition-all duration-500">
                  <i className={`fa-solid ${item.icon} text-xl text-sky-400/80 group-hover:text-sky-400 transition-colors`}></i>
                </div>
                <h3 className="text-sm font-medium text-neutral-400 group-hover:text-white transition-colors duration-300 leading-snug px-2">
                  {item.text}
                </h3>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
