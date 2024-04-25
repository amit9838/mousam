import CopyToClipboard from "./CopyToClipboard";
export default function SnapInstallation() {
  return (
    <>
      <h3 className="text-dimWhite text-xl font-['Ubuntu']">
        Get it from Snapstore
      </h3>
      <div className="mx-2 my-4 font-['Ubuntu']">
        <a href="https://snapcraft.io/mousam">
          <img
            src="https://github.com/snapcore/snap-store-badges/blob/master/EN/%5BEN%5D-snap-store-black-uneditable.png?raw=true"
            alt="flathub"
            className="w-[12rem] my-2"
          />
        </a>
        <h4 className="text-dimWhite text-l mt-8">Or use terminal</h4>

        <p className="">Run the below command in terminal</p>
        <div className="flex items-center flex-row justify-between  sm:w-[40rem] bg-gray-700 sm:px-4 px-1 py-1 rounded-md">
              <div className="code">
                <code className="overflow-scroll">
                  sudo snap install mousam
                </code>
              </div>
              <CopyToClipboard text="sudo snap install mousam" />
        </div>
      </div>
    </>
  );
}
