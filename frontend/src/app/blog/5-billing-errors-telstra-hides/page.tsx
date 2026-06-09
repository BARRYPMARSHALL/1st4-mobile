import Link from "next/link";
import { ArrowLeftIcon, SearchIcon, DollarSignIcon, FileWarningIcon } from "lucide-react";

const errors = [
  {
    id: "ghost-lines",
    title: "Ghost Lines",
    subtitle: "Paying for services that don't exist anymore",
    severity: "High frequency, moderate dollar value",
    color: "border-l-amber-500",
    bg: "bg-amber-50/30",
    body: [
      "Ghost lines are the most common billing error in corporate telecom — and the easiest to understand. A ghost line is any service on your account that's accruing monthly charges but is no longer in use. Disconnected SIMs, returned tablets, decommissioned 4G backup routers, employees who left six months ago — their lines stay active in the billing system and you keep paying for them.",
      "In a recent audit of a 100-service corporate account, we found 9 ghost lines — inactive SIMs with zero data usage across three consecutive billing months, still incurring monthly access fees of $35–$45 each. That's roughly $4,500 a year for services that are literally providing nothing.",
      "How do they happen? Usually it's a process failure. When an employee leaves, IT disables the device but the telco is never notified to cancel the line. The SIM sits in a drawer somewhere, billing away. When a tablet is returned to the pool, it stays on the old user's plan rather than being reassigned.",
      "The fix: every line on your account should have an owner. If a service has zero usage for two consecutive months and can't be assigned to a current employee, it should be flagged for cancellation. Automated auditing catches these instantly — a human reviewing a 40-page invoice almost never does.",
    ],
  },
  {
    id: "rate-mismatches",
    title: "Rate Mismatches",
    subtitle: "Paying standard rates when you negotiated a discount",
    severity: "Highest dollar value",
    color: "border-l-red-500",
    bg: "bg-red-50/30",
    body: [
      "Rate mismatches are the most expensive billing error by total dollar value. They occur when the amount being charged for a service doesn't match the contracted rate in your signed agreement. You negotiated $45/month for the Mobile Business Pool plan, but the billing system is charging $54.90 — the standard rack rate with no discount applied.",
      "A 22% overcharge on a single line is annoying but not catastrophic. A 22% overcharge on 50 lines, every month, for 24 months, is $14,256 — and almost nobody catches it because the difference doesn't jump off the page.",
      "Rate mismatches happen at every stage of the account lifecycle: when a plan is first provisioned (the rep types 'standard' instead of 'contracted'), when a plan is migrated during a renewal (the old discount code doesn't transfer), when a pricing amendment is applied manually (typos happen), or when a new service is added to an existing account (it defaults to the standard rate card).",
      "The only reliable way to detect rate mismatches is to compare every line item on every invoice against the contract matrix. That's what our pipeline does — it loads your signed rate plans, then flags any charge that deviates by more than a configured tolerance (usually 2%).",
    ],
  },
  {
    id: "legacy-rollbacks",
    title: "Legacy Rollbacks",
    subtitle: "Your contract expired and your rates silently doubled",
    severity: "High dollar value per incident",
    color: "border-l-violet-500",
    bg: "bg-violet-50/30",
    body: [
      "Legacy rollbacks are the most insidious billing error because they don't happen immediately. When your contract term ends, most telco billing systems don't proactively apply the renewal rates. Instead, they default the line to the 'legacy' or 'standard' rate card — which can be 2–3 times higher than what you were paying.",
      "We recently detected a rollback where a service jumped from its contracted rate of $45/month to a legacy rack rate of $105/month — a 133% increase. The service had been on the higher rate for six months before the audit caught it.",
      "Why does this happen? Contract renewals involve manual intervention. Someone in the telco's billing team needs to update the rate code on each affected line. If that work order gets queued behind higher-priority tickets, or if the renewal discount doesn't match exactly, the line rolls back to whatever the system considers the 'default' rate for that product code.",
      "The dangerous thing about rollbacks is their compounding nature. A rate mismatch costs you a fixed percentage from day one. A rollback gets progressively worse — every month the service stays on the legacy rate is another month of avoidable overspend. By month 12, you've overpaid by thousands per line.",
    ],
  },
  {
    id: "duplicates",
    title: "Duplicate Services",
    subtitle: "Being charged twice for the same thing",
    severity: "Moderate frequency, variable value",
    color: "border-l-blue-500",
    bg: "bg-blue-50/30",
    body: [
      "Duplicate services occur when the same charge appears twice on your invoice — either as an exact duplicate (same service ID, same charge description, same amount) or a near duplicate (same service ID, same charge category, amounts within a small tolerance).",
      "In our mining company case study, duplicates were the single largest category with 126 instances across three months of billing. The pipeline found the same service IDs appearing with identical or near-identical charges — in some cases a $54.90 late fee charge appearing twice on the same line item.",
      "Duplicates typically arise from system integration errors. When a telco migrates billing platforms or reconciles between its CRM and billing systems, service records can be duplicated. The line appears in the inventory twice, so the billing system charges for it twice. Or a charge correction is applied as a credit on one line and a debit on another, effectively cancelling out the fix.",
      "The key insight: duplicates are almost never intentional, but they're also almost never caught by manual review. Nobody reads an invoice line by line looking for pairs of identical amounts. Automated pattern matching, however, spots them in milliseconds.",
    ],
  },
  {
    id: "roaming-anomalies",
    title: "Roaming Anomalies",
    subtitle: "International data charged at premium rates",
    severity: "High value per incident, lower frequency",
    color: "border-l-emerald-500",
    bg: "bg-emerald-50/30",
    body: [
      "Roaming anomalies affect fewer lines than other error categories, but when they hit, they hit hard. A single field technician spending two weeks in the US without the correct roaming add-on can rack up thousands in per-MB data charges — charged at $0.10/MB instead of the $20/day roaming pass.",
      "There are two common roaming billing errors. The first is the absence of a roaming pack: the employee travels, the device connects, and data is charged at the pay-per-use rate because no roaming add-on was applied to their line. The second is the zombie roaming pack: a roaming add-on that auto-renews every month even when the employee is back in Australia.",
      "Zombie packs are particularly costly at scale. A $20/day roaming pass that renews monthly for 10 travellers year-round adds up to $2,400 in unnecessary charges — and that's before the usage charges that were incorrectly rated because the wrong zone was applied.",
      "Detection requires cross-referencing travel periods against roaming charge activity, which is computationally straightforward but practically impossible to do manually across a large account. Our pipeline flags any roaming charge that doesn't have a corresponding travel event or roaming pack assigned.",
    ],
  },
];

