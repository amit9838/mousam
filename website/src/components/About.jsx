// 1. Constants for clean configuration
const TECH_STACK = ["Python", "GTK4", "Libadwaita", "Cairo", "Open-Meteo API"];

const SOCIAL_LINKS = [
  { icon: "fa-brands fa-linkedin", href: "https://www.linkedin.com/in/amit-chaudhary-2b8b22199/" },
  { icon: "fa-brands fa-square-x-twitter", href: "https://twitter.com/AMIT0539" },
];

export default function About() {
  return (
    <section id="about" className="relative blueprint-grid bg-neutral-900/30 w-full overflow-hidden">
      <div className="relative z-10 py-16 px-6 md:px-12 lg:px-24 max-w-7xl mx-auto w-full">
        
        {/* Responsive Grid Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-20">
          
          {/* Left Column: Project Overview */}
          <div className="lg:col-span-6 space-y-8 font-['Inter']">
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-white/90">About</h2>
            
            <div className="space-y-6 text-neutral-400 leading-relaxed text-sm md:text-base">
              <p>
                Mousam is a sleek desktop-weather application offering real-time weather updates, 
                24-hour and 7-day forecasts. It features comprehensive <strong>Air Quality Index</strong> tracking, 
                a minimal <strong>Compact Mode</strong>, and rich visual data representations.
              </p>
              
              <p>
                Developed with <span className="text-sky-400">Python</span> and <span className="text-sky-400">GTK4</span>, 
                the app utilizes <span className="text-sky-400">Libadwaita</span> and <span className="text-sky-400">Cairo</span> 
                for a native look and feel, fetching precise data via the <span className="text-sky-400">Open-Meteo API</span>.
              </p>
            </div>
          </div>

          {/* Right Column: Author Card */}
          <div className="lg:col-span-6 flex items-start">
            <div className="relative group w-full bg-zinc-950 border border-white/5 rounded-3xl p-6 md:p-8 overflow-hidden transition-all duration-500 hover:border-white/10">
              {/* Background Glow */}
              <div className="absolute -top-24 -right-24 w-64 h-64 bg-sky-500/5 blur-[120px] rounded-full"></div>

              <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6 relative z-10">
                <div className="relative flex-shrink-0">
                  <img
                    src="https://avatars.githubusercontent.com/u/61614402?v=4"
                    alt="Amit Chaudhary"
                    className="h-24 w-24 rounded-2xl object-cover border border-white/10"
                  />
                  <div className="absolute -bottom-1 -right-1 bg-sky-500 text-white w-7 h-7 rounded-full flex items-center justify-center border-4 border-zinc-950">
                    <i className="fa-solid fa-code text-[10px]"></i>
                  </div>
                </div>

                <div className="flex-1 text-center sm:text-left">
                  <h3 className="text-xl font-bold text-white font-['Outfit']">Amit Chaudhary</h3>
                  <p className="text-sky-400 font-medium text-xs tracking-widest uppercase mb-4">Software Engineer</p>

                  <p className="text-neutral-400 text-sm leading-relaxed mb-6 font-['Inter']">
                    I initiated Mousam as an exploration of GTK and Python. Passionate about 
                    open-source and building intuitive tools for the Linux community.
                  </p>

                  <div className="flex items-center justify-center sm:justify-start gap-3">
                    <a 
                      href="https://github.com/amit9838" 
                      target="_blank"
                      className="px-4 py-2 bg-white text-black text-xs font-bold rounded-lg hover:bg-neutral-200 transition-colors"
                    >
                      Follow on GitHub
                    </a>
                    {SOCIAL_LINKS.map((link, i) => (
                      <a key={i} href={link.href} target="_blank" className="w-9 h-9 flex items-center justify-center rounded-lg bg-white/5 border border-white/10 text-neutral-400 hover:text-white hover:bg-white/10 transition-all">
                        <i className={`${link.icon} text-lg`}></i>
                      </a>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}