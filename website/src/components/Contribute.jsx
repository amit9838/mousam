const askContribution = [
  {
    icon: "fa-solid fa-globe",
    text: "Translate the app in your native language",
    link: "https://github.com/amit9838/mousam",
  },
  {
    icon: "fa-solid fa-code",
    text: "If you love python you can definitely help in the development of the project",
    link: "https://github.com/amit9838/mousam/blob/master/Contribution_Guide.md",
  },
  {
    icon: "fa-solid fa-code-branch",
    text: "Raise issue for bugs or request a feature",
    link: "https://github.com/amit9838/mousam/issues",
  },
];

export default function Contribute() {
  return (
    <section id="contribute" className="blueprint-grid bg-neutral-900/30">
      <div className="blueprint-col-sidebar min-h-[300px]">
        <div className="blueprint-marker -top-[3px] -right-[3px]" />
      </div>

      <div className="blueprint-col-content">
        <h2 className="text-4xl font-bold tracking-tight text-white/90 mb-8">Contribute</h2>
        <div className="max-w-3xl">
          <p className="text-base text-neutral-400 mb-8 font-['Inter'] leading-relaxed">
            Mousam is built by the community, for the community. Your contributions help ensure that everyone has access to a beautiful, open-source weather tool.
          </p>

          <div className="flex flex-wrap gap-4 mb-10">
            <a href="https://github.com/amit9838/mousam/graphs/contributors">
              <img src="https://contrib.rocks/image?repo=amit9838/mousam&columns=14" className="rounded-xl border border-white/5 w-full" alt="Contributors" />
            </a>
          </div>

          <h4 className="text-xl font-bold text-white mb-6 font-['Outfit']">How you can help</h4>
          <div className="grid gap-3">
            {askContribution.map((item) => (
              <a
                key={item.icon}
                href={item.link}
                className="group flex items-center p-3 bg-white/5 border border-white/5 rounded-xl hover:bg-white/10 hover:border-white/10 transition-all duration-300"
              >
                <div className="w-10 h-10 flex items-center justify-center bg-sky-500/10 text-sky-400 rounded-lg group-hover:scale-110 transition-transform">
                  <i className={`${item.icon} text-sm`}></i>
                </div>
                <span className="ml-4 text-sm text-neutral-400 group-hover:text-white font-medium">{item.text}</span>
                <i className="fa-solid fa-arrow-right-long ml-auto mr-2 text-neutral-600 group-hover:text-sky-400 transition-colors text-xs"></i>
              </a>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