export default function Article3() {
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
          <span className="rounded-full bg-[#2563eb]/10 px-2.5 py-0.5 text-xs font-medium text-[#2563eb]">
            Education
          </span>
          <span>June 9, 2026</span>
          <span>·</span>
          <span>6 min read</span>
        </div>
        <h1 className="text-3xl font-bold leading-tight text-gray-900 sm:text-4xl">
          5 Billing Errors Telstra Hopes You Never Find
        </h1>
        <p className="mt-4 text-lg leading-relaxed text-gray-600">
          They're not the biggest phone company in Australia by accident. Their billing system is 
          enormously complex — and complexity breeds errors. Here are the five most common, and 
          how to spot them before your next audit.
        </p>
      </header>

      <div className="mx-auto max-w-3xl px-4 pb-20 sm:px-6">
        <div className="mb-8 rounded-lg border border-gray-200 bg-gray-50 p-4">
          <div className="flex items-start gap-3">
            <FileWarningIcon className="mt-0.5 h-5 w-5 shrink-0 text-amber-500" />
            <p className="text-sm text-gray-700">
              <strong>Quick stat:</strong> Independent audits consistently find billing errors in 
              70–80% of corporate telecom accounts. The average overcharge is 8–22% of the monthly bill. 
              If you haven't audited your account in the last 12 months, assume you're overpaying.
            </p>
          </div>
        </div>

        {errors.map((error, idx) => (
          <section key={error.id} className="mb-12">
            <div className={`rounded-lg border-l-4 ${error.color} ${error.bg} p-6`}>
              <div className="flex items-center gap-3 text-sm text-gray-500">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-white text-xs font-bold text-[#2563eb]">
                  {idx + 1}
                </span>
                <span className="rounded-full bg-white px-2 py-0.5 text-xs">
                  {error.severity}
                </span>
              </div>
              <h2 className="mt-3 text-xl font-bold text-gray-900">{error.title}</h2>
              <p className="mt-1 text-sm font-medium text-gray-500">{error.subtitle}</p>
            </div>
            <div className="mt-4 space-y-3 px-1">
              {error.body.map((paragraph, i) => (
                <p key={i} className="text-base leading-relaxed text-gray-700">
                  {paragraph}
                </p>
              ))}
            </div>
          </section>
        ))}

        <section className="mb-10">
          <h2 className="text-xl font-bold text-gray-900">The Common Thread</h2>
          <p className="mt-3 text-base leading-relaxed text-gray-700">
            All five error types share a single root cause: the gap between what's contracted and 
            what's billed is bridged by manual processes. Someone at the telco enters a rate code, 
            applies a discount, or provisions a service — and once that entry is wrong, it stays 
            wrong until someone catches it.
          </p>
          <p className="mt-3 text-base leading-relaxed text-gray-700">
            The telcos know this. Their billing systems are architected for flexibility, not accuracy. 
            Every rate change, every migration, every new service is an opportunity for a discrepancy 
            to enter the system. And their invoices are designed to be paid, not audited — hundreds of 
            line items, cryptic codes, and pooled charges that don't add up on the page.
          </p>
          <p className="mt-3 text-base leading-relaxed text-gray-700">
            The only defence is systematic, automated line-item auditing. Not a spot check. Not a once-a-year 
            review by AP. A proper pipeline that reads every charge, compares it to your contract, and flags 
            anything that doesn't match.
          </p>
        </section>

        <section>
          <div className="rounded-lg border border-[#2563eb]/20 bg-[#2563eb]/5 p-5">
            <div className="flex items-start gap-3">
              <SearchIcon className="mt-0.5 h-5 w-5 shrink-0 text-[#2563eb]" />
              <div>
                <p className="text-sm font-semibold text-gray-900">
                  See which errors are hiding in your bill
                </p>
                <p className="mt-1 text-sm text-gray-600">
                  Upload one month of billing data and we'll run it through all five detection 
                  engines — free, no obligation. You'll get a report showing exactly what you're 
                  overpaying and by how much.
                </p>
                <Link
                  href="/book"
                  className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-[#2563eb] hover:underline"
                >
                  Get Your Free Audit →
                </Link>
              </div>
            </div>
          </div>
        </section>
      </div>
    </article>
  );
}
