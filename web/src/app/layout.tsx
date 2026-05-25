import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";
import { TooltipProvider } from "@/components/ui/tooltip";

const geist = Geist({ subsets: ["latin"], variable: "--font-geist-sans" });

export const metadata: Metadata = {
  title: "CriptoBrasil — Crypto Market Dashboard",
  description: "Monthly data on crypto asset operations in Brazil, sourced from Receita Federal.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning className={geist.variable}>
      <body className="min-h-screen bg-background text-foreground antialiased font-sans">
        <TooltipProvider>{children}</TooltipProvider>
      </body>
    </html>
  );
}
