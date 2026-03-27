import React, { ReactNode } from "react";
import type { Metadata } from "next";
import { Syne, Work_Sans, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/Providers";
interface LayoutProps {
  children: ReactNode;
}

export const metadata: Metadata = {
  title: "Wealth Pro - Financial Management Platform",
  description: "Comprehensive wealth management with portfolio tracking, pension planning, and insurance recommendations",
};

// Distinctive font pairing
const syneFont = Syne({
  variable: "--font-syne",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
});

const workSansFont = Work_Sans({
  variable: "--font-work-sans",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
});

const jetBrainsMonoFont = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

export default function RootLayout({ children }: LayoutProps) {
  return (
    <html lang="en" suppressHydrationWarning>
    <body
    className={`${syneFont.variable} ${workSansFont.variable} ${jetBrainsMonoFont.variable} antialiased`}
    suppressHydrationWarning
  >
    <Providers>{children}</Providers>
    </body>
    </html>
  );
};





