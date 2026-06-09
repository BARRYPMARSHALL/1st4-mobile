"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { CalendarIcon, ClockIcon, CheckCircleIcon } from "lucide-react";

export default function BookDemoPage() {
  const [submitted, setSubmitted] = useState(false);
  const [form, setForm] = useState({
    name: "",
    email: "",
    company: "",
    phone: "",
    employees: "",
    date: "",
    time: "",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // In production, this would hit the backend or a calendar API
    setSubmitted(true);
  };

  if (submitted) {
    return (
      <section className="flex-1 bg-gray-50 px-4 py-24">
        <div className="mx-auto max-w-lg text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
            <CheckCircleIcon className="h-8 w-8 text-green-600" />
          </div>
          <h1 className="mt-6 text-2xl font-bold text-gray-900">
            Demo Scheduled!
          </h1>
          <p className="mt-3 text-sm text-gray-500">
            We&apos;ll send a calendar invite to{" "}
            <span className="font-medium text-gray-900">{form.email}</span>{" "}
            confirming your slot. See you there.
          </p>
          <Button
            variant="outline"
            className="mt-6"
            onClick={() => setSubmitted(false)}
          >
            Book Another
          </Button>
        </div>
      </section>
    );
  }

  return (
    <section className="flex-1 bg-gray-50 px-4 py-16 sm:py-24">
      <div className="mx-auto max-w-2xl">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">
            Book a Free Demo
          </h1>
          <p className="mt-3 text-sm text-gray-500">
            See how our five AI-powered detection engines uncover hidden
            overcharges in your telecom invoices. No commitment, no upfront cost.
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="mt-10 space-y-6 rounded-xl bg-white px-6 py-8 shadow-sm sm:px-10"
        >
          <div className="grid gap-6 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="name">Full Name</Label>
              <Input
                id="name"
                required
                placeholder="John Smith"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Work Email</Label>
              <Input
                id="email"
                type="email"
                required
                placeholder="john@company.com"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="company">Company</Label>
              <Input
                id="company"
                required
                placeholder="Acme Corp"
                value={form.company}
                onChange={(e) => setForm({ ...form, company: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="phone">Phone</Label>
              <Input
                id="phone"
                type="tel"
                placeholder="+61 400 000 000"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="employees">Company Size</Label>
            <Select
              value={form.employees}
              onValueChange={(v: string | null) => setForm({ ...form, employees: v ?? "" })}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select company size" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1-50">1-50 employees</SelectItem>
                <SelectItem value="51-200">51-200 employees</SelectItem>
                <SelectItem value="201-1000">201-1,000 employees</SelectItem>
                <SelectItem value="1000+">1,000+ employees</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="grid gap-6 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="date">
                <CalendarIcon className="mr-1 inline h-4 w-4 text-gray-400" />
                Preferred Date
              </Label>
              <Input
                id="date"
                type="date"
                required
                value={form.date}
                onChange={(e) => setForm({ ...form, date: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="time">
                <ClockIcon className="mr-1 inline h-4 w-4 text-gray-400" />
                Preferred Time
              </Label>
              <Select
                value={form.time}
                onValueChange={(v: string | null) => setForm({ ...form, time: v ?? "" })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select time" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="09:00">9:00 AM AEST</SelectItem>
                  <SelectItem value="10:00">10:00 AM AEST</SelectItem>
                  <SelectItem value="11:00">11:00 AM AEST</SelectItem>
                  <SelectItem value="12:00">12:00 PM AEST</SelectItem>
                  <SelectItem value="13:00">1:00 PM AEST</SelectItem>
                  <SelectItem value="14:00">2:00 PM AEST</SelectItem>
                  <SelectItem value="15:00">3:00 PM AEST</SelectItem>
                  <SelectItem value="16:00">4:00 PM AEST</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <Button
            type="submit"
            className="w-full h-11 bg-[#2563eb] text-white hover:bg-[#2563eb]/90"
          >
            Confirm Booking
          </Button>

          <p className="text-center text-xs text-gray-400">
            No spam. We&apos;ll only use your details to arrange this demo.
          </p>
        </form>
      </div>
    </section>
  );
}
