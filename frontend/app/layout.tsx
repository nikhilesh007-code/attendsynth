import type { Metadata } from "next";
import "./globals.css";
import { DatasetProvider } from "@/context/DatasetContext";
import { ThemeProvider } from "@/context/ThemeContext";
import { AppShell } from "@/components/layout/AppShell";

export const metadata: Metadata = {
  title: "AttendSynth AI – Synthetic Student Engagement Generator",
  description:
    "Production-grade synthetic student engagement platform, longitudinal time series analytics, early warning system, and Groq AI insights.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              try {
                var savedTheme = localStorage.getItem('attendsynth_theme');
                if (savedTheme === 'light') {
                  document.documentElement.classList.remove('dark');
                  document.documentElement.classList.add('light');
                } else {
                  document.documentElement.classList.add('dark');
                  document.documentElement.classList.remove('light');
                }
              } catch (e) {}
            `,
          }}
        />
      </head>
      <body className="antialiased selection:bg-emerald-500/30 selection:text-emerald-200">
        <ThemeProvider>
          <DatasetProvider>
            <AppShell>{children}</AppShell>
          </DatasetProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
