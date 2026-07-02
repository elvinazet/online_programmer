import "./globals.css";
import "highlight.js/styles/github-dark.css";
import type { Metadata } from "next";

import Nav from "@/components/Nav";

import Providers from "./providers";

export const metadata: Metadata = {
  title: "Online Programmer",
  description: "Онлайн-школа программирования: C++ и Python",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body>
        <Providers>
          <Nav />
          <main className="mx-auto max-w-4xl px-6 py-6">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
