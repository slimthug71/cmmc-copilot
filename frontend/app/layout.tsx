import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CMMC Pilot MVP",
  description: "CMMC Level 2 implementation statement and evidence checklist generator",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
