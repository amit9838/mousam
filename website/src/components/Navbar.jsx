import { useState } from "react";
import logo from "../assets/weather.png";
import Button from "./Button";

const MENU_ITEMS = ["home", "installation", "contribute", "about"];

export default function Navbar() {
  const [showNav, setshowNav] = useState(false);
  return (
    <>
      <nav className="p-6 grid gap-4 grid-cols-12 items-center">
        <div className="col-span-4 flex">
          <img src={logo} alt="logo" className="md:max-h-16 max-h-12" />
          <h1 className="my-auto md:text-[2.4rem] text-[1.6rem] mx-2 font-sans font-semibold">
            Mousam
          </h1>
        </div>
        <div className="col-span-8">
          <div className="bg-secondary md:block hidden  max-w-[40rem] float-end pr-1 pl-2 py-1 rounded-full">
            <ul className="list-none flex   md:gap-0 lg:gap-4 items-center justify-center">
              {MENU_ITEMS.map((item) => {
                return (
                  <li key={item}>
                    <Button
                      myStyle="rounded-full"
                      onClick={() => {
                        const element = document.getElementById(item);
                        element.scrollIntoView({
                          behavior: "smooth",
                        });
                      }}
                    >
                      {item.toUpperCase()}
                    </Button>
                  </li>
                );
              })}
              <li>
                <a
                  className="bg-black px-4 py-2 rounded-[6rem] hover:text-black hover:bg-white flex items-center"
                  href="https://github.com/amit9838/mousam" target="_blank"
                >
                  <i className="fa-brands fa-github mr-2"></i>
                  Github
                </a>
              </li>
            </ul>
          </div>
          {/* Phone */}
          <div className=" md:hidden block">
            <div
              className="flex float-right "
              onClick={() => setshowNav(!showNav)}
            >
              <i className="fa-solid fa-bars"></i>
            </div>
          </div>
        </div>
      </nav>
      {showNav && (
        <div
          onClick={(prev) => setshowNav(!prev)}
          className="fixed top-0 left-0 w-screen bg-gradient-to-b from-gray-900/0  via-gray-800 h-screen flex items-center justify-center z-10"
        >
          <div className="fixed bg-neutral-900 w-[18rem] h-[30rem] rounded-md opacity-100 z-40">
            <ul className="list-none  h-[30rem]  flex flex-col gap-10 items-center justify-center">
              {MENU_ITEMS.map((item) => {
                return (
                  <li key={item}>
                    <Button
                      myStyle="rounded-full"
                      onClick={() => {
                        const element = document.getElementById(item);
                        element.scrollIntoView({
                          behavior: "smooth",
                        });
                      }}
                    >
                      {item.toUpperCase()}
                    </Button>
                  </li>
                );
              })}
              <li>
                <a
                  className="bg-black px-4 py-2 rounded-[6rem] hover:text-black hover:bg-white flex items-center"
                  href="https://github.com/amit9838/mousam"
                >
                  <i className="fa-brands fa-github mr-2"></i>
                  Github
                </a>
              </li>
            </ul>
          </div>
        </div>
      )}
    </>
  );
}
