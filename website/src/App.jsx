import Hero from "./components/Hero.jsx";
import Features from "./components/Features.jsx";
import Installation from "./components/Installation.jsx";
import Contribute from "./components/Contribute.jsx";
import About from "./components/About.jsx";
import Support from "./components/Support.jsx";
import Footer from "./components/Footer.jsx";
import Carousel from "./components/Carousal.jsx";
function App() {
  return (
    <>
      <Hero />
      <Carousel/>
      <Features />
      <Installation/>
      <Contribute/>
      <About/>
      <Support/>
      <Footer/>
    </>
  );
}

export default App;
