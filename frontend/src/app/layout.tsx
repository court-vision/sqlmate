import type { Metadata } from "next";
import { Analytics } from "@vercel/analytics/next"
import { AuthProvider } from "@/contexts/authContext";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";

export const metadata: Metadata = {
  title: "SQLMate",
  description: "Visual SQL Editor",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="isolate">
        <AuthProvider>{children}</AuthProvider>
        <Toaster />
        <Analytics />
      </body>
    </html>
  );
}
