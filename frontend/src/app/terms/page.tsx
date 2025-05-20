'use client';

import { MainLayout } from '@/components/layout/MainLayout';

export default function TermsPage() {
  return (
    <MainLayout>
      <div className="max-w-4xl mx-auto prose">
        <h1>Terms of Service</h1>
        <p>Last updated: January 12, 2025</p>

        <section className="mb-8">
          <h2>1. Introduction</h2>
          <p>
            These Terms of Service govern your use of Agent Framework and the AI agent services we provide. 
            By using our service, you agree to these terms. Please read them carefully.
          </p>
        </section>

        <section className="mb-8">
          <h2>2. Using Our Services</h2>
          <p>You must follow these terms and any applicable policies to use our services:</p>
          <ul>
            <li>You must be 18 years or older to use our services</li>
            <li>You must maintain accurate account information</li>
            <li>You are responsible for maintaining account security</li>
            <li>You must not misuse our services or help anyone else do so</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2>3. Payment Terms</h2>
          <p>
            We use Stripe to process payments. By purchasing our services, you agree to:
          </p>
          <ul>
            <li>Provide accurate billing information</li>
            <li>Pay all charges at the prices in effect when the charges were incurred</li>
            <li>Pay any applicable taxes</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2>4. Tokens and Credits</h2>
          <p>
            Our service operates using tokens. Please note:
          </p>
          <ul>
            <li>Tokens are non-refundable once used</li>
            <li>Subscription tokens are granted monthly</li>
            <li>Unused subscription tokens roll over to the next month</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2>5. Cancellation and Termination</h2>
          <p>
            You can cancel your subscription at any time through your account settings or by contacting support. 
            Upon cancellation:
          </p>
          <ul>
            <li>Your subscription will continue until the end of the current billing period</li>
            <li>No refunds will be provided for unused tokens in the billing period</li>
            <li>You retain access to any remaining tokens</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2>6. Service Availability and Updates</h2>
          <p>
            While we strive for 100% uptime, we cannot guarantee uninterrupted access to our services. 
            We reserve the right to modify, suspend, or discontinue any part of our services at any time.
          </p>
        </section>

        <section className="mb-8">
          <h2>7. Intellectual Property</h2>
          <p>
            Users retain ownership of their content. By using our service, you grant us a license to use, 
            store, and process your content to provide our services.
          </p>
        </section>

        <section className="mb-8">
          <h2>8. Limitation of Liability</h2>
          <p>
            Our services are provided &quot;as is&quot; without any warranties. We are not liable for any indirect, 
            incidental, special, consequential, or punitive damages.
          </p>
        </section>

        <section className="mb-8">
          <h2>9. Changes to Terms</h2>
          <p>
            We may modify these terms at any time. We&apos;ll notify you of significant changes. 
            Continued use of our services constitutes acceptance of the modified terms.
          </p>
        </section>

        <section className="mb-8">
          <h2>10. Contact</h2>
          <p>
            For any questions about these terms, please contact us at{' '}
            <a href="mailto:pete@cyberiad.ai" className="text-blue-600 hover:text-blue-800">
              pete@cyberiad.ai
            </a>
          </p>
        </section>
      </div>
    </MainLayout>
  );
}
