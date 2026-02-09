import type React from "react"
import "./globals.css"
import type { Metadata } from "next"
import { JetBrains_Mono } from "next/font/google"
import { Analytics } from "@vercel/analytics/next"
import { AuthProvider } from "@/components/auth-provider"
import { Toaster } from "@/components/ui/toaster"
import { Toaster as SonnerToaster } from "@/components/ui/sonner"

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
  display: "swap",
  preload: true,
})

export const metadata: Metadata = {
  title: "Agent47 - AI Automation Platform",
  description: "Automate your workflows with 47 specialized AI personnel",
  icons: {
    icon: "/icon.svg",
  },
  generator: 'v0.app',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="scroll-smooth" suppressHydrationWarning>
      <body className={jetbrainsMono.className}>
        <AuthProvider>
          {children}
          <Toaster />
          <SonnerToaster position="top-right" richColors />
          <Analytics />
        </AuthProvider>
      </body>
    </html>
  )
}
