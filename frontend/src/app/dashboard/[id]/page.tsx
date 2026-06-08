"use client";

import { useState, useEffect, useMemo } from "react";
import { useParams } from "next/navigation";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Progress, ProgressLabel, ProgressTrack, ProgressIndicator,
} from "@/components/ui/progress";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { getDashboard, downloadReport, runAudit, type DashboardData } from "@/lib/api";
import {
  DollarSignIcon,
  TrendingDownIcon,
  ShieldCheckIcon,
  DownloadIcon,
  SearchIcon,
  ArrowUpDownIcon,
  Loader2Icon,
  AlertCircleIcon,
  CheckCircleIcon,
  ZapIcon,
  FileTextIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";

const statusConfig: Record<string, { label: string; color: string; icon: typeof ShieldCheckIcon }> = {
  completed: { label: "Audit Complete", color: "bg-green-100 text-green-700 border-green-200", icon: CheckCircleIcon },
  processing: { label: "Processing", color: "bg-blue-100 text-blue-700 border-blue-200", icon: Loader2Icon },
  pending: { label: "Pending", color: "bg-yellow-100 text-yellow-700 border-yellow-200", icon: AlertCircleIcon },
  error: { label: "Error", color: "bg-red-100 text-red-700 border-red-200", icon: AlertCircleIcon },
};

const engineColors: Record<string, string> = {
  "Rate Plan Optimiser": "bg-blue-500",
  "Data Usage Anomaly": "bg-emerald-500",
  "Roaming Revenue Shield": "bg-violet-500",
  "Device Subsidy Audit": "bg-amber-500",
  "Contract Compliance": "bg-rose-500",
};

export default function DashboardPage() {
  const params = useParams();
  const id = params.id as string;
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortField, setSortField] = useState<string>("date");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [downloading, setDownloading] = useState(false);
  const [auditLoading, setAuditLoading] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await getDashboard(id);
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load dashboard");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id]);

  const handleDownload = async () => {
    setDownloading(true);
    try {
      const blob = await downloadReport(id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `audit-report-${id}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      // Silently handle — endpoint will be built
    } finally {
      setDownloading(false);
    }
  };

  const handleRunAudit = async () => {
    setAuditLoading(true);
    try {
      await runAudit(id);
      // Refresh
      const result = await getDashboard(id);
      setData(result);
    } catch {
      // Silently handle
    } finally {
      setAuditLoading(false);
    }
  };

  const filteredAndSortedDiscrepancies = useMemo(() => {
    if (!data?.discrepancies) return [];
    let items = [...data.discrepancies];
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      items = items.filter(
        (d) =>
          d.description.toLowerCase().includes(q) ||
          d.invoice_ref.toLowerCase().includes(q) ||
          d.category.toLowerCase().includes(q)
      );
    }
    items.sort((a, b) => {
      let cmp = 0;
      if (sortField === "amount") cmp = a.amount - b.amount;
      else if (sortField === "date") cmp = a.date.localeCompare(b.date);
      else if (sortField === "description") cmp = a.description.localeCompare(b.description);
      else if (sortField === "category") cmp = a.category.localeCompare(b.category);
      return sortDir === "asc" ? cmp : -cmp;
    });
    return items;
  }, [data?.discrepancies, searchQuery, sortField, sortDir]);

  const toggleSort = (field: string) => {
    if (sortField === field) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDir("asc");
    }
  };

  const status = data?.status || "pending";
  const statusInfo = statusConfig[status] || statusConfig.pending;

  // Loading state
  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <Loader2Icon className="h-8 w-8 animate-spin text-[#2563eb]" />
          <p className="text-sm text-gray-500">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center px-4">
        <div className="flex flex-col items-center gap-3 text-center">
          <AlertCircleIcon className="h-10 w-10 text-red-400" />
          <h2 className="text-lg font-semibold text-gray-900">Failed to Load Dashboard</h2>
          <p className="text-sm text-gray-500">{error}</p>
          <Button variant="outline" onClick={() => window.location.reload()}>
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-6 sm:px-6 sm:py-8">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-6 flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
          <div>
            <h1 className="text-xl font-bold text-gray-900 sm:text-2xl">
              {data?.company_name || "Dashboard"}
            </h1>
            <p className="text-sm text-gray-500">Audit Overview</p>
          </div>
          <div className="flex flex-wrap gap-3">
            {data?.status === "pending" && (
              <Button
                onClick={handleRunAudit}
                disabled={auditLoading}
                className="bg-[#2563eb] text-white hover:bg-[#2563eb]/90"
              >
                {auditLoading ? (
                  <Loader2Icon className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <ZapIcon className="mr-2 h-4 w-4" />
                )}
                Run Audit
              </Button>
            )}
            <Button
              variant="outline"
              onClick={handleDownload}
              disabled={downloading}
            >
              {downloading ? (
                <Loader2Icon className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <DownloadIcon className="mr-2 h-4 w-4" />
              )}
              Download Report
            </Button>
          </div>
        </div>

        {/* Stat cards */}
        <div className="mb-6 grid gap-4 sm:grid-cols-3">
          <Card className="border-0 shadow-sm">
            <CardContent className="flex items-center gap-4 p-5">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-red-50">
                <DollarSignIcon className="h-6 w-6 text-red-500" />
              </div>
              <div>
                <p className="text-xs font-medium text-gray-500">
                  Total Overcharges
                </p>
                <p className="text-2xl font-bold text-gray-900">
                  ${(data?.total_overcharges ?? 0).toLocaleString()}
                </p>
              </div>
            </CardContent>
          </Card>
          <Card className="border-0 shadow-sm">
            <CardContent className="flex items-center gap-4 p-5">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-green-50">
                <TrendingDownIcon className="h-6 w-6 text-green-500" />
              </div>
              <div>
                <p className="text-xs font-medium text-gray-500">
                  Annualized Savings
                </p>
                <p className="text-2xl font-bold text-gray-900">
                  ${(data?.annualized_savings ?? 0).toLocaleString()}
                </p>
              </div>
            </CardContent>
          </Card>
          <Card className="border-0 shadow-sm">
            <CardContent className="flex items-center gap-4 p-5">
              <div className={cn("flex h-12 w-12 items-center justify-center rounded-xl", statusInfo.color.split(" ")[0])}>
                <statusInfo.icon
                  className={cn(
                    "h-6 w-6",
                    status === "completed" ? "text-green-500" : status === "processing" ? "text-blue-500" : status === "error" ? "text-red-500" : "text-yellow-500"
                  )}
                />
              </div>
              <div>
                <p className="text-xs font-medium text-gray-500">Status</p>
                <Badge variant="outline" className={cn("mt-0.5", statusInfo.color)}>
                  <statusInfo.icon className="mr-1 h-3 w-3" />
                  {statusInfo.label}
                </Badge>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Chart */}
        <Card className="mb-6 border-0 shadow-sm">
          <CardHeader>
            <CardTitle className="text-sm font-semibold">
              Monthly Billing Drift
            </CardTitle>
            <CardDescription>
              Contracted vs actual billing amounts over the last 12 months
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-72">
              {data?.monthly_billing_drift &&
              data.monthly_billing_drift.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={data.monthly_billing_drift}
                    margin={{ top: 5, right: 10, left: 0, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis
                      dataKey="month"
                      tick={{ fontSize: 11 }}
                      stroke="#9ca3af"
                    />
                    <YAxis
                      tick={{ fontSize: 11 }}
                      stroke="#9ca3af"
                      tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
                    />
                    <Tooltip
                      formatter={(value: unknown) => [
                        `$${Number(value).toLocaleString()}`,
                      ]}
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="contracted"
                      stroke="#2563eb"
                      strokeWidth={2}
                      dot={false}
                      name="Contracted"
                    />
                    <Line
                      type="monotone"
                      dataKey="actual"
                      stroke="#ef4444"
                      strokeWidth={2}
                      dot={false}
                      name="Actual Billed"
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex h-full items-center justify-center text-sm text-gray-400">
                  No billing data available yet
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Engine breakdown */}
        <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
          {data?.engine_results?.map((engine) => (
            <Card key={engine.engine} className="border-0 shadow-sm">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-semibold">
                  {engine.engine}
                </CardTitle>
                <CardDescription className="text-xs">
                  {engine.description}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Progress value={engine.confidence}>
                  <div className="flex w-full items-center justify-between">
                    <ProgressLabel className="text-xs">Confidence</ProgressLabel>
                    <span className="ml-auto text-xs text-muted-foreground tabular-nums">
                      {engine.confidence}%
                    </span>
                  </div>
                  <ProgressTrack>
                    <ProgressIndicator
                      className={cn(
                        engineColors[engine.engine] || "bg-primary"
                      )}
                    />
                  </ProgressTrack>
                </Progress>
                <div className="mt-3 flex items-baseline gap-1">
                  <span className="text-lg font-bold text-gray-900">
                    ${engine.overcharge_amount.toLocaleString()}
                  </span>
                  <span className="text-xs text-gray-400">found</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Searchable discrepancy table */}
        <Card className="mb-6 border-0 shadow-sm">
          <CardHeader>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <CardTitle className="text-sm font-semibold">
                Discrepancies Found
              </CardTitle>
              <div className="relative w-full sm:w-64">
                <SearchIcon className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                <Input
                  placeholder="Search invoices, descriptions..."
                  className="h-8 pl-8 text-xs"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {filteredAndSortedDiscrepancies.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead
                      className="cursor-pointer text-xs"
                      onClick={() => toggleSort("invoice_ref")}
                    >
                      Invoice
                      <ArrowUpDownIcon className="ml-1 inline h-3 w-3" />
                    </TableHead>
                    <TableHead
                      className="cursor-pointer text-xs"
                      onClick={() => toggleSort("description")}
                    >
                      Description
                      <ArrowUpDownIcon className="ml-1 inline h-3 w-3" />
                    </TableHead>
                    <TableHead
                      className="cursor-pointer text-xs"
                      onClick={() => toggleSort("category")}
                    >
                      Category
                      <ArrowUpDownIcon className="ml-1 inline h-3 w-3" />
                    </TableHead>
                    <TableHead
                      className="cursor-pointer text-right text-xs"
                      onClick={() => toggleSort("amount")}
                    >
                      Amount
                      <ArrowUpDownIcon className="ml-1 inline h-3 w-3" />
                    </TableHead>
                    <TableHead
                      className="cursor-pointer text-xs"
                      onClick={() => toggleSort("date")}
                    >
                      Date
                      <ArrowUpDownIcon className="ml-1 inline h-3 w-3" />
                    </TableHead>
                    <TableHead className="text-xs">Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredAndSortedDiscrepancies.map((d) => (
                    <TableRow key={d.id}>
                      <TableCell className="text-xs font-medium">
                        {d.invoice_ref}
                      </TableCell>
                      <TableCell className="max-w-xs truncate text-xs">
                        {d.description}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="text-xs">
                          {d.category}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right text-xs font-medium text-red-600">
                        ${d.amount.toLocaleString()}
                      </TableCell>
                      <TableCell className="text-xs text-gray-500">
                        {new Date(d.date).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            d.status === "identified"
                              ? "destructive"
                              : d.status === "disputed"
                                ? "default"
                                : "secondary"
                          }
                          className="text-xs"
                        >
                          {d.status}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <div className="py-8 text-center">
                <FileTextIcon className="mx-auto h-8 w-8 text-gray-300" />
                <p className="mt-2 text-sm text-gray-500">
                  {searchQuery
                    ? "No discrepancies match your search"
                    : "No discrepancies found yet. Run an audit to get started."}
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Submit Dispute panel */}
        <Card className="border-0 shadow-sm">
          <CardHeader>
            <CardTitle className="text-sm font-semibold">
              Submit Dispute
            </CardTitle>
            <CardDescription>
              Review findings and submit a formal dispute to your carrier
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="mb-4 text-sm text-gray-600">
              Our system has prepared a draft dispute letter based on the
              identified overcharges. Review and submit to your carrier directly
              from this dashboard.
            </p>
            <Button className="bg-[#2563eb] text-white hover:bg-[#2563eb]/90">
              <FileTextIcon className="mr-2 h-4 w-4" />
              View &amp; Submit Dispute Letter
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
