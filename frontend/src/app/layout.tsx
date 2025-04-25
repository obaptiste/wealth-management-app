import React, { FC, ReactNode } from "react";
import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/Providers";
interface LayoutProps {
  children: ReactNode;
}

export const metadata: Metadata = {
  title: "OpenBank Wealth Management",
  description: "Manage your investment portfolio with ease",
};

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export default function RootLayout({ children }: LayoutProps) {
  return (
    <html lang="en">
    <body
    className={`${geistSans.variable} ${geistMono.variable} antialiased`}
  >
    <div className="flex min-h-screen bg-gray-900 text-white">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <TopBar />
        <main className="flex-1 p-6 overflow-y-auto">
          <Providers>{children}</Providers></main>
      </div>
    </div>
    </body>
    </html>
  );
};

interface NavItemProps {
  label: string;
}

const navItems: NavItemProps[] = [
  { label: "Dashboard" },
  { label: "My Portfolio" },
  { label: "Insights" },
  { label: "Transactions" },
  { label: "Goals" },
  { label: "Budget Tracker" },
  { label: "Settings" },
  { label: "Admin Panel" },
];

export const Sidebar: FC = () => (
  <aside className="w-64 bg-gray-800 p-4">
    <div className="text-2xl font-bold mb-6">Wealth Management</div>
    <nav className="space-y-4">
      {navItems.map(({ label }) => (
        <a
          key={label}
          href={`/${label.toLowerCase().replace(/ /g, "-")}`}
          className="block hover:text-teal-400"
        >
          {label}
        </a>
      ))}
    </nav>
  </aside>
);

export const TopBar: FC = () => (
  <header className="h-16 bg-gray-850 border-b border-gray-700 flex items-center justify-between px-6">
    <input
      type="text"
      placeholder="Search..."
      className="bg-gray-700 text-white px-4 py-2 rounded-md w-1/3"
    />
    <div className="flex items-center space-x-4">
      <button className="hover:text-teal-400">🔔</button>
      <div className="w-8 h-8 bg-gray-600 rounded-full" />
    </div>
  </header>
);





