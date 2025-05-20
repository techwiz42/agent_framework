'use client'
import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { AgentFrameworkLogo, RobotLogo } from '@/components/ui/logo';
import dynamic from 'next/dynamic';
import Script from 'next/script';
import Link from 'next/link';

// Dynamically load the AnonymousChatWidget to avoid SSR issues
const AnonymousChatWidget = dynamic(
  () => import('@/components/chat/AnonymousChatWidget'),
  { 
    ssr: false,
    loading: () => null 
  }
);

export default function LandingPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [showChatWidget, setShowChatWidget] = useState(false);
  
  // Only show chat widget after page has loaded in the browser
  useEffect(() => {
    setShowChatWidget(true);
  }, []);

  // Structured data for SEO
  const structuredData = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "Agent Framework",
    "applicationCategory": "BusinessApplication",
    "operatingSystem": "Web",
    "offers": {
      "@type": "Offer",
      "price": "0",
      "priceCurrency": "USD"
    },
    "description": "Agent Framework - a platform for AI agent collaboration"
  };

  return (
    <>
      <Script id="structured-data" type="application/ld+json">
        {JSON.stringify(structuredData)}
      </Script>
      
      <div className="min-h-screen flex flex-col">
        {/* Navigation */}
        <header>
          <nav className="bg-white shadow-sm" aria-label="Main navigation">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
              <div className="flex justify-between items-center">
                <div className="text-2xl font-bold text-blue-600" aria-label="Agent Framework logo">Agent Framework</div>
                <div className="flex gap-4">
                  {!user ? (
                    <>
                      <Button variant="ghost" onClick={() => router.push('/login')}>Login</Button>
                      <Button variant="default" onClick={() => router.push('/register')}>Register</Button>
                    </>
                  ) : (
                    <>
                      <Button variant="outline" onClick={() => router.push('/conversations')}>My Conversations</Button>
                      {user.role === 'admin' && (
                        <>
                          <Button variant="outline" onClick={() => router.push('/admin/status')}>System Status</Button>
                          <Button variant="outline" onClick={() => router.push('/admin/health')}>System Health</Button>
                        </>
                      )}
                    </>
                  )}
                </div>
              </div>
            </div>
          </nav>
        </header>

        {/* Simple Hero Section */}
        <main className="flex-grow">
          <section aria-labelledby="hero-heading" className="bg-white py-12">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="text-center">
                <h1 id="hero-heading" className="text-5xl font-bold text-gray-900 mb-6">
                  Agent Framework
                </h1>
                <div className="flex justify-center mb-8">
                  <div className="rounded-lg p-4 border-2 border-blue-500 shadow-md bg-white">
                    <RobotLogo size={180} className="text-blue-600" aria-hidden="true" />
                  </div>
                </div>
                <Button
                  size="lg"
                  className="bg-blue-600 hover:bg-blue-700 text-white mb-2"
                  onClick={() => router.push(user ? '/conversations' : '/register')}
                >
                  {user ? 'Go to Conversations' : 'Get Started'}
                </Button>
              </div>
            </div>
          </section>
        </main>

        {/* Footer */}
        <footer className="bg-white border-t">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="flex flex-col md:flex-row justify-between items-center">
              <p className="text-gray-500 mb-4 md:mb-0">
                © {new Date().getFullYear()} Agent Framework
              </p>
              <nav aria-label="Footer navigation">
                <ul className="flex items-center space-x-4">
                  <li>
                    <Link href="/terms" className="text-blue-600 hover:text-blue-800">Terms of Service</Link>
                  </li>
                  <li className="text-gray-400">|</li>
                  <li>
                    <Link href="/privacy" className="text-blue-600 hover:text-blue-800">Privacy Policy</Link>
                  </li>
                </ul>
              </nav>
            </div>
          </div>
        </footer>
        
        {/* Anonymous Chat Widget */}
        {showChatWidget && <AnonymousChatWidget />}
      </div>
    </>
  );
}
