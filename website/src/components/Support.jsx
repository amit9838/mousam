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
        <a href="https://www.buymeacoffee.com/ami9838" rel="nofollow">
          <img
            src="https://camo.githubusercontent.com/cace41b0afc90c68d0207e2bd809ee121f9ff4f72ac032e8ced972aee7adbb23/68747470733a2f2f63646e2e6275796d6561636f666665652e636f6d2f627574746f6e732f76322f64656661756c742d79656c6c6f772e706e67"
            alt="Buy Me A Coffee"
            className="w-[14rem] my-4"
            data-canonical-src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png"
          />
        </a>
      </div>
    </section>
  );
}
