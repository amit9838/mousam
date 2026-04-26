import CopyToClipboard from "./CopyToClipboard";
import Button from "./Button";
export default function FlatpakInstallation() {
  const command = "flatpak install flathub io.github.amit9838.mousam";
  return (
    <div className="space-y-8 font-['Inter']">
      <div>
        <h3 className="text-2xl font-bold text-white mb-4 font-['Outfit']">
          Download from Flathub
        </h3>
        <a 
          href="https://flathub.org/apps/io.github.amit9838.mousam"
          className="inline-block transition-transform hover:scale-105"
        >
          <img
            src="https://dl.flathub.org/assets/badges/flathub-badge-en.png"
            alt="flathub"
            className="h-14"
          />
        </a>
      </div>

      <div className="space-y-8">
        <div className="flex flex-col gap-4">
          <h4 className="text-xl font-bold text-white font-['Outfit'] flex items-center gap-2">
            <span className="w-8 h-8 rounded-lg bg-sky-500/10 flex items-center justify-center text-sky-400 text-sm">01</span>
            Setup Flatpak
          </h4>
          <div className="pl-12">
            <p className="text-neutral-400 text-sm mb-4 leading-relaxed">Ensure Flatpak is installed on your Linux distribution before proceeding.</p>
            <Button
              variant="secondary"
              size="sm"
              className="uppercase tracking-widest gap-2"
              href="https://flathub.org/setup"
            >
              Setup Instructions <i className="fa-solid fa-arrow-right-long ml-1 text-sky-400"></i>
            </Button>
          </div>
        </div>

        <div className="flex flex-col gap-4">
          <h4 className="text-xl font-bold text-white font-['Outfit'] flex items-center gap-2">
            <span className="w-8 h-8 rounded-lg bg-sky-500/10 flex items-center justify-center text-sky-400 text-sm">02</span>
            Install Command
          </h4>
          <div className="pl-12">
            <p className="text-neutral-400 text-sm mb-4 leading-relaxed">Copy and paste the following command into your terminal emulator.</p>
            <div className="relative group overflow-hidden bg-zinc-950 border border-white/10 p-5 rounded-2xl flex items-center justify-between transition-all hover:border-white/20">
              <div className="flex items-center gap-4 overflow-hidden">
                <i className="fa-solid fa-terminal text-neutral-600 text-sm"></i>
                <code className="text-sky-400 font-mono text-sm overflow-x-auto whitespace-nowrap scrollbar-hide">
                  {command}
                </code>
              </div>
              <div className="flex-shrink-0 ml-4">
                <CopyToClipboard text={command} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
