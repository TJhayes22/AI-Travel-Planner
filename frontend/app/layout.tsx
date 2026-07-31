import type { Metadata } from "next";
import "./globals.css";

// Placeholder system-font stack for now. Typography is a deliberate design
// decision to make later (per the frontend-design approach), not something
// to inherit from the create-next-app default.

export const metadata: Metadata = {
  title: "AI Travel Planner",
  description: "AI-powered destination discovery and trip planning.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col font-sans">{children}</body>
    </html>
  );
}