import Link from "next/link";
import { ArrowLeftIcon, CheckCircleIcon, FileTextIcon, ClockIcon, SendIcon } from "lucide-react";

const steps = [
  {
    num: "01",
    title: "Gather Your Evidence",
    body: [
      "Before you dispute anything, you need a clear record of what you were charged versus what you should have been charged. This means assembling:",
      "• Your current signed contract or service agreement showing all rate plans, discounts, and entitlements",
      "• At least 3–6 months of itemised invoices (PDF or CSV — the more data, the stronger your case)",
      "• A line-item comparison showing each charge, the contracted rate, and the discrepancy",
      "",
      "This is the step where most businesses give up. Your contract might be in a filing cabinet somewhere. Your invoices are PDFs in someone's inbox. And comparing them line by line across 50+ services is genuinely a multi-day task.",
      "That's what automated audit tools solve — they do this step in under 60 seconds.",
    ],
  },
  {
    num: "02",
    title: "Calculate the Total Overcharge",
    body: [
      "Once you've identified the discrepancies, calculate the total overcharge across three horizons:",
      "",
      "• Monthly overcharge — what you're being overbilled each month right now",
      "• Historical overcharge — the total overcharge across the full audit period (typically 12 months)",
      "• Annualised projection — if the error is ongoing, what it will cost over the next 12 months if not corrected",
      "",
      "Use these numbers to determine your recovery ask. Most Australian carriers will credit up to 12 months of historical overcharges if you can provide clear evidence. Anything beyond 12 months requires a stronger argument — typically that the error was systemic and should have been caught by the carrier's own quality controls.",
      "",
      "Add 10% GST to your total when making the claim. The carrier should credit the GST-inclusive amount since that's what you actually paid.",
    ],
  },
  {
    num: "03",
    title: "Draft a Formal Dispute Letter",
    body: [
      "A dispute letter isn't an angry email to your account manager. It's a formal document that sets out the facts and demands specific corrective action. A well-structured dispute letter contains:",
      "",
      "1. The account details — account numbers, company name, contract reference",
      "2. The scope — what period is being disputed, what charges are in question",
      "3. The findings — a summary table showing each error category, the number of instances, and the total overcharge",
      "4. The evidence — reference to the attached dispute schedule with line-item detail",
      "5. The demand — what you want the carrier to do (review, credit, correct, confirm in writing)",
      "6. A deadline — typically 14–21 business days for an initial response",
      "",
      "Here's a template structure that works:",
      "",
      '      "We are writing on behalf of [Company Name] to formally dispute',
      '      certain charges identified on the above account(s) during a',
      '      comprehensive billing audit conducted by [Auditor / Internal Team].',
      "",
      '      Our audit has identified [X] billing irregularities across the',
      '      following categories, resulting in an estimated total overcharge',
      '      of $[Y]. [Attach detailed schedule.]"',
      "",
      "Keep it professional. The carrier's billing team will process your claim faster if it's clearly presented with a supporting spreadsheet they can audit themselves.",
    ],
  },
  {
    num: "04",
    title: "Submit to the Right Person",
    body: [
      "Don't just send the dispute letter to the general enquiries address. It needs to reach someone who can action it:",
      "",
      "• Your dedicated account manager (if you have one) — they have a relationship to protect and can escalate internally",
      "• The carrier's billing disputes team — Telstra has a dedicated Billing Disputes function",
      "• Your account's customer service manager — ask to speak to the team that handles credit note requests",
      "",
      "Send both the dispute letter and the supporting schedule (Excel or CSV). A letter alone is a complaint with no evidence. A letter plus a schedule is a case that can be processed.",
      "",
      "Request a case reference number and keep a record of who you spoke to, when, and what they committed to.",
    ],
  },
  {
    num: "05",
    title: "Follow Up Relentlessly",
    body: [
      "Carriers process billing disputes in batches. Your request will sit in a queue unless you actively manage it. The typical timeline:",
      "",
      "• Week 1: Acknowledgement of receipt",
      "• Week 2–3: Initial review by billing team",
      "• Week 3–4: Carrier requests additional information or clarification",
      "• Week 4–6: Credit note issued (for clear-cut cases)",
      "• Week 6–8: Credit appears on next invoice",
      "",
      "If you haven't heard anything by day 10, send a follow-up email referencing your case number. By day 21, escalate to the account manager. By day 30, mention the Telecommunications Industry Ombudsman (TIO) — carriers take TIO referrals seriously because they incur regulatory costs.",
      "The TIO process: if the carrier doesn't resolve your dispute within 30 business days, you can lodge a formal complaint with the TIO at tio.com.au. The carrier is then required to respond within a defined timeframe, and unresolved complaints can result in binding directions.",
    ],
  },
  {
    num: "06",
    title: "Verify the Correction",
    body: [
      "When the credit comes through, don't just file it. Verify:",
      "",
      "• Was the credit for the correct amount?",
      "• Does it cover the full audit period?",
      "• Has the underlying billing configuration been fixed, or will the error recur next month?",
      "• Are the corrected rates reflected on the next invoice?",
      "",
      "We've seen cases where a carrier issued a $35,000 credit but didn't fix the root cause — the same errors reappeared the following month. A credit is a Band-Aid. What you actually want is the billing configuration corrected so the error stops happening.",
      "",
      "Run a follow-up audit 2–3 months after the correction to confirm it stuck. If the error has recurred, escalate immediately — you now have a documented pattern of the same systemic failure.",
    ],
  },
];

