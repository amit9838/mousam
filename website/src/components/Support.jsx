export default function Support() {
  return (
    <section className="md:px-6 px-2 pb-5 grid grid-cols-2 sm:grid-cols-12 my-auto bg-secondary h-contain text-white">
      <div className="col-span-1 md:block hidden h-[5rem] border-b-[1px] border-r-[1px] border-slate-400"></div>
      <div className="md:col-span-11 col-span-12  border-b-[1px] border-slate-400 flex items-end">
        <h2 className="mx-2  my-2 text-2xl ">Support</h2>
      </div>
      <div className="col-span-1 h-[15rem] border-r-[1px] border-slate-400 md:block hidden"></div>
      <div className="col-span-11 p-4 font-['ubuntu']">
        <p className="text-neutral-300">
          I hope you ❤️ Mousam , if you think it is worth supporting you can do
          so. Thanks!
        </p>

        <a href="https://www.buymeacoffee.com/ami9838">
          <img className="mt-4" src="https://img.buymeacoffee.com/button-api/?text=Buy me a coffee&emoji=☕&slug=ami9838&button_colour=FF5F5F&font_colour=ffffff&font_family=Comic&outline_colour=000000&coffee_colour=FFDD00" />
        </a>
      </div>
    </section>
  );
}
