import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DhanSaarthi — IDBI Wealth Advisor",
  description:
    "Avatar-based, Account-Aggregator-powered behavioral wealth advisor for IDBI Bank.",
};

export const viewport = {
  themeColor: "#0a1310",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
