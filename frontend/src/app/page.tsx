"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  ShieldCheckIcon,
  ArrowRightIcon,
  BarChart3Icon,
  FileSearchIcon,
  ScaleIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  CheckCircleIcon,
  ZapIcon,
  TrendingDownIcon,
  DollarSignIcon,
  Building2Icon,
  FileTextIcon,
  SmartphoneIcon,
  NetworkIcon,
  CloudIcon,
  WifiIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";

/* ── Animated Counter ── */
function AnimatedCounter({
  end,
  suffix = "",
  prefix = "",
  duration = 2000,
}: {
  end: number;
  suffix?: string;
  prefix?: string;
  duration?: number;
}) {
  const [value, setValue] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  const hasAnimated = useRef(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !hasAnimated.current) {
          hasAnimated.current = true;
          const start = performance.now();
          const animate = (now: number) => {
            const elapsed = now - start;
            const progress = Math.min(elapsed / duration, 1);
            // ease-out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            setValue(Math.floor(eased * end));
            if (progress < 1) requestAnimationFrame(animate);
          };
          requestAnimationFrame(animate);
        }
      },
      { threshold: 0.3 }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, [end, duration]);

  return (
    <span ref={ref}>
      {prefix}
      {value.toLocaleString()}
      {suffix}
    </span>
  );
}

/* ── FAQ Accordion ── */
const faqs = [
  {
    q: "How does the audit work?",
    a: "Upload your invoices, and our 5 proprietary engines analyse every line item — rate plans, data usage, roaming, device subsidies, and contract terms — flagging discrepancies and overcharges.",
  },
  {
    q: "What types of invoices do you accept?",
    a: "We accept CSV, PDF, and XLSX files from major carriers including Telstra, Optus, Vodafone, T-Mobile, Verizon, AT&T, and more.",
  },
  {
    q: "How long does an audit take?",
    a: "Most audits complete within 24-48 hours depending on the volume of invoices. Our automated engines process thousands of line items per second.",
  },
  {
    q: "Is my data secure?",
    a: "Yes. We use 256-bit encryption at rest and in transit. All data is processed in a secure, isolated environment and never shared with third parties.",
  },
  {
    q: "What happens after the audit?",
    a: "You receive a detailed report with itemised overcharges, an executive summary, and a draft dispute letter ready for submission to your carrier.",
  },
  {
    q: "How much does it cost?",
    a: "We operate on a contingency basis — we only get paid when you recover money. Our fee is 50% of the overcharges recovered, with no upfront costs.",
  },
];

function FAQItem({
  question,
  answer,
  open,
  onToggle,
}: {
  question: string;
  answer: string;
  open: boolean;
  onToggle: () => void;
}) {
  return (
    <div className="border-b border-gray-200">
      <button
        onClick={onToggle}
        className="flex w-full items-center justify-between py-4 text-left text-sm font-medium text-gray-900 transition-colors hover:text-[#2563eb]"
      >
        <span>{question}</span>
        {open ? (
          <ChevronUpIcon className="h-4 w-4 shrink-0 text-gray-400" />
        ) : (
          <ChevronDownIcon className="h-4 w-4 shrink-0 text-gray-400" />
        )}
      </button>
      <div
        className={cn(
          "overflow-hidden transition-all duration-300",
          open ? "max-h-96 pb-4" : "max-h-0"
        )}
      >
        <p className="text-sm leading-relaxed text-gray-600">{answer}</p>
      </div>
    </div>
  );
}

/* ── Engine cards ── */
const engines = [
  {
    icon: SmartphoneIcon,
    name: "Rate Plan Optimiser",
    desc: "Detects plans that no longer match usage patterns",
    amount: "$12,400",
    color: "from-blue-500 to-blue-600",
  },
  {
    icon: NetworkIcon,
    name: "Data Usage Anomaly",
    desc: "Flags pooled data overcharges and bill shock events",
    amount: "$8,700",
    color: "from-emerald-500 to-emerald-600",
  },
  {
    icon: CloudIcon,
    name: "Roaming Revenue Shield",
    desc: "Identifies excessive or erroneous roaming charges",
    amount: "$5,200",
    color: "from-violet-500 to-violet-600",
  },
  {
    icon: WifiIcon,
    name: "Device Subsidy Audit",
    desc: "Finds hidden handset and device payment markups",
    amount: "$3,800",
    color: "from-amber-500 to-amber-600",
  },
  {
    icon: FileTextIcon,
    name: "Contract Compliance",
    desc: "Verifies billed rates match agreed contract terms",
    amount: "$6,100",
    color: "from-rose-500 to-rose-600",
  },
];

