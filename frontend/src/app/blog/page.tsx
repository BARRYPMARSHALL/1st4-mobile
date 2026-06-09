import Link from "next/link";
import { PhoneIcon, ArrowRightIcon, CalendarIcon, ClockIcon } from "lucide-react";

const posts = [
  {
    slug: "why-corporate-mobile-bill-wrong",
    title: "Why Your Corporate Mobile Bill Is Wrong (And How To Fix It)",
    excerpt:
      "Telecom billing errors aren't rare — they're the norm. Here's why 80% of corporate accounts have hidden overcharges and what you can do about it.",
    date: "2026-06-09",
    readTime: "6 min",
    category: "Education",
    image: "📱",
  },
  {
    slug: "45k-hidden-overcharges",
    title: "How a Mining Company Found $45K in Hidden Telstra Overcharges",
    excerpt:
      "A real audit of a 50-SIM corporate account uncovered 126 billing errors worth $45,376 per year. Here's exactly what we found and how.",
    date: "2026-06-09",
    readTime: "8 min",
    category: "Case Study",
    image: "⛏️",
  },
  {
    slug: "5-billing-errors-telstra-hides",
    title: "5 Billing Errors Telstra Hopes You Never Find",
    excerpt:
      "From ghost lines you're paying for to rate plans that silently roll back to rack rates — the five most common and expensive billing errors in corporate telecom.",
    date: "2026-06-09",
    readTime: "6 min",
    category: "Education",
    image: "🔍",
  },
  {
    slug: "dispute-telco-bill-win",
    title: "How to Dispute Your Telco Bill (And Win)",
    excerpt:
      "A step-by-step guide to formally disputing Telstra or Optus overcharges — from gathering evidence to getting a credit note issued.",
    date: "2026-06-09",
    readTime: "7 min",
    category: "Guide",
    image: "⚖️",
  },
];

export default function BlogPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero */}
      <section className="border-b border-gray-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 sm:py-24">
          <div className="mx-auto max-w-3xl text-center">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-[#2563eb]/10">
              <PhoneIcon className="h-6 w-6 text-[#2563eb]" />
            </div>
            <h1 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              The 1st 4 Mobile Blog
            </h1>
            <p className="mt-4 text-lg leading-relaxed text-gray-600">
              Insights, case studies, and practical guides on corporate telecom billing —
              uncovering the hidden overcharges in Australian business mobile accounts.
            </p>
          </div>
        </div>
      </section>

      {/* Posts */}
      <section className="mx-auto max-w-7xl px-4 py-12 sm:px-6">
        <div className="grid gap-8 md:grid-cols-2">
          {posts.map((post) => (
            <Link
              key={post.slug}
              href={`/blog/${post.slug}`}
              className="group rounded-xl border border-gray-200 bg-white p-6 shadow-sm transition-all hover:shadow-md hover:border-[#2563eb]/30"
            >
              <div className="flex items-start gap-4">
                <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-gray-100 text-xl">
                  {post.image}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-3 text-xs text-gray-500">
                    <span className="rounded-full bg-[#2563eb]/10 px-2.5 py-0.5 text-xs font-medium text-[#2563eb]">
                      {post.category}
                    </span>
                    <span className="flex items-center gap-1">
                      <CalendarIcon className="h-3 w-3" />
                      {post.date}
                    </span>
                    <span className="flex items-center gap-1">
                      <ClockIcon className="h-3 w-3" />
                      {post.readTime}
                    </span>
                  </div>
                  <h2 className="mt-2 text-lg font-semibold leading-snug text-gray-900 group-hover:text-[#2563eb] transition-colors">
                    {post.title}
                  </h2>
                  <p className="mt-2 text-sm leading-relaxed text-gray-600 line-clamp-3">
                    {post.excerpt}
                  </p>
                  <div className="mt-3 flex items-center gap-1 text-sm font-medium text-[#2563eb]">
                    Read more <ArrowRightIcon className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-gray-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-xl font-bold text-gray-900">
              Think Your Bills Could Be Wrong?
            </h2>
            <p className="mt-3 text-sm text-gray-600">
              We audit corporate Telstra and Optus accounts on a contingency basis —
              if we don't find savings, you don't pay.
            </p>
            <Link
              href="/book"
              className="mt-6 inline-flex items-center gap-2 rounded-lg bg-[#2563eb] px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[#2563eb]/90"
            >
              Book a Free Audit Review <ArrowRightIcon className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
