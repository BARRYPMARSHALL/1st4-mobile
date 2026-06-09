"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Progress, ProgressLabel, ProgressTrack, ProgressIndicator } from "@/components/ui/progress";
import { getOwnerDashboard, triggerWorkerAudit, type OwnerDashboardData } from "@/lib/api";
import AuthGuard from "@/components/AuthGuard";
import {
  UsersIcon,
  Loader2Icon,
  ScaleIcon,
  CheckCircleIcon,
  DollarSignIcon,
  TrendingUpIcon,
  AlertCircleIcon,
  EyeIcon,
  ZapIcon,
  BarChart3Icon,
  Building2Icon,
  ClockIcon,
  XIcon,
  DownloadIcon,
  SendIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";

const pipeIcon = (stage: string) => {
  switch (stage) {
    case "leads_uploaded": return UsersIcon;
    case "audits_processing": return Loader2Icon;
    case "disputes_active": return ScaleIcon;
    case "invoices_settled": return CheckCircleIcon;
    default: return BarChart3Icon;
  }
};

const pipeLabel: Record<string, string> = {
  leads_uploaded: "Leads Uploaded",
  audits_processing: "Audits Processing",
  disputes_active: "Disputes Active",
  invoices_settled: "Invoices Settled",
};

const pipeColor: Record<string, string> = {
  leads_uploaded: "border-l-blue-500 bg-blue-50",
  audits_processing: "border-l-amber-500 bg-amber-50",
  disputes_active: "border-l-violet-500 bg-violet-50",
  invoices_settled: "border-l-green-500 bg-green-50",
};

const pipeTextColor: Record<string, string> = {
  leads_uploaded: "text-blue-600",
  audits_processing: "text-amber-600",
  disputes_active: "text-violet-600",
  invoices_settled: "text-green-600",
};

export default function OwnerPage() {
  const [data, setData] = useState<OwnerDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [runningAudit, setRunningAudit] = useState<string | null>(null);
  const [selectedDispute, setSelectedDispute] = useState<{ company_name: string; audit_findings: string; dispute_letter: string; status: string; completed_at: string } | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await getOwnerDashboard();
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load dashboard");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleRunAudit = async (clientId: string) => {
    setRunningAudit(clientId);
    try {
      await triggerWorkerAudit(clientId);
      const result = await getOwnerDashboard();
      setData(result);
    } catch {
      // Silently handle
    } finally {
      setRunningAudit(null);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <Loader2Icon className="h-8 w-8 animate-spin text-[#2563eb]" />
          <p className="text-sm text-gray-500">Loading command center...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center px-4">
        <div className="flex flex-col items-center gap-3 text-center">
          <AlertCircleIcon className="h-10 w-10 text-red-400" />
          <h2 className="text-lg font-semibold text-gray-900">Failed to Load</h2>
          <p className="text-sm text-gray-500">{error}</p>
          <Button variant="outline" onClick={() => window.location.reload()}>
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  const pipeline = data?.pipeline || { total_clients: 0, leads_uploaded: 0, audits_processing: 0, disputes_active: 0, invoices_settled: 0 };
  const cash = data || { total_invoiced: 0, total_collected: 0, outstanding: 0 };
  const feePercentage = 50;

  return (
    <AuthGuard>
    <div className="min-h-screen bg-gray-50 px-4 py-6 sm:px-6 sm:py-8">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-xl font-bold text-gray-900 sm:text-2xl">
            Mission Control
          </h1>
          <p className="text-sm text-gray-500">
            Command center for all audits, disputes, and collections
          </p>
        </div>

        {/* ─── 1. Global Pipeline View ─── */}
        <section className="mb-8">
          <h2 className="mb-4 text-sm font-semibold text-gray-700">
            Global Pipeline
          </h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {Object.entries(pipeline).map(([key, value]) => {
              const Icon = pipeIcon(key);
              return (
                <Card
                  key={key}
                  className={cn(
                    "border-0 border-l-4 shadow-sm",
                    pipeColor[key]
                  )}
                >
                  <CardContent className="p-5">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs font-medium text-gray-500">
                          {pipeLabel[key]}
                        </p>
                        <p
                          className={cn(
                            "mt-1 text-3xl font-bold",
                            pipeTextColor[key]
                          )}
                        >
                          {value}
                        </p>
                      </div>
                      <div
                        className={cn(
                          "flex h-10 w-10 items-center justify-center rounded-full",
                          pipeTextColor[key]
                        )}
                      >
                        <Icon className="h-5 w-5" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </section>

        {/* ─── 2. Client Queue Table ─── */}
        <section className="mb-8">
          <Card className="border-0 shadow-sm">
            <CardHeader>
              <CardTitle className="text-sm font-semibold">
                Client Queue
              </CardTitle>
              <CardDescription>
                All registered clients and their current audit status
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-xs">Company</TableHead>
                    <TableHead className="text-xs">Industry</TableHead>
                    <TableHead className="text-xs">Carrier</TableHead>
                    <TableHead className="text-xs">Status</TableHead>
                    <TableHead className="text-xs">Uploaded</TableHead>
                    <TableHead className="text-xs">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data?.clients?.length ? (
                    data.clients.map((client) => (
                      <TableRow key={client.id}>
                        <TableCell className="text-xs font-medium">
                          <div className="flex items-center gap-2">
                            <Building2Icon className="h-3.5 w-3.5 text-gray-400" />
                            {client.company_name}
                          </div>
                        </TableCell>
                        <TableCell className="text-xs">{client.industry}</TableCell>
                        <TableCell className="text-xs">{client.primary_carrier}</TableCell>
                        <TableCell>
                          <Badge
                            variant={
                              client.status === "completed"
                                ? "default"
                                : client.status === "processing"
                                  ? "secondary"
                                  : "outline"
                            }
                            className="text-xs"
                          >
                            {client.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-xs text-gray-500">
                          {new Date(client.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell>
                          <Button
                            size="sm"
                            variant="outline"
                            disabled={runningAudit === client.id}
                            onClick={() => handleRunAudit(client.id)}
                            className="h-7 text-xs"
                          >
                            {runningAudit === client.id ? (
                              <Loader2Icon className="mr-1 h-3 w-3 animate-spin" />
                            ) : (
                              <ZapIcon className="mr-1 h-3 w-3" />
                            )}
                            Run Audit
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell
                        colSpan={6}
                        className="py-8 text-center text-sm text-gray-400"
                      >
                        No clients registered yet
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </section>

        {/* ─── 3. Recent Activity ─── */}
        <section className="mb-8">
          <Card className="border-0 shadow-sm">
            <CardHeader>
              <CardTitle className="text-sm font-semibold">
                Recent Activity
              </CardTitle>
              <CardDescription>
                Latest client registrations and status changes
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-xs">Company</TableHead>
                    <TableHead className="text-xs">Status</TableHead>
                    <TableHead className="text-xs">Timestamp</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data?.recent_activity?.length ? (
                    data.recent_activity.map((activity, i) => (
                      <TableRow key={i}>
                        <TableCell className="text-xs font-medium">
                          {activity.company_name}
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant="outline"
                            className="text-xs"
                          >
                            {activity.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-xs text-gray-500">
                          {new Date(activity.timestamp).toLocaleDateString()}
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell
                        colSpan={3}
                        className="py-8 text-center text-sm text-gray-400"
                      >
                        No recent activity
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </section>

        {/* ─── 4. Cash Collector ─── */}
        <section>
          <Card className="border-0 shadow-sm">
            <CardHeader>
              <CardTitle className="text-sm font-semibold">
                Cash Collector
              </CardTitle>
              <CardDescription>
                Revenue tracking and fee calculations
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 sm:grid-cols-3">
                <div className="rounded-xl border border-green-100 bg-green-50/50 p-5">
                  <div className="flex items-center gap-2 text-xs font-medium text-green-600">
                    <DollarSignIcon className="h-4 w-4" />
                    Total Invoiced
                  </div>
                  <p className="mt-2 text-2xl font-bold text-green-700">
                    ${cash.total_invoiced.toLocaleString()}
                  </p>
                </div>
                <div className="rounded-xl border border-blue-100 bg-blue-50/50 p-5">
                  <div className="flex items-center gap-2 text-xs font-medium text-blue-600">
                    <TrendingUpIcon className="h-4 w-4" />
                    Total Collected
                  </div>
                  <p className="mt-2 text-2xl font-bold text-blue-700">
                    ${cash.total_collected.toLocaleString()}
                  </p>
                </div>
                <div className="rounded-xl border border-amber-100 bg-amber-50/50 p-5">
                  <div className="flex items-center gap-2 text-xs font-medium text-amber-600">
                    <ClockIcon className="h-4 w-4" />
                    Outstanding
                  </div>
                  <p className="mt-2 text-2xl font-bold text-amber-700">
                    ${cash.outstanding.toLocaleString()}
                  </p>
                </div>
              </div>
              <div className="mt-4 rounded-lg border border-gray-200 bg-gray-50 p-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">
                    Your Fee ({feePercentage}% of collected)
                  </span>
                  <span className="text-lg font-bold text-[#2563eb]">
                    ${((cash.total_collected * feePercentage) / 100).toLocaleString()}
                  </span>
                </div>
                <div className="mt-2">
                  <Progress value={cash.total_invoiced > 0 ? (cash.total_collected / cash.total_invoiced) * 100 : 0}>
                    <div className="flex w-full items-center justify-between">
                      <ProgressLabel className="text-xs">Collection Rate</ProgressLabel>
                      <span className="ml-auto text-xs text-muted-foreground tabular-nums">
                        {cash.total_invoiced > 0
                          ? Math.round((cash.total_collected / cash.total_invoiced) * 100)
                          : 0}
                        %
                      </span>
                    </div>
                    <ProgressTrack>
                      <ProgressIndicator className="bg-emerald-500" />
                    </ProgressTrack>
                  </Progress>
                </div>
              </div>
            </CardContent>
          </Card>
        </section>
      </div>

      {/* ─── Review Modal ─── */}
      {selectedDispute && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={() => setSelectedDispute(null)}
          />
          <div className="relative z-50 mx-4 w-full max-w-2xl rounded-xl bg-white p-6 shadow-xl">
            <button
              onClick={() => setSelectedDispute(null)}
              className="absolute right-4 top-4 rounded-sm opacity-70 transition-opacity hover:opacity-100"
            >
              <XIcon className="h-4 w-4" />
            </button>
            <h2 className="text-lg font-semibold text-gray-900">
              Audit Review — {selectedDispute.company_name}
            </h2>
            <p className="mt-1 text-sm text-gray-500">
              Review audit findings and dispute letter before sending to carrier
            </p>
            <div className="mt-6 space-y-4">
              <div>
                <h4 className="mb-1 text-sm font-semibold text-gray-900">
                  Audit Findings Summary
                </h4>
                <div className="rounded-lg bg-gray-50 p-3 text-sm text-gray-700">
                  {selectedDispute.audit_findings}
                </div>
              </div>
              <div>
                <h4 className="mb-1 text-sm font-semibold text-gray-900">
                  Dispute Letter
                </h4>
                <div className="max-h-60 overflow-y-auto rounded-lg border bg-white p-3 font-mono text-xs leading-relaxed text-gray-700">
                  {selectedDispute.dispute_letter}
                </div>
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-2">
              <Button variant="outline" className="h-8 text-xs">
                <DownloadIcon className="mr-1 h-3 w-3" />
                Download Letter
              </Button>
              <Button className="h-8 bg-[#2563eb] text-xs text-white hover:bg-[#2563eb]/90">
                <SendIcon className="mr-1 h-3 w-3" />
                Send to Carrier
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
    </AuthGuard>
  );
}