/* ── Trust badges ── */
const trustItems = [
  { icon: ShieldCheckIcon, label: "SOC 2 Type II Compliant" },
  { icon: CheckCircleIcon, label: "256-bit Encryption" },
  { icon: ScaleIcon, label: "Fully Compliant" },
  { icon: BarChart3Icon, label: "10,000+ Invoices Audited" },
];

export default function LandingPage() {
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  return (
    <div className="flex flex-col">
      {/* ─── HERO ─── */}
      <section className="relative overflow-hidden bg-[#0a1628] px-4 pb-20 pt-16 sm:px-6 sm:pt-24 lg:pt-32">
        {/* Background gradient glow */}
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_rgba(37,99,235,0.15),transparent_60%)]" />
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,_rgba(16,185,129,0.08),transparent_50%)]" />

        <div className="relative mx-auto max-w-5xl text-center">
          <Badge
            variant="default"
            className="mb-6 border-[#2563eb]/30 bg-[#2563eb]/10 text-[#2563eb]"
          >
            <ZapIcon className="mr-1 h-3 w-3" />
            AI-Powered Telecom Audit Platform
          </Badge>
          <h1 className="text-3xl font-bold leading-tight tracking-tight text-white sm:text-4xl md:text-5xl lg:text-6xl">
            Uncover Systemic Overcharges in Your{" "}
            <span className="text-[#2563eb]">Corporate Mobile</span> &amp; Fleet
            Data Invoices
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-base leading-relaxed text-white/60 sm:text-lg">
            Our five proprietary detection engines analyse every line item —
            from rate plans to roaming — identifying hidden overcharges and
            delivering ready-to-submit disputes. Average recovery: 18-35% of
            annual telecom spend.
          </p>
          <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link href="/portal">
              <Button
                size="lg"
                className="h-11 bg-[#2563eb] px-6 text-white hover:bg-[#2563eb]/90"
              >
                Start Your Free Audit
                <ArrowRightIcon className="ml-2 h-4 w-4" />
              </Button>
            </Link>
            <Link href="#how-it-works">
              <Button
                size="lg"
                variant="outline"
                className="h-11 border-white/20 px-6 text-white hover:bg-white/10"
              >
                See How It Works
              </Button>
            </Link>
          </div>
        </div>

        {/* ─── Stat counters ─── */}
        <div className="relative mx-auto mt-16 grid max-w-4xl grid-cols-2 gap-4 sm:grid-cols-4 sm:gap-8">
          {[
            { label: "Invoices Analysed", end: 12450, suffix: "+" },
            { label: "Overcharges Found", end: 3870, suffix: "+" },
            { label: "Clients Served", end: 520, suffix: "+" },
            { label: "Avg. Recovery", end: 35, suffix: "%" },
          ].map((stat) => (
            <div key={stat.label} className="text-center">
              <div className="text-2xl font-bold text-white sm:text-3xl">
                <AnimatedCounter
                  end={stat.end}
                  suffix={stat.suffix}
                  duration={2500}
                />
              </div>
              <div className="mt-1 text-xs text-white/50 sm:text-sm">
                {stat.label}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ─── HOW IT WORKS ─── */}
      <section
        id="how-it-works"
        className="bg-white px-4 py-16 sm:px-6 sm:py-24"
      >
        <div className="mx-auto max-w-6xl">
          <h2 className="text-center text-2xl font-bold text-gray-900 sm:text-3xl">
            How It Works
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-center text-sm text-gray-500 sm:text-base">
            Three simple steps from upload to recovery
          </p>
          <div className="mt-12 grid gap-8 md:grid-cols-3">
            {[
              {
                step: "01",
                icon: FileSearchIcon,
                title: "Upload Your Invoices",
                desc: "Securely upload your mobile and fleet data invoices in CSV, PDF, or XLSX format. We support all major carriers.",
              },
              {
                step: "02",
                icon: BarChart3Icon,
                title: "AI-Powered Analysis",
                desc: "Our five detection engines cross-reference every line item against contract terms, usage patterns, and market benchmarks.",
              },
              {
                step: "03",
                icon: TrendingDownIcon,
                title: "Recover Overcharges",
                desc: "Receive a detailed report with itemised findings and a ready-to-submit dispute letter. We handle the carrier negotiations.",
              },
            ].map((step) => (
              <div key={step.step} className="group relative text-center">
                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-[#2563eb]/10">
                  <step.icon className="h-6 w-6 text-[#2563eb]" />
                </div>
                <div className="mt-4 text-sm font-semibold text-[#2563eb]">
                  Step {step.step}
                </div>
                <h3 className="mt-2 text-lg font-semibold text-gray-900">
                  {step.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-gray-500">
                  {step.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── DETECTION ENGINES ─── */}
      <section className="bg-gray-50 px-4 py-16 sm:px-6 sm:py-24">
        <div className="mx-auto max-w-6xl">
          <h2 className="text-center text-2xl font-bold text-gray-900 sm:text-3xl">
            Five Detection Engines, One Mission
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-center text-sm text-gray-500 sm:text-base">
            Each engine specialises in uncovering a specific category of
            overcharge
          </p>
          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
            {engines.map((engine) => (
              <Card
                key={engine.name}
                className="group border-0 bg-white shadow-sm transition-shadow hover:shadow-md"
              >
                <CardHeader>
                  <div
                    className={cn(
                      "flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br text-white",
                      engine.color
                    )}
                  >
                    <engine.icon className="h-5 w-5" />
                  </div>
                  <CardTitle className="mt-3 text-sm font-semibold text-gray-900">
                    {engine.name}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-xs leading-relaxed text-gray-500">
                    {engine.desc}
                  </p>
                  <div className="mt-3 flex items-baseline gap-1">
                    <span className="text-lg font-bold text-green-600">
                      {engine.amount}
                    </span>
                    <span className="text-xs text-gray-400">avg. found</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* ─── TRUST BADGES ─── */}
      <section className="bg-white px-4 py-16 sm:px-6">
        <div className="mx-auto max-w-4xl">
          <h2 className="text-center text-2xl font-bold text-gray-900 sm:text-3xl">
            Trusted &amp; Secure
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-center text-sm text-gray-500">
            Your data is protected by enterprise-grade security
          </p>
          <div className="mt-10 grid grid-cols-2 gap-6 sm:grid-cols-4">
            {trustItems.map((item) => (
              <div
                key={item.label}
                className="flex flex-col items-center gap-2 rounded-xl border border-gray-100 bg-gray-50/50 px-4 py-6 text-center"
              >
                <item.icon className="h-6 w-6 text-[#2563eb]" />
                <span className="text-xs font-medium text-gray-700">
                  {item.label}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── FAQ ─── */}
      <section className="bg-gray-50 px-4 py-16 sm:px-6 sm:py-24">
        <div className="mx-auto max-w-2xl">
          <h2 className="text-center text-2xl font-bold text-gray-900 sm:text-3xl">
            Frequently Asked Questions
          </h2>
          <div className="mt-10 rounded-xl bg-white px-6 shadow-sm">
            {faqs.map((faq, i) => (
              <FAQItem
                key={i}
                question={faq.q}
                answer={faq.a}
                open={openFaq === i}
                onToggle={() => setOpenFaq(openFaq === i ? null : i)}
              />
            ))}
          </div>
        </div>
      </section>

      {/* ─── CTA ─── */}
      <section className="bg-[#0a1628] px-4 py-16 sm:py-24">
        <div className="mx-auto max-w-3xl text-center">
          <h2 className="text-2xl font-bold text-white sm:text-3xl">
            Ready to Start Saving?
          </h2>
          <p className="mx-auto mt-4 max-w-lg text-sm leading-relaxed text-white/60">
            No upfront cost. No risk. You only pay when we recover overcharges
            on your behalf.
          </p>
          <Link href="/portal">
            <Button className="mt-8 h-11 bg-[#2563eb] px-8 text-white hover:bg-[#2563eb]/90">
              Start Your Free Audit
              <ArrowRightIcon className="ml-2 h-4 w-4" />
            </Button>
          </Link>
        </div>
      </section>
    </div>
  );
}
