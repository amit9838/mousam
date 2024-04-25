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
    <section
      id="installation"
      className="md:p-6 py-6 px-2 grid grid-cols-12 my-auto bg-primary h-contain text-white"
    >
      <div className="col-span-2 h-[5rem] border-b-[1px] border-r-[1px] border-slate-400 relative md:block hidden">
        <h2 className="mx-2  my-2 absolute bottom-0 right-0 text-xl ">
          Installation
        </h2>
      </div>
      <div className="md:col-span-10 col-span-12 border-b-[1px] border-slate-400">
        <h2 className="mx-2 mb-4 text-xl md:hidden block ">Installation</h2>
        <div className="flex items-center justify-center border-t-[1px] border-slate-400 md:hidden">
          {tabs.map((item) => {
            let myStyle =
              "bg-secondary hover:bg-slate-600 py-2 w-auto px-8";
            if (item.tab_name === activeTab) {
              myStyle =
                "bg-slate-500 hover:bg-slate-600 py-2 w-auto px-8";
            }
            return (
              <Button
                key={item.tab_name}
                myStyle={myStyle}
                onClick={() => setActiveTab(item.tab_name)}
              >
                {item.tab_name}
              </Button>
            );
          })}
        </div>
      </div>
      <div className="col-span-2 md:block hidden h-[30rem] border-r-[1px] border-slate-400">
        <div className="md:flex items-end flex-col hidden">
          {tabs.map((item) => {
            let myStyle =
              "bg-secondary hover:bg-slate-600 py-2 w-40 border-b-[1px]";
            if (item.tab_name === activeTab) {
              myStyle =
                "bg-slate-500 hover:bg-slate-600 py-2 w-40 border-b-[1px]";
            }
            return (
              <Button
                key={item.tab_name}
                myStyle={myStyle}
                onClick={() => setActiveTab(item.tab_name)}
              >
                {item.tab_name}
              </Button>
            );
          })}
        </div>
      </div>
      <div className="md:col-span-10 col-span-12  m-6">
        {tabs.map((item) => {
          return (
            item.tab_name === activeTab && (
              <div key={item.tab_name}>{item.content}</div>
            )
          );
        })}
      </div>
    </section>
  );
}
