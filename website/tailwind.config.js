/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#131E27",
        secondary: "#222A31",
        dimWhite: "#BBBBBB",
        fullWhite: "#fff",
        card: "#A6A6A6",
        skyBlue: "#166EAE",
        dustOrange: "#C3A192",
        blueGrey: "#7B8389",
      },
    },
  },
  plugins: [],
};
