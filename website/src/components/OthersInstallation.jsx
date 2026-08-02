import Button from "./Button";
export default function OthersInstallation() {
  return (
      <div className="space-y-8">
        <div className="flex flex-col gap-4">
          <h3 className="text-xl font-bold text-white font-['Outfit']">
            Debian Package (Unofficial)
          </h3>
          <div className="">
            <p className="text-neutral-400 text-sm mb-6 leading-relaxed">Community-maintained package for Debian-based distributions. Special thanks to @hsbasu.</p>
            <a 
              href="https://github.com/amit9838/mousam/discussions/68"
              className="inline-block transition-transform hover:scale-105 mb-6"
            >
              <img
                src="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Ftse3.mm.bing.net%2Fth%3Fid%3DOIP.Dq1Eh6YE4JsXJ3PoEex_mgHaB6%26pid%3DApi&f=1&ipt=ec8d6c34b59888708ff908b9e26024e965a7759fbe90365b24f607db892d9d3f&ipo=images"
                alt="Debian Package"
                className="h-12 w-auto object-contain rounded-xl border border-white/10"
              />
            </a>
            <div className="block">
              <Button
                variant="secondary"
                size="sm"
                className="uppercase tracking-widest gap-2"
                href="https://github.com/amit9838/mousam/discussions/68"
              >
                Installation Instructions <i className="fa-solid fa-arrow-right-long ml-1 text-sky-400"></i>
              </Button>
            </div>
          </div>
        </div>
      </div>
  );
}
