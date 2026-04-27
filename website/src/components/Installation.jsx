import { useState } from "react";
import CopyToClipboard from "./CopyToClipboard";
import Button from "./Button";

// 1. Centralized Data Object
const INSTALLATION_DATA = {
  flatpak: {
    title: "Download from Flathub",
    badge: {
      src: "https://dl.flathub.org/assets/badges/flathub-badge-en.png",
      alt: "Flathub",
      href: "https://flathub.org/apps/io.github.amit9838.mousam",
      className: "h-14",
    },
    steps: [
      {
        id: "01",
        title: "Setup Flatpak",
        desc: "Ensure Flatpak is installed on your Linux distribution before proceeding.",
        action: {
          type: "button",
          label: "Setup Instructions",
          href: "https://flathub.org/setup",
        },
      },
      {
        id: "02",
        title: "Install Command",
        desc: "Copy and paste the following command into your terminal emulator.",
        action: {
          type: "command",
          code: "flatpak install flathub io.github.amit9838.mousam",
        },
      },
    ],
  },
  snap: {
    title: "Install from Snap Store",
    badge: {
      src: "https://github.com/snapcore/snap-store-badges/blob/master/EN/%5BEN%5D-snap-store-black-uneditable.png?raw=true",
      alt: "Snap Store",
      href: "https://snapcraft.io/mousam",
      className: "h-14",
    },
    steps: [
      {
        id: "01",
        title: "Install Command",
        desc: "Copy and paste the following command into your terminal emulator.",
        action: {
          type: "command",
          code: "sudo snap install mousam",
        },
      },
    ],
  },
  other: {
    title: "Debian Package (Unofficial)",
    desc: "Community-maintained package for Debian-based distributions. Special thanks to @hsbasu.",
    badge: {
      src: "https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Ftse3.mm.bing.net%2Fth%3Fid%3DOIP.Dq1Eh6YE4JsXJ3PoEex_mgHaB6%26pid%3DApi&f=1&ipt=ec8d6c34b59888708ff908b9e26024e965a7759fbe90365b24f607db892d9d3f&ipo=images",
      alt: "Debian Package",
      href: "https://github.com/amit9838/mousam/discussions/68",
      className: "h-12 w-auto object-contain rounded-xl border border-white/10",
    },
    steps: [
      {
        id: "01",
        title: "Installation Setup",
        desc: "Visit the discussion thread for detailed installation instructions.",
        action: {
          type: "button",
          label: "Installation Instructions",
          href: "https://github.com/amit9838/mousam/discussions/68",
        },
      },
    ],
  },
};

const TABS = [
  { key: "flatpak", label: "Flatpak" },
  { key: "snap", label: "Snap" },
  { key: "other", label: "Other" },
];

// 2. Reusable Sub-components
function TerminalCommand({ code }) {
  return (
    <div className="relative group overflow-hidden bg-zinc-950 border border-white/10 p-4 md:p-5 rounded-2xl flex items-center justify-between transition-all hover:border-white/20">
      <div className="flex items-center gap-4 overflow-hidden w-full">
        <i className="fa-solid fa-terminal text-neutral-600 text-sm hidden sm:block"></i>
        <code className="text-sky-400 font-mono text-sm overflow-x-auto whitespace-nowrap scrollbar-hide flex-1">
          {code}
        </code>
      </div>
      <div className="flex-shrink-0 ml-3 bg-zinc-950 pl-2">
        <CopyToClipboard text={code} />
      </div>
    </div>
  );
}

function StepBlock({ step }) {
  return (
    <div className="flex flex-col gap-3 md:gap-4">
      <h4 className="text-lg md:text-xl font-bold text-white font-['Outfit'] flex items-center gap-3">
        <span className="w-8 h-8 rounded-lg bg-sky-500/10 flex items-center justify-center text-sky-400 text-sm flex-shrink-0">
          {step.id}
        </span>
        {step.title}
      </h4>
      <div className="pl-11 md:pl-12">
        <p className="text-neutral-400 text-sm mb-4 leading-relaxed">
          {step.desc}
        </p>
        {step.action.type === "command" && (
          <TerminalCommand code={step.action.code} />
        )}
        {step.action.type === "button" && (
          <Button
            variant="secondary"
            size="sm"
            className="uppercase tracking-widest gap-2 text-xs md:text-sm"
            href={step.action.href}
          >
            {step.action.label} <i className="fa-solid fa-arrow-right-long ml-1 text-sky-400"></i>
          </Button>
        )}
      </div>
    </div>
  );
}

// 3. Tab Content view utilizing grid for responsive desktop rendering
function TabContent({ data }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-16 font-['Inter'] w-full">
      {/* Left Column: Title & Badge */}
      <div className="lg:col-span-4 space-y-4">
        <h3 className="text-2xl font-bold text-white font-['Outfit']">
          {data.title}
        </h3>
        {data.desc && (
          <p className="text-neutral-400 text-sm leading-relaxed max-w-sm">
            {data.desc}
          </p>
        )}
        <a
          href={data.badge.href}
          className="inline-block transition-transform hover:scale-105 mt-2"
          target="_blank"
          rel="noreferrer"
        >
          <img
            src={data.badge.src}
            alt={data.badge.alt}
            className={data.badge.className}
          />
        </a>
      </div>

      {/* Right Column: Dynamic Steps */}
      <div className="lg:col-span-8 space-y-8 md:space-y-10 border-l-0 lg:border-l border-white/5 lg:pl-10">
        {data.steps.map((step) => (
          <StepBlock key={step.id} step={step} />
        ))}
      </div>
    </div>
  );
}

// 4. Main Component Wrapper
export default function Installation() {
  const [activeTab, setActiveTab] = useState("flatpak");

  return (
    <section
      id="installation"
      className="relative blueprint-grid bg-neutral-900/30 w-full overflow-hidden"
    >
      {/* `max-w-7xl` and `mx-auto` lock the width centrally for large desktops */}
      <div className="relative z-10 py-16 px-6 md:px-12 lg:px-24 max-w-7xl mx-auto w-full">
        <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-white/90 mb-8 md:mb-12">
          Installation
        </h2>

        {/* Scrollable container on mobile prevents overflow issues */}
        <div className="flex gap-6 md:gap-10 mb-10 md:mb-12 border-b border-white/5 overflow-x-auto scrollbar-hide">
          {TABS.map((tab) => {
            const isActive = tab.key === activeTab;
            return (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`pb-4 px-1 font-bold text-xs md:text-sm tracking-widest uppercase transition-all duration-300 relative whitespace-nowrap ${
                  isActive
                    ? "text-sky-400"
                    : "text-neutral-500 hover:text-neutral-300"
                }`}
              >
                {tab.label}
                {isActive && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-sky-500 animate-in slide-in-from-left-full duration-300"></div>
                )}
              </button>
            );
          })}
        </div>

        <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 w-full">
          <TabContent data={INSTALLATION_DATA[activeTab]} />
        </div>
      </div>
    </section>
  );
}