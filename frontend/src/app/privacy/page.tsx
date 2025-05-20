'use client';

import { MainLayout } from '@/components/layout/MainLayout';

export default function PrivacyPage() {
  return (
    <MainLayout>
      <div className="max-w-4xl mx-auto prose">
        <h1>Privacy Policy</h1>
        <p>Last updated: January 12, 2025</p>

        <section className="mb-8">
          <h2>Introduction</h2>
          <p>
            Agent Framework (&quot;we&quot;, &quot;our&quot;, or &quot;us&quot;) respects your privacy and is committed to protecting your personal data. 
            This privacy policy will inform you about how we look after your personal data when you visit our website 
            and tell you about your privacy rights and how the law protects you.
          </p>
        </section>

        <section className="mb-8">
          <h2>Data We Collect</h2>
          <p>We collect and process the following types of personal data:</p>
          <ul>
            <li>Email address</li>
            <li>Username</li>
            <li>Usage data and analytics</li>
            <li>If the &quot;privacy&quot; feature is enabled, we do not save usage data</li>
            <li>Payment information (processed securely through Stripe)</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2>How We Use Your Data</h2>
          <p>We use your personal data for the following purposes:</p>
          <ul>
            <li>To provide and maintain our service</li>
            <li>To notify you about changes to our service</li>
            <li>To provide customer support</li>
            <li>To process your payments</li>
            <li>To monitor usage of our service</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2>Data Security</h2>
          <p>
            We implement appropriate security measures to protect your personal data against unauthorized access, 
            alteration, disclosure, or destruction. Your payment information is handled securely by Stripe, 
            our payment processor.
          </p>
        </section>

        <section className="mb-8">
          <h2>Your Rights</h2>
          <p>You have the right to:</p>
          <ul>
            <li>Access your personal data</li>
            <li>Correct inaccurate data</li>
            <li>Delete your data</li>
            <li>Object to processing of your data</li>
            <li>Request transfer of your data</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2>Contact Us</h2>
          <p>
            For any questions about this privacy policy or our privacy practices, please contact us at{' '}
            <a href="mailto:pete@agentframework.ai" className="text-blue-600 hover:text-blue-800">
              pete@agentframework.ai
            </a>
          </p>
        </section>
      </div>
    </MainLayout>
  );
}
