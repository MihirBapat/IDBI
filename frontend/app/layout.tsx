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
  // suppressHydrationWarning: browser extensions (Dark Reader, Grammarly, …)
  // inject attributes on <html>/<body> before hydration; those mismatches are
  // harmless and outside our control.
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
