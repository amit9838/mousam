import { useState } from "react";

const CopyToClipboard = ({ text }) => {
  const [copied, setCopied] = useState(false);

  const handleCopyClick = () => {
    navigator.clipboard
      .writeText(text)
      .then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 1500); // Reset copied state after 1.5 seconds
      })
      .catch((err) => console.error("Failed to copy:", err));
  };

  return (
    <div>
      <button
        onClick={handleCopyClick}
        className=" px-2 rounded py-[.1rem] text-neutral-300 hover:text-white"
      >
        {copied ? (
          <i className="fa-solid fa-check text-green-500"></i>
        ) : (
          <i className="fa-solid fa-copy "></i>
        )}
      </button>
    </div>
  );
};

export default CopyToClipboard;
