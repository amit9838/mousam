export default function About() {
  let code_style = "bg-primary px-1 rounded-sm";
  return (
    <section
      id="about"
      className="md:px-6  px-2 grid grid-cols-12  bg-secondary h-contain text-white"
    >
      <div className="col-span-1  h-[5rem] border-b-[1px] border-r-[1px] border-slate-400 md:block hidden"></div>
      <div className="md:col-span-11 col-span-12  md:mt-0 mt-6 border-b-[1px] border-slate-400 flex items-end">
        <h2 className="mx-2  my-2 text-2xl ">About</h2>
      </div>
      <div className="col-span-1 border-r-[1px] border-slate-400 md:block hidden"></div>
      <div className="md:col-span-11 col-span-12 p-4 text-neutral-300 font-sans max-w-[90%]">
        <p>
          Mousam is a sleek desktop-weather application offering real-time
          weather updates and forecasts for the next{" "}
          <code className={code_style}>24 hours</code> and{" "}
          <code className={code_style}>7 days</code> .It utilizes graphs and
          bars to visually represent weather conditions and supports both{" "}
          <code className={code_style}>imperial</code> and{" "}
          <code className={code_style}> metric </code> units for user
          convenience.
        </p>
        <p className="my-2">
          Developed with <code className={code_style}> Python</code> and{" "}
          <code className={code_style}>GTK4</code> using{" "}
          <code className={code_style}>Libadwaita</code> and{" "}
          <code className={code_style}>Cairo</code> for graphics, Mousam fetches
          weather data from the{" "}
          <code className={code_style}>Open-Meteo API</code> , ensuring accurate
          and timely information.
        </p>
        <h4 className="text-neutral-200 mt-8 font-bold">About me</h4>
        <p className="my-1 ">
          I’m Amit, and I initiated this project as part of my ongoing
          exploration of Gtk with Python. It’s great to see Mousam’s success and
          positive feedback. It motivates me to keep working on the project.
        </p>
        <p>
          I commend the collaborative spirit inherent in open source, where
          individuals can freely interact, exchange innovative ideas, and
          contribute to projects collectively.
        </p>
        <p>
          Let's build something amazing together! Join the open source community
          today. Whether you're starting your own project or contributing to an
          existing one, it's a fantastic way to learn and grow.
        </p>
        Let's code together!

        {/* Developer Card */}
        <div className="max-w-[24rem] w-full bg-gray-700 hover:bg-gray-600 rounded-md flex items-center p-4 my-6">
          <img
            src="https://avatars.githubusercontent.com/u/61614402?v=4"
            alt=""
            className=" h-16 w-16 rounded-full"
          />
          <div className="detail mx-4 text-white text-['ubuntu']">
            <h3 className="text-xl font-['ubuntu']">Amit Chaudhary</h3>
            <p className="text-[.8rem] text-neutral-300">Software Engineer</p>
            <div className="social flex gap-2">
              <a
                href="https://github.com/amit9838"
                target="_blank"
                rel="noreferrer"
                className=" hover:bg-slate-700 rounded-md px-1"
              >
                <i className="fa-brands fa-github"></i>
              </a>
              <a
                href="https://www.linkedin.com/in/amit-chaudhary-2b8b22199/"
                target="_blank"
                rel="noreferrer"
                className=" hover:bg-slate-700 rounded-md px-1"
              >
                <i className="fa-brands fa-linkedin"></i>
              </a>
              <a
                href="https://twitter.com/AMIT0539"
                target="_blank"
                rel="noreferrer"
                className=" hover:bg-slate-700 rounded-md px-1"
              >
                <i className="fa-brands fa-square-x-twitter"></i>
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
