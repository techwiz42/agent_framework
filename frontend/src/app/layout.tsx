// src/app/layout.tsx
import './globals.css'
import { ClientLayout } from '@/components/layout/ClientLayout'
import { Toaster } from "@/components/ui/toaster"
import { Inter } from 'next/font/google'
import type { Metadata, Viewport } from 'next'

const inter = Inter({ subsets: ['latin'] })

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
}

export const metadata: Metadata = {
  title: 'Agent Framework',
  description: 'Agent Framework - a platform for AI agent collaboration',
  keywords: 'AI agents, agent framework, collaboration, AI platform',
  authors: [{ name: 'Agent Framework' }],
  creator: 'Agent Framework',
  publisher: 'Agent Framework',
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  icons: {
    icon: '/favicon.ico',
    apple: '/icons/apple-touch-icon.png',
    shortcut: '/icons/favicon-32x32.png',
  },
  category: 'AI Tools',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={inter.className}>
      <body>
        <ClientLayout>
          {children}
        </ClientLayout>
        <Toaster />
      </body>
    </html>
  );
}
