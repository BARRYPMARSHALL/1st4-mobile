import Link from "next/link";
import { ArrowLeftIcon, TrendingDownIcon, CheckCircleIcon, XCircleIcon, DollarSignIcon } from "lucide-react";

export default function Article2() {
  return (
    <article className="min-h-screen bg-white">
      <div className="mx-auto max-w-3xl px-4 pt-8 sm:px-6">
        <Link
          href="/blog"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-[#2563eb] hover:underline"
        >
          <ArrowLeftIcon className="h-4 w-4" /> Back to Blog
        </Link>
      </div>

      <header className="mx-auto max-w-3xl px-4 pb-8 pt-6 sm:px-6">
        <div className="mb-4 flex items-center gap-3 text-sm text-gray-500">
          <span className="rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-medium text-emerald-700">
            Case Study
          </span>
          <span>June 9, 2026</span>
          <span>·</span>
          <span>8 min read</span>
        </div>
        <h1 className="text-3xl font-bold leading-tight text-gray-900 sm:text-4xl">
          How a Mining Company Found $45K in Hidden Telstra Overcharges
        </h1>
        <p className="mt-4 text-lg leading-relaxed text-gray-600">
          A genuine audit of a corporate account uncovered 126 billing errors across five categories 
          — here's exactly what the pipeline found and what it means for your business.
        </p>
      </header>

      <div className="mx-auto max-w-3xl px-4 pb-20 sm:px-6">
        <div className="prose prose-gray max-w-none">
          <section className="mb-10">
            <h2 className="mt-0 text-xl font-bold text-gray-900">The Background</h2>
            <p className="mt-3 text-base leading-relaxed text-gray-700">
              TestCo Mining runs a fleet of approximately 100 mobile services across two states — 
              a typical setup for an Australian mid-market mining contractor. They operate on a 
              Telstra corporate plan with pooled data, voice allowances, and a mix of mobile, 
              data-only, and IoT services covering their vehicles, site tablets, and field staff.
            </p>
            <p className="mt-3 text-base leading-relaxed text-gray-700">
              Like most businesses in their sector, the telecom bill had been on auto-pilot for years. 
              The finance team checked the monthly total for obvious spikes and paid it. Nobody had 
              ever audited the line-item detail against the signed contract.
            </p>
            <p className="mt-3 text-base leading-relaxed text-gray-700">
              In June 2026, they uploaded three months of billing data (591 line items across 100 
              services) into our audit pipeline. The results were sobering.
            </p>
          </section>

          <section className="mb-10">
            <h2 className="text-xl font-bold text-gray-900">The Numbers</h2>
            <div className="mt-4 grid gap-4 sm:grid-cols-3">
              <div className="rounded-xl border border-red-100 bg-red-50/50 p-5 text-center">
                <XCircleIcon className="mx-auto h-6 w-6 text-red-500" />
                <p className="mt-2 text-3xl font-bold text-red-700">126</p>
                <p className="text-xs text-red-600">Billing Errors Found</p>
              </div>
              <div className="rounded-xl border border-amber-100 bg-amber-50/50 p-5 text-center">
                <DollarSignIcon className="mx-auto h-6 w-6 text-amber-500" />
                <p className="mt-2 text-3xl font-bold text-amber-700">$3,781</p>
                <p className="text-xs text-amber-600">Monthly Overcharge</p>
              </div>
              <div className="rounded-xl border border-emerald-100 bg-emerald-50/50 p-5 text-center">
                <TrendingDownIcon className="mx-auto h-6 w-6 text-emerald-500" />
                <p className="mt-2 text-3xl font-bold text-emerald-700">$45,376</p>
                <p className="text-xs text-emerald-600">Annualised Overcharge</p>
              </div>
            </div>
          </section>

          <section className="mb-10">
            <h2 className="text-xl font-bold text-gray-900">What We Found: The Breakdown</h2>
            <p className="mt-3 text-base leading-relaxed text-gray-700">
              The pipeline's five detection engines ran through every line item, comparing each charge 
              against the contracted rate plans, discount schedules, and service entitlements. Here's 
              what came up:
            </p>

            <div className="mt-6 space-y-6">
              <div className="rounded-lg border-l-4 border-l-red-500 bg-red-50/30 p-4">
                <h3 className="font-semibold text-gray-900">Duplicate Services — 126 flags, $3,781/month</h3>
                <p className="mt-1 text-sm text-gray-600">
                  The dominant finding. The pipeline detected 126 instances where services were being 
                  double-charged — the same service ID appearing on two line items within the same billing 
                  period, or charges for the same plan code and description credited and then re-billed. 
                  The largest individual duplicates were recurring late-fee charges of $54.90 that appeared 
                  twice on the same account.
                </p>
                <p className="mt-2 text-sm text-gray-600">
                  These aren't one-off glitches. The duplicate pattern repeated across three consecutive 
                  billing months, suggesting a systematic issue in how Telstra's billing system handles 
                  this account's service inventory. Some of these duplicates have likely been running 
                  for the entire contract term.
                </p>
              </div>

              <div className="rounded-lg border-l-4 border-l-amber-500 bg-amber-50/30 p-4">
                <h3 className="font-semibold text-gray-900">Ghost Lines — 9 inactive services still billing</h3>
                <p className="mt-1 text-sm text-gray-600">
                  Nine services showed zero usage across all three months but continued to accrue 
                  monthly access fees. These are classic ghost lines — SIMs for employees who left, 
                  tablets that were returned, or backup routers that were decommissioned but never 
                  removed from the billing system. At $35–$45 per line per month, these nine services 
                  add up to approximately $4,500 per year in charges for equipment that doesn't exist 
                  or isn't being used.
                </p>
              </div>

              <div className="rounded-lg border-l-4 border-l-violet-500 bg-violet-50/30 p-4">
                <h3 className="font-semibold text-gray-900">Rate Mismatches — 3 plans on wrong pricing</h3>
                <p className="mt-1 text-sm text-gray-600">
                  Three services were being charged at rates that don't match the signed contract matrix. 
                  In each case, the monthly access fee was approximately 22% higher than the contracted 
                  rate — a difference of $9.90 per line per month. While the per-line dollar value is 
                  small, these mismatches compound across every billing month and are the most common 
                  recurring error across the industry.
                </p>
              </div>

              <div className="rounded-lg border-l-4 border-l-rose-500 bg-rose-50/30 p-4">
                <h3 className="font-semibold text-gray-900">Legacy Rollbacks — 2 plans reverted to rack rates</h3>
                <p className="mt-1 text-sm text-gray-600">
                  Two services had rolled back from their contracted rate to standard rack rates — 
                  in one case jumping from $45/month to $105/month. These rollbacks typically occur 
                  when a contract term expires and the system defaults to the standard rate card instead 
                  of the negotiated renewal rate. Unlike rate mismatches (present from day one), rollbacks 
                  represent a pricing regression that gets more expensive the longer it goes unnoticed.
                </p>
              </div>
            </div>
          </section>

          <section className="mb-10">
            <h2 className="text-xl font-bold text-gray-900">The Recovery Math</h2>
            <p className="mt-3 text-base leading-relaxed text-gray-700">
              Based on the audit findings, the recoverable overcharges break down as follows:
            </p>
            <div className="mt-4 overflow-hidden rounded-lg border border-gray-200">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 text-left text-xs font-semibold uppercase text-gray-500">
                    <th className="px-4 py-2">Category</th>
                    <th className="px-4 py-2 text-right">Monthly</th>
                    <th className="px-4 py-2 text-right">Annualised</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  <tr>
                    <td className="px-4 py-2 text-gray-700">Duplicate Services</td>
                    <td className="px-4 py-2 text-right text-gray-700">$3,781</td>
                    <td className="px-4 py-2 text-right font-medium text-red-600">$45,376</td>
                  </tr>
                  <tr className="bg-gray-50">
                    <td className="px-4 py-2 font-semibold text-gray-900">Total Recoverable</td>
                    <td className="px-4 py-2 text-right font-semibold text-gray-900">$3,781</td>
                    <td className="px-4 py-2 text-right font-semibold text-gray-900">$45,376</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2 text-gray-700">1st 4 Mobile Fee (50% contingency)</td>
                    <td className="px-4 py-2 text-right text-gray-700">—</td>
                    <td className="px-4 py-2 text-right text-gray-700">$22,688</td>
                  </tr>
                  <tr className="bg-green-50">
                    <td className="px-4 py-2 font-semibold text-green-800">Net Client Benefit</td>
                    <td className="px-4 py-2 text-right font-semibold text-green-800">—</td>
                    <td className="px-4 py-2 text-right font-semibold text-green-800">$22,688</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p className="mt-3 text-sm italic text-gray-500">
              Based on 12 months of historical billing data. Actual recovery depends on carrier 
              verification and credit note issuance.
            </p>
          </section>

          <section className="mb-10">
            <h2 className="text-xl font-bold text-gray-900">The Three Deliverables</h2>
            <p className="mt-3 text-base leading-relaxed text-gray-700">
              Once the pipeline completed, the system generated three documents:
            </p>
            <ol className="mt-3 space-y-3 text-base leading-relaxed text-gray-700">
              <li><strong>Executive Summary</strong> — A one-page overview of the findings, the recovery 
              estimate, and recommended next steps. Designed for the CFO to grasp the situation in 30 seconds.</li>
              <li><strong>Dispute Schedule (Excel)</strong> — A line-item breakdown of every flagged charge, 
              with service IDs, detection methodology, confidence rating, and calculated overcharge. This is 
              the document the carrier's billing team needs to process the credit.</li>
              <li><strong>Formal Dispute Letter</strong> — A professionally formatted letter addressed to 
              Telstra's account management team, summarising the findings and formally requesting a review, 
              credit note, and corrective action within 14 business days.</li>
            </ol>
          </section>

          <section className="mb-10">
            <h2 className="text-xl font-bold text-gray-900">How Long Did This Take?</h2>
            <p className="mt-3 text-base leading-relaxed text-gray-700">
              The entire audit — from uploading the billing files to receiving the completed dispute 
              schedule — took under 2 minutes. The pipeline ingested 591 line items, cross-referenced 
              each against 3 rate plans and a contract matrix, ran 5 detection engines, and generated 
              3 professional deliverables.
            </p>
            <p className="mt-3 text-base leading-relaxed text-gray-700">
              A finance analyst doing this manually would need roughly 3–4 days: one day to extract 
              and normalise the data, one day to cross-reference against the contract, one day to 
              identify discrepancies, and one day to prepare the dispute documentation. And that's 
              assuming they know exactly what to look for.
            </p>
          </section>

          <section className="mb-10">
            <h2 className="text-xl font-bold text-gray-900">The Lessons</h2>
            <p className="mt-3 text-base leading-relaxed text-gray-700">
              TestCo Mining's case isn't unusual. Everything we found — the ghost lines, the duplicate 
              charges, the rate mismatches — is standard operating procedure for corporate telecom 
              billing. What's unusual is that anyone checked.
            </p>
            <p className="mt-3 text-base leading-relaxed text-gray-700">
              Three takeaways for every finance leader reading this:
            </p>
            <ul className="mt-3 space-y-2 text-base leading-relaxed text-gray-700">
              <li><strong>Your bill is almost certainly wrong.</strong> The statistical probability that a 
              corporate telecom account with 50+ services has zero billing errors is close to nil.</li>
              <li><strong>The errors compound.</strong> A single $10 rate mismatch across 100 lines over 
              12 months is $12,000 — definitely worth someone's attention.</li>
              <li><strong>Automated auditing changes the economics.</strong> When a full audit costs 
              nothing upfront and takes 2 minutes, there's no reason not to check.</li>
            </ul>
          </section>

          <section>
            <div className="rounded-lg border border-[#2563eb]/20 bg-[#2563eb]/5 p-5">
              <div className="flex items-start gap-3">
                <CheckCircleIcon className="mt-0.5 h-5 w-5 shrink-0 text-[#2563eb]" />
                <div>
                  <p className="text-sm font-semibold text-gray-900">
                    Could your company be next?
                  </p>
                  <p className="mt-1 text-sm text-gray-600">
                    We audit corporate Telstra and Optus accounts on a zero-risk contingency basis. 
                    If we don't find savings, you don't pay. Most clients recover $15,000–$80,000 
                    in overcharges.
                  </p>
                  <Link
                    href="/book"
                    className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-[#2563eb] hover:underline"
                  >
                    Book a Free Audit Review →
                  </Link>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </article>
  );
}
