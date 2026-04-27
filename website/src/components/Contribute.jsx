// 1. Centralized Data
const CONTRIBUTE_DATA = {
  title: "Contribute",
  description: "Mousam is built by the community, for the community. Your contributions help ensure that everyone has access to a beautiful, open-source weather tool.",
  contributors: {
    imageSrc: "https://contrib.rocks/image?repo=amit9838/mousam&columns=12",
    href: "https://github.com/amit9838/mousam/graphs/contributors",
  },
  waysToHelp: [
    {
      id: "translate",
      icon: "fa-solid fa-globe",
      text: "Translate the app in your native language",
      link: "https://github.com/amit9838/mousam",
    },
    {
      id: "develop",
      icon: "fa-solid fa-code",
      text: "If you love python you can definitely help in the development",
      link: "https://github.com/amit9838/mousam/blob/master/Contribution_Guide.md",
    },
    {
      id: "issues",
      icon: "fa-solid fa-code-branch",
      text: "Raise issues for bugs or request a feature",
      link: "https://github.com/amit9838/mousam/issues",
    },
  ],
};

// 2. Reusable Sub-component for individual contribution links
function ContributionItem({ item }) {
  return (
    <a
      href={item.link}
      target="_blank"
      rel="noreferrer"
      className="group flex items-center p-3 md:p-4 bg-zinc-950 border border-white/5 rounded-2xl hover:bg-white/5 hover:border-white/10 transition-all duration-300 w-full"
    >
      <div className="w-12 h-12 flex items-center justify-center bg-sky-500/10 text-sky-400 rounded-xl group-hover:scale-110 group-hover:bg-sky-500/20 transition-all flex-shrink-0">
        <i className={`${item.icon} text-lg`}></i>
      </div>
      <span className="ml-4 text-sm md:text-base text-neutral-400 group-hover:text-white font-medium transition-colors font-['Inter'] leading-tight">
        {item.text}
      </span>
      <div className="ml-auto pl-4 flex-shrink-0">
        <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center group-hover:bg-sky-500 group-hover:text-white text-neutral-500 transition-all">
          <i className="fa-solid fa-arrow-right-long text-xs"></i>
        </div>
      </div>
    </a>
  );
}

// 3. Main Component
export default function Contribute() {
  return (
    <section
      id="contribute"
      className="relative blueprint-grid bg-neutral-900/30 w-full overflow-hidden"
    >
      <div className="relative z-10 py-16 px-6 md:px-12 lg:px-24 max-w-7xl mx-auto w-full">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16">
          
          {/* Left Column: Context & Contributors */}
          <div className="lg:col-span-5 space-y-8 flex flex-col justify-center">
            <div>
              <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-white/90 mb-4 font-['Outfit']">
                {CONTRIBUTE_DATA.title}
              </h2>
              <p className="text-sm md:text-base text-neutral-400 font-['Inter'] leading-relaxed max-w-md">
                {CONTRIBUTE_DATA.description}
              </p>
            </div>

            <div className="flex flex-col gap-3">
              <h4 className="text-sm font-bold text-neutral-500 uppercase tracking-widest font-['Inter']">
                Current Contributors
              </h4>
              <a 
                href={CONTRIBUTE_DATA.contributors.href}
                target="_blank"
                rel="noreferrer"
                className="block bg-zinc-950 border border-white/5 p-4 rounded-2xl hover:border-white/10 transition-colors w-fit"
              >
                <img 
                  src={CONTRIBUTE_DATA.contributors.imageSrc} 
                  className="w-full max-w-[400px] opacity-80 hover:opacity-100 transition-opacity" 
                  alt="Contributors" 
                  loading="lazy"
                />
              </a>
            </div>
          </div>

          {/* Right Column: Interactive Contribution Links */}
          <div className="lg:col-span-7 flex flex-col justify-center border-t border-white/5 lg:border-t-0 lg:border-l lg:pl-16 pt-10 lg:pt-0">
            <h4 className="text-xl md:text-2xl font-bold text-white mb-6 font-['Outfit'] flex items-center gap-3">
              <span className="w-2 h-8 bg-sky-500 rounded-full inline-block"></span>
              How you contribute
            </h4>
            <div className="flex flex-col gap-4">
              {CONTRIBUTE_DATA.waysToHelp.map((item) => (
                <ContributionItem key={item.id} item={item} />
              ))}
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}