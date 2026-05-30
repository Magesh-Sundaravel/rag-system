/** @type {import('tailwindcss').Config} */
// Used for a production Tailwind CLI build. Local dev uses the Play CDN in index.html.
module.exports = {
  content: ["./index.html", "./src/**/*.js"],
  theme: { extend: {} },
  plugins: [],
};
