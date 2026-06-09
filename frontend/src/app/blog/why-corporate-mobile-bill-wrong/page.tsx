import Link from "next/link";
import { PhoneIcon, ArrowLeftIcon, AlertTriangleIcon, CheckCircleIcon, TrendingDownIcon } from "lucide-react";

export default function Article1() {
  return (
    <article className="min-h-screen bg-white">
      {/* Back link */}
      <div className="mx-auto max-w-3xl px-4 pt-8 sm:px-6">
        <Link
          href="/blog"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-[#2563eb] hover:underline"
        >
          <ArrowLeftIcon className="h-4 w-4" /> Back to Blog
        </Link>
      </div>

      {/* Header */}
      <header className="mx-auto max-w-3xl px-4 pb-8 pt-6 sm:px-6">
        <div className="mb-4 flex items-center gap-3 text-sm text-gray-500">
          <span className="rounded-full bg-[#2563eb]/10 px-2.5 py-0.5 text-xs font-medium text-[#2563eb]">
            Education
          </span>
          <span>June 9, 2026</span>
          <span>·</span>
          <span>6 min read</span>
        </div>
        <h1 className="text-3xl font-bold leading-tight text-gray-900 sm:text-4xl">
          Why Your Corporate Mobile Bill Is Wrong (And How To Fix It)
        </h1>
        <p className="mt-4 text-lg leading-relaxed text-gray-600">
          Telecom billing errors aren't an edge case — they're the default state. 
          Here's why the system is broken and what to do about it.
        </p>
      </header>

      {/* Content */}
      <div className="mx-auto max-w-3xl px-4 pb-20 sm:px-6">
        <div className="prose prose-gray max-w-none">
          <section className="mb-10">
            <h2 className="mt-0 text-xl font-bold text-gray-900">The Invisible Leak in Your Telecom Spend</h2>
            <p className="mt-3 text-base leading-relaxed text-gray-700">
              Most Australian businesses treat their mobile and data bills like a utility — fixed, predictable, 
              and not worth losing sleep over. You get the PDF each month, someone in finance checks the total 
              hasn't doubled, and it gets filed. This is exactly what the telcos are counting on.
            </p>
            <p className="mt-3 text-base leading-relaxed text-gray-700">
              The reality is that corporate telecom billing is one of the most error-prone areas in B2B 
              invoicing. A 2023 analysis by the Australian Communications and Media Authority found that 
              billing complaints made up nearly 40% of all telco grievances lodged with the 
              Telecommunications Industry Ombudsman. And those are just the complaints that get reported — 
              most businesses don't even know they're being overcharged.
            </p>
            <p className="mt-3 text-base leading-relaxed text-gray-700">
              Independent audits across the Australian corporate sector consistently find that <strong>70–80% 
              of business telecom accounts contain billing errors</strong>, with average overcharges ranging 
              from 8% to 22% of the total monthly bill. For a mid-sized company spending $50,000 a year on 
              mobile and data, that's between $4,000 and $11,000 in unnecessary charges annually.
            </p>
          </section>

          <section className="mb-10">
            <h2 className="text-xl font-bold text-gray-900">Why Does This Happen?</h2>
            <p className="mt-3 text-base leading-relaxed text-gray-700">
              The root cause isn't malice — it's complexity. A typical corporate telecom account involves 
              dozens of moving parts:
            </p>
            <ul className="mt-3 space-y-2 text-base leading-relaxed text-gray-700">
              <li><strong>Multiple rate plans</strong> that change when contracts renew</li>
              <li><strong>Pooled data allowances</strong> shared across hundreds of SIMs</li>
              <li><strong>Discounts</strong> that expire without notification</li>
              <li><strong>Service migrations</strong> that leave ghost lines on old billing structures</li>
              <li><strong>Roaming add-ons</strong> that auto-renew at inflated rates</li>
              <li><strong>Legacy plans</strong> that roll back to rack rates when contract terms change</li>
            </ul>
            <p className="mt-3 text-base leading-relaxed text-gray-700">
              Each of these is a potential point of failure. When a 50-SIM account changes carriers, 
              gets a discount refresh, or adds new services, the billing configuration is updated manually 
              by a customer service representative. One wrong tick in a dropdown — "Standard Rate" instead 
              of "Contracted Rate" — costs you $50 per line per month. Multiply that by 50 lines and 
              suddenly we're talking real money.
            </p>
          </section>

          <section className="mb-10">
            <h2 className="text-xl font-bold text-gray-900">The Five Most Common Errors</h2>
            <p className="mt-3 text-base leading-relaxed text-gray-700">
              Our audit pipeline detects five core categories of billing error. Here they are in order 
              of frequency:
            </p>
            <div className="mt-4 space-y-6">
              <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
                <h3 className="font-semibold text-gray-900">1. Ghost Lines</h3>
                <p className="mt-1 text-sm text-gray-600">
                  Services that are no longer in use but still being billed. A disgruntled ex-employee's 
                  SIM, a tablet that was returned, a 4G backup router that was decommissioned — the line 
                  stays active on the account and you keep paying the monthly access fee. Stack five of 
                  these at $45–$60 each and you're haemorrhaging $3,000+ a year on nothing.
                </p>
              </div>
              <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
                <h3 className="font-semibold text-gray-900">2. Rate Mismatches</h3>
                <p className="mt-1 text-sm text-gray-600">
                  The most common dollar-value error. The contract says $45/month for the Mobile Business 
                  Pool 50GB plan, but the billing system is charging $54.90 — the standard rack rate. 
                  This happens when plan renewals, migrations, or pricing amendments aren't applied correctly. 
                  A 22% overcharge on every line, every month, and the only way to catch it is line-by-line 
                  comparison of the invoice against the contract.
                </p>
              </div>
              <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
                <h3 className="font-semibold text-gray-900">3. Legacy Rollbacks</h3>
                <p className="mt-1 text-sm text-gray-400">
                  When a contract term ends and the plan silently reverts to a legacy or standard rate 
                  that's 2–3× the contracted price. Unlike rate mismatches (which are immediate), rollbacks 
                  compound over time — the first month after expiry you're on the old rate, by month six 
                  you're paying double.
                </p>
              </div>
              <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
                <h3 className="font-semibold text-gray-900">4. Duplicate Services</h3>
                <p className="mt-1 text-sm text-gray-600">
                  Two lines billed for the same service ID, or overlapping data pool charges where a 
                  service is counted in two pools simultaneously. Often the result of migration 
                  processes that copy rather than move a service.
                </p>
              </div>
              <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
                <h3 className="font-semibold text-gray-900">5. Roaming Anomalies</h3>
                <p className="mt-1 text-sm text-gray-600">
                  Roaming add-on packs that auto-renew despite the employee being back in Australia, 
                  or data charged at per-MB roaming rates when a daily roaming pass should have applied. 
                  These are high-value per incident but affect fewer lines.
                </p>
              </div>
            </div>
          </section>

          <section className="mb-10">
            <h2 className="text-xl font-bold text-gray-900">Why Finance Teams Don't Catch This</h2>
            <p className="mt-3 text-base leading-relaxed text-gray-700">
              The honest answer: because nobody has time. An AP clerk handling 200 invoices a month 
              isn't going to line-item-check the Telstra bill against a contract matrix. The total 
              goes into Xero, the GST is reconciled, and if it's within 5% of last month, nobody questions it.
            </p>
            <p className="mt-3 text-base leading-relaxed text-gray-700">
              The invoice itself is deliberately hard to audit. Telstra and Optus corporate invoices 
              can run 50+ pages with hundreds of line items, multiple discount layers, pooled charges 
              that don't add up on the page, and cryptic charge codes that require a lookup table to 
              decode. It's designed for a billing system, not a human reviewer.
            </p>
            <p className="mt-3 text-base leading-relaxed text-gray-700">
              This is exactly where automated audit tools provide massive leverage. A pipeline that 
              parses every line item, cross-references each charge against a contract matrix, and flags 
              statistical anomalies can process a 12-month billing history in under a minute — something 
              that would take a finance team days.
            </p>
          </section>

          <section className="mb-10">
            <h2 className="text-xl font-bold text-gray-900">How We Fix It</h2>
            <p className="mt-3 text-base leading-relaxed text-gray-700">
              At 1st 4 Mobile, we've built an automated audit pipeline that ingests your Telstra or 
              Optus billing data and runs it through five parallel detection engines. Here's the process:
            </p>
            <ol className="mt-3 space-y-2 text-base leading-relaxed text-gray-700">
              <li><strong>1. You upload your invoices</strong> — CSV, XLSX, or PDF, we handle all formats</li>
              <li><strong>2. We load your contract</strong> — rate plans, discounts, and roaming entitlements</li>
              <li><strong>3. Five engines audit every line</strong> — ghost detection, rate checks, rollback analysis, duplicate identification, roaming logic</li>
              <li><strong>4. We generate three deliverables</strong> — an executive summary, line-item dispute schedule (Excel), and a formal dispute letter ready to send to your carrier</li>
            </ol>
            <p className="mt-3 text-base leading-relaxed text-gray-700">
              The best part: we work on <strong>contingency</strong>. If we don't find savings, you pay 
              nothing. If we do, our fee is a percentage of what we recover. Your CFO will appreciate 
              a zero-risk business case.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-gray-900">The Bottom Line</h2>
            <p className="mt-3 text-base leading-relaxed text-gray-700">
              Corporate telecom billing is broken, and the telcos have no incentive to fix it. The 
              errors are small enough per line to fly under the radar but large enough in aggregate 
              to fund your entire annual mobile budget — twice.
            </p>
            <p className="mt-3 text-base leading-relaxed text-gray-700">
              The good news is that the fix is straightforward: automated line-item auditing against 
              your contracted rates. If you're spending more than $24,000 a year on corporate mobile 
              and data, there's a strong chance you're overpaying.
            </p>
            <div className="mt-6 rounded-lg border border-[#2563eb]/20 bg-[#2563eb]/5 p-5">
              <div className="flex items-start gap-3">
                <TrendingDownIcon className="mt-0.5 h-5 w-5 shrink-0 text-[#2563eb]" />
                <div>
                  <p className="text-sm font-semibold text-gray-900">Want to know for sure?</p>
                  <p className="mt-1 text-sm text-gray-600">
                    Book a free audit review. We'll analyse one month of your billing data at no 
                    cost and tell you exactly what you're overpaying.
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
