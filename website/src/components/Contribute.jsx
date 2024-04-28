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
    <section
      id="contribute"
      className="md:px-6 px-2 pt-6 grid grid-cols-12 my-auto bg-secondary h-contain text-white "
    >
      <div className="col-span-1  border-b-[1px] border-r-[1px] border-slate-400 md:block hidden"></div>
      <div className="md:col-span-11 col-span-12  border-b-[1px] border-slate-400 flex items-end">
        <h2 className="mx-2  my-2 text-2xl ">Contribute</h2>
      </div>
      <div className="col-span-1 border-r-[1px] border-slate-400 md:block hidden"></div>
      <div className="md:col-span-11 col-span-12  p-3 font-['ubuntu']">
        <p className=" text-neutral-300 bg">
          Thanks to all the contributors have helped in the development project
          so that open-source community can enjoy best features in the market.
        </p>
        <div className="my-3 mx-2">
          <a href="https://github.com/amit9838/mousam/graphs/contributors">
            <img
              className="sm:block hidden"
              src="https://contrib.rocks/image?repo=amit9838/mousam&columns=12"
            />
            <img
              className="sm:hidden block"
              src="https://contrib.rocks/image?repo=amit9838/mousam&columns=6"
            />
          </a>
        </div>

        <div className="mt-10">
          <h4 className="text-xl text-neutral-100 bg">
            You can also contribute if you wish to, here are some ways
          </h4>

          {askContribution.map((item) => (
            <div
              key={item.icon}
              className="flex items-center my-4 hover:bg-slate-500 text-neutral-300 hover:text-white py-1 rounded-md"
            >
              <div className="mx-2 text-neutral-200 bg-slate-600  w-10 h-10 flex items-center justify-center rounded-full">
                <i className={item.icon}></i>
              </div>
              <a className=" " href={item.link}>
                {item.text}
                <i className="fa-solid fa-square-arrow-up-right mx-2 text-[.9rem] text-neutral-300"></i>
              </a>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
