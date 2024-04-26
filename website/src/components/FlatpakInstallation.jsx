import CopyToClipboard from "./CopyToClipboard";
export default function FlatpakInstallation() {
  return (
    <>
      <h3 className="text-dimWhite text-xl font-['Ubuntu']">
        Get it from flathub
      </h3>
      <div className="mx-2 my-4 font-['Ubuntu']">
        <a href="https://flathub.org/apps/io.github.amit9838.mousam">
          <img
            src="https://dl.flathub.org/assets/badges/flathub-badge-en.png"
            alt="flathub"
            className="w-[12rem] my-2"
          />
        </a>
        <h4 className="text-dimWhite text-l mt-8">Or use terminal</h4>
        <ol className="list-ouside list-disc mx-5">
          <li>
            Install flathub if not installed
            <p className="mb-4 mt-1">
              <a
                className="bg-gray-700 hover:bg-gray-600 px-2 py-1 rounded-md"
                href="https://flathub.org/setup"
              >
                See Instruction{" "}
                <i className="fa-solid fa-circle-chevron-right"></i>
              </a>
            </p>
          </li>
          <li>
            <p className="">Now run the below command in terminal</p>
            <div className="flex items-center flex-row justify-between  sm:max-w-[40rem] bg-gray-700 sm:px-4 px-1 py-1 rounded-md">
              <div className="code">
                <code className="overflow-scroll">
                  flatpak install io.github.amit9838.mousam
                </code>
              </div>
              <CopyToClipboard text="flatpak install io.github.amit9838.mousam" />
            </div>
          </li>
        </ol>
      </div>
    </>
  );
}
