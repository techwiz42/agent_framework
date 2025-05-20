'use client';

import { MainLayout } from '@/components/layout/MainLayout';
import Link from 'next/link';

export default function FAQPage() {
  return (
    <MainLayout>
      <div className="max-w-4xl mx-auto prose">
        <h1>Frequently Asked Questions</h1>
        
        {/* Table of Contents */}
        <section className="mb-8 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <h2>Table of Contents</h2>
          <ul className="grid grid-cols-1 md:grid-cols-2 gap-2">
            <li><a href="#what-is-agent-framework" className="text-blue-600 hover:text-blue-800">What Is Agent Framework?</a></li>
            <li><a href="#how-different" className="text-blue-600 hover:text-blue-800">How is Agent Framework different from an AI chatbot?</a></li>
            <li><a href="#cost" className="text-blue-600 hover:text-blue-800">What does it cost to use Agent Framework?</a></li>
            <li><a href="#agents" className="text-blue-600 hover:text-blue-800">Agents and Capabilities</a></li>
            <li><a href="#interactions" className="text-blue-600 hover:text-blue-800">Interactions and Queries</a></li>
            <li><a href="#system" className="text-blue-600 hover:text-blue-800">System Functionality</a></li>
          </ul>
        </section>

        <section id="what-is-agent-framework" className="mb-8">
          <h2>What Is Agent Framework?</h2>
          <p>
            Think of Agent Framework as a consultancy in a box. Picture your organization sitting around a virtual conference 
            table meeting with a team of expert AI consultants. Agent Framework was built with owners of small to medium 
            sized businesses and organizations in mind. Now you can get the professional help and guidance you need 
            to grow your business without paying exorbitant consulting fees - you can try it for free.
          </p>
        </section>

        <section id="how-different" className="mb-8">
          <h2>How is Agent Framework different from using an AI chatbot?</h2>
          <p>
            There are over thirty AI agents available to work with you in Agent Framework. Each agent is highly tuned to 
            focus on one specific aspect of your business or organization. Some of the agents can perform tasks such as:
          </p>
          <ul>
            <li>Index your Google Drive or Microsoft OneDrive files</li>
            <li>Search the web and summarize the results</li>
            <li>Write code</li>
            <li>Read and summarize documents of all types</li>
            <li>Draft legal documents or review medical charts</li>
	    <li>...and many more</li>
          </ul>
          <p>
            You can direct your questions to all of these agents or only the ones you feel are relevant to the task at hand. 
            You get sharper focus and greater specificity. There&apos;s even an agent specifically trained to help you get 
            the most out of Agent Framework.
          </p>
        </section>

        <section id="cost" className="mb-8">
          <h2>What does it cost to use Agent Framework?</h2>
          <p>
            Using an AI agent consumes &quot;tokens&quot;. One token is roughly equivalent to a single word. When you register 
            for Agent Framework we give you 50,000 free tokens to get you started. When you&apos;ve used all your tokens, 
            you can buy more, either on a one-time as-needed basis or by subscription.
          </p>
        </section>

        <section id="agents" className="mb-8">
          <h2>Agents and Capabilities</h2>
          <h3>What are Agent Framework agents?</h3>
          <p>
            Agent Framework agents are components of the system, each crafted to handle particular domains, tasks, 
            or types of queries. They work independently or collaboratively based on user needs.
          </p>
          <h3>How do I choose the right agent?</h3>
          <p>
            Agent selection depends on the task requirement. You may use recommendation tools or consult 
            usage guides to identify which agent fits your specific needs.
          </p>
        </section>

        <section id="interactions" className="mb-8">
          <h2>Interactions and Queries</h2>
          <h3>What is the difference between direct querying and broadcasting?</h3>
          <p>
            Direct querying involves interacting with a specific agent for precise tasks, whereas broadcasting 
            queries allow multiple agents to respond, providing diverse insights.
          </p>
          <h3>How do I format my query?</h3>
          <p>
            Query formatting depends on whether you&apos;re addressing a specific agent or broadcasting. 
            Use appropriate syntax like &quot;@&quot; for particular agents.
          </p>
        </section>

        <section id="system" className="mb-8">
          <h2>System Functionality</h2>
          <h3>What is the MODERATOR function?</h3>
          <p>
            The MODERATOR manages interactions, maintaining order, resolving conflicts, and ensuring 
            effective communication between users and agents.
          </p>
          <h3>How do I escalate an issue with an agent?</h3>
          <p>
            For unresolved issues, use the MODERATOR to address conflicts or escalate to human support if necessary.
          </p>
        </section>

      </div>
      
      {/* Footer */}
      <footer className="bg-white border-t mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <p className="text-gray-500 mb-4 md:mb-0">
              © {new Date().getFullYear()} Agent Framework - All rights reserved
            </p>
            <div className="flex items-center space-x-4">
              <a 
                href="mailto:pete@cyberiad.ai"
                className="text-blue-600 hover:text-blue-800"
              >
                pete@cyberiad.ai
              </a>
              <div className="text-gray-400">|</div>
              <Link 
                href="/terms" 
                className="text-blue-600 hover:text-blue-800"
              >
                Terms of Service
              </Link>
              <div className="text-gray-400">|</div>
              <Link 
                href="/privacy" 
                className="text-blue-600 hover:text-blue-800"
              >
                Privacy Policy
              </Link>
              <div className="text-gray-400">|</div>
              <Link 
                href="/faq" 
                className="text-blue-600 hover:text-blue-800"
              >
                FAQ
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </MainLayout>
  );
}
