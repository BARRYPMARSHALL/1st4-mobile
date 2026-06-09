export default function TermsPage() {
  return (
    <section className="flex-1 bg-white px-4 py-16 sm:py-24">
      <div className="mx-auto max-w-3xl prose prose-sm sm:prose">
        <h1 className="text-3xl font-bold text-gray-900">Terms of Service</h1>
        <p className="text-sm text-gray-500">Last updated: June 2026</p>

        <h2 className="mt-8 text-xl font-semibold text-gray-900">1. Service Description</h2>
        <p className="text-sm text-gray-600">
          1st 4 Mobile provides an AI-powered telecom invoice audit platform. Our five detection
          engines analyse uploaded invoices to identify overcharges, billing errors, and
          non-compliance with contract terms.
        </p>

        <h2 className="mt-6 text-xl font-semibold text-gray-900">2. Contingency Fee Model</h2>
        <p className="text-sm text-gray-600">
          We operate on a no-win, no-fee basis. Our fee is 50% of overcharges successfully
          recovered on your behalf. No upfront costs, no monthly retainers. Fees are invoiced
          upon successful recovery and are due within 30 days.
        </p>

        <h2 className="mt-6 text-xl font-semibold text-gray-900">3. Client Obligations</h2>
        <p className="text-sm text-gray-600">
          You agree to provide accurate and complete invoice data. You authorise 1st 4 Mobile
          to communicate with your carrier(s) regarding disputed charges. You retain the right
          to approve or reject any dispute before it is submitted.
        </p>

        <h2 className="mt-6 text-xl font-semibold text-gray-900">4. Limitation of Liability</h2>
        <p className="text-sm text-gray-600">
          1st 4 Mobile&apos;s liability is limited to the fees paid for the specific engagement
          giving rise to the claim. We are not liable for indirect or consequential damages.
          Our audits are advisory and do not constitute legal advice.
        </p>

        <h2 className="mt-6 text-xl font-semibold text-gray-900">5. Termination</h2>
        <p className="text-sm text-gray-600">
          Either party may terminate the engagement with 30 days written notice. Upon termination,
          you retain all audit reports and findings produced up to that point.
        </p>

        <h2 className="mt-6 text-xl font-semibold text-gray-900">6. Governing Law</h2>
        <p className="text-sm text-gray-600">
          These terms are governed by the laws of New South Wales, Australia.
        </p>

        <h2 className="mt-6 text-xl font-semibold text-gray-900">7. Contact</h2>
        <p className="text-sm text-gray-600">
          For questions about these terms: legal@1st4.mobi
        </p>
      </div>
    </section>
  );
}
