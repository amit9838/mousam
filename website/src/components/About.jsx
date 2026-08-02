import Button from "./Button";
export default function About() {
  let code_style = "bg-white/10 px-2 py-0.5 rounded text-sky-300 font-mono text-sm";
  return (
    <section id="about" className="blueprint-grid bg-neutral-950/30">
      <div className="blueprint-col-sidebar min-h-[300px]">
        <div className="blueprint-marker -top-[3px] -right-[3px]" />
      </div>

      <div className="blueprint-col-content">
        <h2 className="text-4xl font-bold tracking-tight text-white/90 mb-8">About</h2>
        <div className="max-w-3xl space-y-5 text-base text-neutral-400 leading-relaxed font-['Inter']">
          <p>
            Mousam is a sleek desktop-weather application offering real-time
            weather updates and forecasts for the next{" "}
            <code className={code_style}>24 hours</code> and{" "}
            <code className={code_style}>7 days</code>. It provides comprehensive{" "}
            <code className={code_style}>Air Quality Index</code> tracking, a minimal{" "}
            <code className={code_style}>Compact Mode</code>, and utilizes graphs and
            bars to visually represent weather conditions. Supports both{" "}
            <code className={code_style}>imperial</code> and{" "}
            <code className={code_style}> metric </code> units for user
            convenience.
          </p>
          <p>
            Developed with <code className={code_style}> Python</code> and{" "}
            <code className={code_style}>GTK4</code> using{" "}
            <code className={code_style}>Libadwaita</code> and{" "}
            <code className={code_style}>Cairo</code> for graphics, Mousam fetches
            weather data from the{" "}
            <code className={code_style}>Open-Meteo API</code>, ensuring accurate
            and timely information.
          </p>

          <div className="pt-10 border-t border-white/5">
            <div className="relative group max-w-xl bg-white/[0.03] border border-white/10 rounded-xl p-6 md:p-8 overflow-hidden transition-all duration-500 hover:bg-white/[0.05] hover:border-white/20">
              {/* Background Glow */}
              <div className="absolute -top-24 -right-24 w-64 h-64 bg-sky-500/10 blur-[100px] rounded-full group-hover:bg-sky-500/20 transition-colors duration-500"></div>

              <div className="relative z-10 flex flex-col md:flex-row items-center md:items-start gap-6">
                <div className="relative flex-shrink-0">
                  <img
                    src="https://avatars.githubusercontent.com/u/61614402?v=4"
                    alt="Amit Chaudhary"
                    className="h-24 w-24 md:h-32 md:w-32 rounded-xl object-cover shadow-2xl border border-white/10"
                  />
                  <div className="absolute -bottom-1.5 -right-1.5 bg-sky-500 text-white w-8 h-8 rounded-full flex items-center justify-center border-4 border-neutral-900 shadow-lg">
                    <i className="fa-solid fa-code text-[10px]"></i>
                  </div>
                </div>

                <div className="flex-1 text-center md:text-left">
                  <h3 className="text-2xl font-bold text-white tracking-tight mb-0.5 font-['Outfit']">Amit Chaudhary</h3>
                  <p className="text-sky-400 font-semibold mb-5 tracking-wide uppercase text-[10px]">Software Engineer</p>

                  <p className="text-neutral-400 text-sm leading-relaxed mb-6 font-['Inter']">
                    I initiated Mousam as an exploration of GTK and Python.
                    I’m passionate about open-source and the collaborative spirit of
                    building tools that empower users with beautiful, intuitive interfaces.
                  </p>

                  <div className="flex flex-wrap items-center justify-center md:justify-start gap-3">
                    <Button
                      href="https://github.com/amit9838"
                      target="_blank"
                      variant="white"
                      size="sm"
                      className="gap-2 px-5 py-2"
                    >
                      <i className="fa-brands fa-github"></i>
                      Follow
                    </Button>

                    <div className="flex gap-2">
                      <a href="https://www.linkedin.com/in/amit-chaudhary-2b8b22199/" target="_blank" className="w-9 h-9 flex items-center justify-center rounded-lg bg-white/5 border border-white/10 text-neutral-400 hover:text-white hover:bg-white/10 transition-all">
                        <i className="fa-brands fa-linkedin text-lg"></i>
                      </a>
                      <a href="https://twitter.com/AMIT0539" target="_blank" className="w-9 h-9 flex items-center justify-center rounded-lg bg-white/5 border border-white/10 text-neutral-400 hover:text-white hover:bg-white/10 transition-all">
                        <i className="fa-brands fa-square-x-twitter text-lg"></i>
                      </a>
                    </div>
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
