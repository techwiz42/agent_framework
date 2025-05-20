'use client';
import { MainLayout } from '@/components/layout/MainLayout';

export default function AIAgentsPage() {
  return (
    <MainLayout>
      <div className="max-w-4xl mx-auto prose">
        <h1>Understanding AI Agents</h1>
        
        <section className="mb-8">
          <h2>What is an AI Agent?</h2>
          <p>
            An AI agent is a specialized artificial intelligence system designed to perform specific tasks
            or provide expertise in particular domains. Unlike general AI chatbots, agents are equipped
            with focused knowledge, specific instructions, and defined roles that allow them to provide
            deep, contextual assistance in their areas of expertise.
          </p>
        </section>

        <section className="mb-8">
          <h2>The Agent Framework Multi-Agent System</h2>
          <p>
            Agent Framework&apos;s multi-agent system is a collaborative platform where multiple AI agents work
            together to provide comprehensive insights and solutions. Our system is unique because it:
          </p>
          <ul>
            <li>
              <strong>Enables Real-Time Collaboration:</strong> Multiple agents can participate in the same
              conversation, each contributing their specialized knowledge.
            </li>
            <li>
              <strong>Features Intelligent Routing:</strong> Our MODERATOR agent analyzes questions and
              automatically involves the most appropriate specialist agents.
            </li>
            <li>
              <strong>Maintains Context:</strong> Agents understand the full conversation history,
              enabling coherent and contextual responses.
            </li>
            <li>
              <strong>Supports Human Participation:</strong> Teams can collaborate with AI agents in
              secure, private conversations.
            </li>
          </ul>
        </section>

        <section className="mb-8">
          <h2>Our Specialized Agents</h2>
          <p>
            Agent Framework offers a diverse team of specialist agents, each with deep expertise in their
            domain:
          </p>
          <ul>
            <li>
              <strong>MODERATOR:</strong> Manages conversations, directs queries to appropriate specialists,
              and ensures productive dialogue.
            </li>
            <li>
              <strong>MEDICAL:</strong> Provides general medical information and healthcare insights
              (Note: Does not provide medical advice).
            </li>
            <li>
              <strong>LEGAL:</strong> Offers legal information and regulatory insights
              (Note: Does not provide legal advice).
            </li>
            <li>
              <strong>ACCOUNTING:</strong> Assists with financial analysis and accounting principles.
            </li>
            <li>
              <strong>ETHICIST:</strong> Analyzes ethical implications and moral considerations.
            </li>
            <li>
              <strong>ENVIRONMENTAL:</strong> Provides expertise on sustainability and environmental impact.
            </li>
            <li>
              <strong>FINANCE:</strong> Offers financial analysis and market insights.
            </li>
            <li>
              <strong>BUSINESS:</strong> Assists with business strategy and operations.
            </li>
            <li>
              <strong>BIOINFORMATICS:</strong> Specializes in computational biology and genomic analysis.
            </li>
            <li>
              <strong>TECHNOLOGIST:</strong> Provides expertise in software, systems, and technology.
            </li>
          </ul>
        </section>

        <section className="mb-8">
          <h2>How It Works</h2>
          <p>
            The Agent Framework platform facilitates seamless interaction between humans and AI agents:
          </p>
          <ol>
            <li>
              Create a secure conversation and invite team members.
            </li>
            <li>
              Select which specialist agents you want available in your conversation.
            </li>
            <li>
              Ask questions or discuss topics - our MODERATOR agent will automatically
              involve the most appropriate specialists.
            </li>
            <li>
              Directly mention specific agents (e.g., &quot;@LEGAL&quot;) when you want their
              particular expertise.
            </li>
            <li>
              Enable privacy mode when needed to prevent message storage.
            </li>
          </ol>
        </section>

        <section className="mb-8">
          <h2>Use Cases</h2>
          <p>
            Our multi-agent system is particularly valuable for:
          </p>
          <ul>
            <li>
              Cross-functional team discussions requiring multiple types of expertise
            </li>
            <li>
              Complex decision-making processes needing various specialist inputs
            </li>
            <li>
              Research and analysis involving multiple domains
            </li>
            <li>
              Project planning requiring diverse expert perspectives
            </li>
            <li>
              Risk assessment across different dimensions (legal, financial, ethical, etc.)
            </li>
          </ul>
        </section>

        <section className="mb-8">
          <h2>Security and Privacy</h2>
          <p>
            Agent Framework prioritizes the security and privacy of your conversations:
          </p>
          <ul>
            <li>
              All conversations are encrypted and secure
            </li>
            <li>
              Privacy mode available to prevent message storage
            </li>
            <li>
              Token-based access control for all participants
            </li>
            <li>
              Detailed privacy policy and terms of service available
            </li>
          </ul>
        </section>

        <section className="mb-8">
          <h2>Get Started</h2>
          <p>
            Ready to experience the power of multi-agent collaboration? Register for an account
            or contact us to discuss custom implementations for your organization&apos;s specific needs.
          </p>
        </section>
      </div>
    </MainLayout>
  );
}
