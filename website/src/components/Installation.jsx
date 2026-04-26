import { useState } from "react";
import Button from "./Button";
import FlatpakInstallation from "./FlatpakInstallation";
import SnapInstallation from "./SnapInstallation";
import OthersInstallation from "./OthersInstallation";
const tabs = [
  {
    tab_name: "flatpak",
    content: <FlatpakInstallation />,
  },
  {
    tab_name: "snap",
    content: <SnapInstallation />,
  },
  {
    tab_name: "other",
    content: <OthersInstallation />,
  },
];
export default function Installation() {
  const [activeTab, setActiveTab] = useState("flatpak");
  return (
    <section id="installation" className="blueprint-grid bg-neutral-900/30">
      <div className="blueprint-col-sidebar min-h-[300px]">
        <div className="blueprint-marker -top-[3px] -right-[3px]" />
      </div>
      
      <div className="blueprint-col-content">
        <h2 className="text-4xl font-bold tracking-tight text-white/90 mb-12">Installation</h2>
        <div className="flex gap-10 mb-12 border-b border-white/5">
          {tabs.map((item) => {
             const isActive = item.tab_name === activeTab;
             return (
               <button
                 key={item.tab_name}
                 onClick={() => setActiveTab(item.tab_name)}
                 className={`pb-4 px-1 font-bold text-sm tracking-widest uppercase transition-all duration-300 relative ${
                   isActive 
                   ? "text-sky-400" 
                   : "text-neutral-500 hover:text-neutral-300"
                 }`}
               >
                 {item.tab_name}
                 {isActive && (
                   <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-sky-500 animate-in slide-in-from-left-full duration-300"></div>
                 )}
               </button>
             );
          })}
        </div>

        <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
          {tabs.find(t => t.tab_name === activeTab)?.content}
        </div>
      </div>
    </section>
  );
}
