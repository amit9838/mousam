// src/ImageSlide.js
// eslint-disable-next-line react/prop-types
const ImageSlide = ({ path }) => {
  return (
    <div className="flex items-center justify-center w-full flex-shrink-0">
      <img src={path} alt="slide" className="sm:w-[50%] w-[90%] h-auto" />
    </div>
  );
};

export default ImageSlide;