export default function Article4() {
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
            Guide
          </span>
          <span>June 9, 2026</span>
          <span>·</span>
          <span>7 min read</span>
        </div>
        <h1 className="text-3xl font-bold leading-tight text-gray-900 sm:text-4xl">
          How to Dispute Your Telco Bill (And Win)
        </h1>
        <p className="mt-4 text-lg leading-relaxed text-gray-600">
          A step-by-step guide to formally disputing Telstra or Optus overcharges — from gathering 
          evidence to getting a credit note issued and preventing recurrence.
        </p>
      </header>

      <div className="mx-auto max-w-3xl px-4 pb-20 sm:px-6">
        <section className="mb-10">
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
            <div className="flex items-start gap-3">
              <ClockIcon className="mt-0.5 h-5 w-5 shrink-0 text-gray-400" />
              <div>
                <p className="text-sm font-medium text-gray-900">Before you start</p>
                <p className="mt-1 text-sm text-gray-600">
                  The dispute process takes 4–8 weeks from start to finish. Most carriers will credit 
                  up to 12 months of historical overcharges if you provide clear evidence. The likelihood 
                  of success depends almost entirely on the quality of your evidence — vague complaints 
                  get rejected, detailed line-item comparisons get paid.
                </p>
              </div>
            </div>
          </div>
        </section>

        {steps.map((step) => (
          <section key={step.num} className="mb-14">
            <div className="mb-4 flex items-center gap-4">
              <span className="flex h-10 w-10 items-center justify-center rounded-full bg-[#2563eb] text-sm font-bold text-white">
                {step.num}
              </span>
              <h2 className="text-xl font-bold text-gray-900">{step.title}</h2>
            </div>
            <div className="space-y-3 pl-14">
              {step.body.map((line, i) => {
                if (!line) {
                  return <br key={i} />;
                }
                if (line.startsWith("•") || line.startsWith("1.") || line.startsWith("2.") || 
                    line.startsWith("3.") || line.startsWith("4.") || line.startsWith("5.") || line.startsWith("6.")) {
                  return (
                    <p key={i} className="text-base leading-relaxed text-gray-700 pl-4">
                      {line}
                    </p>
                  );
                }
                if (line.startsWith('"')) {
                  return (
                    <blockquote key={i} className="border-l-2 border-gray-300 pl-4 text-sm italic text-gray-500">
                      {line.replace(/"/g, "")}
                    </blockquote>
                  );
                }
                return (
                  <p key={i} className="text-base leading-relaxed text-gray-700">
                    {line}
                  </p>
                );
              })}
            </div>
          </section>
        ))}

        <section className="mb-10">
          <h2 className="text-xl font-bold text-gray-900">What If You'd Rather Not Do It Yourself?</h2>
          <p className="mt-3 text-base leading-relaxed text-gray-700">
            The honest truth: the dispute process is tedious and time-consuming. Even with strong 
            evidence, the back-and-forth with carrier billing teams can take weeks. If you're a 
            business leader or finance professional, your time is better spent on things that grow 
            the business.
          </p>
          <p className="mt-3 text-base leading-relaxed text-gray-700">
            This is exactly why 1st 4 Mobile exists. We handle the entire lifecycle — from ingesting 
            your billing data and running the detection pipeline, to drafting the dispute letter and 
            schedule, to managing the carrier follow-up. Our fee is a 50% contingency on what we recover. 
            If there's nothing to recover, there's nothing to pay.
          </p>
        </section>

        <section>
          <div className="rounded-lg border border-[#2563eb]/20 bg-[#2563eb]/5 p-5">
            <div className="flex items-start gap-3">
              <SendIcon className="mt-0.5 h-5 w-5 shrink-0 text-[#2563eb]" />
              <div>
                <p className="text-sm font-semibold text-gray-900">
                  Want us to run the full process for you?
                </p>
                <p className="mt-1 text-sm text-gray-600">
                  Book a free audit review. We'll analyse one month of your billing data at no 
                  cost and tell you exactly what you're overpaying — no obligation.
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
    </article>
  );
}
