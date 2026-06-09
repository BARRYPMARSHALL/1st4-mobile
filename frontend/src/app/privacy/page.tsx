export default function PrivacyPage() {
  return (
    <section className="flex-1 bg-white px-4 py-16 sm:py-24">
      <div className="mx-auto max-w-3xl prose prose-sm sm:prose">
        <h1 className="text-3xl font-bold text-gray-900">Privacy Policy</h1>
        <p className="text-sm text-gray-500">Last updated: June 2026</p>

        <h2 className="mt-8 text-xl font-semibold text-gray-900">1. Information We Collect</h2>
        <p className="text-sm text-gray-600">
          We collect information you provide directly: name, email, company name, phone number, and
          invoice data you upload for analysis. We also collect technical data such as IP address,
          browser type, and usage patterns to improve our service.
        </p>

        <h2 className="mt-6 text-xl font-semibold text-gray-900">2. How We Use Your Data</h2>
        <p className="text-sm text-gray-600">
          Your invoice data is processed solely for the purpose of detecting overcharges and
          generating audit reports. We never share raw invoice data with third parties. Aggregated,
          anonymised statistics may be used for product improvement.
        </p>

        <h2 className="mt-6 text-xl font-semibold text-gray-900">3. Data Security</h2>
        <p className="text-sm text-gray-600">
          All data is encrypted at rest (AES-256) and in transit (TLS 1.3). Our infrastructure
          runs in isolated environments with strict access controls. We undergo regular security
          audits and maintain SOC 2 Type II compliance.
        </p>

        <h2 className="mt-6 text-xl font-semibold text-gray-900">4. Data Retention</h2>
        <p className="text-sm text-gray-600">
          Uploaded invoices and audit results are retained for the duration of your engagement
          plus 90 days. You may request deletion at any time by contacting us.
        </p>

        <h2 className="mt-6 text-xl font-semibold text-gray-900">5. Your Rights</h2>
        <p className="text-sm text-gray-600">
          You have the right to access, correct, or delete your personal data. To exercise these
          rights, contact privacy@1st4.mobi. We respond to all requests within 30 days.
        </p>

        <h2 className="mt-6 text-xl font-semibold text-gray-900">6. Contact</h2>
        <p className="text-sm text-gray-600">
          For privacy-related inquiries: privacy@1st4.mobi
        </p>
      </div>
    </section>
  );
}
