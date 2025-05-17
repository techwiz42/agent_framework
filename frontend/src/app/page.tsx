'use client'
import React from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Users, Bot, MessageCircle, Search, FileText, BarChart3 } from 'lucide-react';
import Link from 'next/link';
import Logo from '@/components/ui/logo/Logo';

export default function LandingPage() {
  const router = useRouter();
  const { user } = useAuth();

  return (
    <div className="min-h-screen flex flex-col">
      {/* Navigation */}
      <header>
        <nav className="bg-white shadow-sm" aria-label="Main navigation">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex justify-between items-center">
              <div className="flex items-center text-2xl font-bold text-blue-600" aria-label="Agent Framework logo">
                <Logo size={32} className="mr-2 text-blue-600" />
                Agent Framework
              </div>
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
                      <Button variant="outline" onClick={() => router.push('/admin/dashboard')}>Admin</Button>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <main className="flex-grow">
        <section aria-labelledby="hero-heading" className="bg-white py-12">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              <h1 id="hero-heading" className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
                Multi-Agent Collaborative Workspace
              </h1>
              <div className="flex justify-center mb-8">
                <Logo size={96} className="text-blue-600" aria-hidden="true" />
              </div>
              <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-8">
                A flexible platform for business collaboration featuring specialized AI agents that work together to solve your business challenges.
              </p>
              <Button
                size="lg"
                className="bg-blue-600 hover:bg-blue-700 text-white mb-2"
                onClick={() => router.push(user ? '/conversations' : '/register')}
              >
                {user ? 'Go to Workspace' : 'Get Started'}
              </Button>
            </div>
          </div>
        </section>

        {/* Agents Section */}
        <section aria-labelledby="agents-heading" className="bg-gray-50 py-12">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-10">
              <h2 id="agents-heading" className="text-3xl font-bold mb-4">Specialized AI Agents</h2>
              <p className="text-lg text-gray-600 mb-8">
                Our platform features these specialized agents to assist with your business needs:
              </p>
            </div>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                  <Bot className="w-6 h-6 text-blue-600" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Business Advisor</h3>
                <p className="text-gray-600">
                  Provides business strategy and management advice for decision-making and planning.
                </p>
              </div>
              
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                  <BarChart3 className="w-6 h-6 text-blue-600" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Business Intelligence</h3>
                <p className="text-gray-600">
                  Analyzes business data and provides metric insights to track performance.
                </p>
              </div>
              
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                  <BarChart3 className="w-6 h-6 text-blue-600" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Data Analysis</h3>
                <p className="text-gray-600">
                  Processes and interprets complex datasets to uncover patterns and insights.
                </p>
              </div>
              
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                  <Search className="w-6 h-6 text-blue-600" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Web Search</h3>
                <p className="text-gray-600">
                  Searches the web for relevant information to answer your questions.
                </p>
              </div>
              
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                  <FileText className="w-6 h-6 text-blue-600" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Document Search</h3>
                <p className="text-gray-600">
                  Searches and analyzes your uploaded documents to extract insights.
                </p>
              </div>
              
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                  <Users className="w-6 h-6 text-blue-600" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Collaboration</h3>
                <p className="text-gray-600">
                  Work with human teammates and specialized AI agents in a unified workspace.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Integration Section */}
        <section className="bg-white py-12">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold mb-4">External Integrations</h2>
              <p className="text-lg text-gray-600 mb-4">
                Connect with your favorite tools and services
              </p>
            </div>
            <div className="grid sm:grid-cols-2 gap-8">
              <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
                <h3 className="text-xl font-semibold mb-3">Google Drive</h3>
                <p className="text-gray-600 mb-4">
                  Import and analyze documents directly from your Google Drive.
                </p>
              </div>
              <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
                <h3 className="text-xl font-semibold mb-3">OneDrive</h3>
                <p className="text-gray-600 mb-4">
                  Seamlessly access and process files stored in Microsoft OneDrive.
                </p>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center mb-4 md:mb-0">
              <Logo size={24} className="mr-2 text-blue-600" />
              <p className="text-gray-500">
                © {new Date().getFullYear()} Agent Framework - All rights reserved
              </p>
            </div>
            <nav aria-label="Footer navigation">
              <ul className="flex items-center space-x-4">
                <li>
                  <Link href="/terms" className="text-blue-600 hover:text-blue-800">Terms</Link>
                </li>
                <li>
                  <Link href="/privacy" className="text-blue-600 hover:text-blue-800">Privacy</Link>
                </li>
                <li>
                  <Link href="/contact" className="text-blue-600 hover:text-blue-800">Contact</Link>
                </li>
              </ul>
            </nav>
          </div>
        </div>
      </footer>
    </div>
  );
}