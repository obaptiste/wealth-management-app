// tailwind.config.js
/** @type {import('tailwindcss').Config} */
module.exports = {
    // Crucial: Enable class-based dark mode to work with next-themes
    darkMode: "class",
    // Specify files where Tailwind should look for classes
    content: [
      "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
      "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
      "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
      "./src/styles/**/*.css", // Include CSS files if using @apply
    ],
    // You can extend the theme here if needed, but start minimal
    theme: {
      extend: {
        // Example: If you want to make Geist fonts easily available
        // as Tailwind utility classes (e.g., `font-sans`, `font-mono`),
        // uncomment the following lines. Otherwise, Chakra handles fonts.
        // fontFamily: {
        //   sans: ['var(--font-geist-sans)', 'sans-serif'],
        //   mono: ['var(--font-geist-mono)', 'monospace'],
        // },
      },
    },
    plugins: [],
  };
  