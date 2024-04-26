const FEATURES = [
  {
    icon: "fa-compass-drafting",
    text: "Beautifully Designed UI",
  },
  {
    icon: "fa-code",
    text: "Open Source and free to use",
  },
  {
    icon: "fa-chart-line",
    text: "Utilizes graphs and bars to show various attributes",
  },
  {
    icon: "fa-globe",
    text: "Available in multiple languages",
  },
  {
    icon: "fa-heart",
    text: "More than 30k users enjoying the app",
  },
];

export default function Features() {
  return (
    <section className="md:p-6 px-1 py-2 grid grid-cols-12 my-auto bg-secondary h-contain text-white">
      <div className="col-span-1 h-[5rem] border-b-[1px]  border-r-[1px] border-slate-400 "></div>
      <div className="col-span-11 border-b-[1px]  border-slate-400 relative ">
        <h2 className="mx-2 my-2 absolute bottom-0 text-xl">Features</h2>
      </div>

      <div className="col-span-1  border-r-[1px] border-slate-400"></div>
      <div className="col-span-11 flex md:flex-row flex-col  justify-between md:items-start items-center ">
        {FEATURES.map((item) => {
          let iconClass = `fa-solid ${item.icon} md:text-5xl text-4xl text-dimWhite`;
          return (
            <div
              className="w-[70vw] flex items-center flex-col md:my-10 my-4"
              key={item.icon}
            >
              <i className={iconClass}></i>
              <p className="text-center mt-5 md:text-[1rem] text-[.9rem]">{item.text}</p>
            </div>
          );
        })}
      </div>
    </section>
  );
}
