"use client";

import { useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { registerClient, uploadFile } from "@/lib/api";
import {
  Building2Icon,
  ChevronRightIcon,
  ChevronLeftIcon,
  UploadIcon,
  FileIcon,
  XIcon,
  PenToolIcon,
  CheckCircleIcon,
  Loader2Icon,
  AlertCircleIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";

const industries = [
  "Transport & Logistics",
  "Construction",
  "Healthcare",
  "Retail",
  "Manufacturing",
  "Financial Services",
  "Technology",
  "Energy & Utilities",
  "Government",
  "Education",
  "Hospitality",
  "Other",
];

const carriers = [
  "Telstra",
  "Optus",
  "Vodafone",
  "TPG Telecom",
  "T-Mobile",
  "Verizon",
  "AT&T",
  "Other",
];

const steps = [
  { id: 1, label: "Company Profile", icon: Building2Icon },
  { id: 2, label: "Legal Authorization", icon: PenToolIcon },
  { id: 3, label: "Upload Invoices", icon: UploadIcon },
];

export default function PortalPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [clientId, setClientId] = useState<string | null>(null);

  // Step 1: Company profile
  const [companyName, setCompanyName] = useState("");
  const [abn, setAbn] = useState("");
  const [industry, setIndustry] = useState("");
  const [fleetSize, setFleetSize] = useState("");
  const [carrier, setCarrier] = useState("");

  // Step 2: Legal auth
  const [authorizedName, setAuthorizedName] = useState("");
  const [consentChecked, setConsentChecked] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [hasSignature, setHasSignature] = useState(false);

  // Step 3: File upload
  const [files, setFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  /* ── Canvas signature ── */
  const startDrawing = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
      setIsDrawing(true);
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      const rect = canvas.getBoundingClientRect();
      const x =
        "touches" in e
          ? e.touches[0].clientX - rect.left
          : e.clientX - rect.left;
      const y =
        "touches" in e
          ? e.touches[0].clientY - rect.top
          : e.clientY - rect.top;
      ctx.beginPath();
      ctx.moveTo(x, y);
    },
    []
  );

  const draw = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
      if (!isDrawing) return;
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      const rect = canvas.getBoundingClientRect();
      const x =
        "touches" in e
          ? e.touches[0].clientX - rect.left
          : e.clientX - rect.left;
      const y =
        "touches" in e
          ? e.touches[0].clientY - rect.top
          : e.clientY - rect.top;
      ctx.lineWidth = 2;
      ctx.lineCap = "round";
      ctx.strokeStyle = "#0a1628";
      ctx.lineTo(x, y);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(x, y);
      setHasSignature(true);
    },
    [isDrawing]
  );

  const stopDrawing = useCallback(() => {
    setIsDrawing(false);
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (ctx) ctx.beginPath();
  }, []);

  const clearSignature = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (ctx) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
    setHasSignature(false);
  }, []);

  const getSignatureData = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return "";
    return canvas.toDataURL("image/png");
  }, []);

  /* ── File upload handlers ── */
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFiles = Array.from(e.dataTransfer.files).filter((f) =>
      [".csv", ".pdf", ".xlsx"].some((ext) => f.name.endsWith(ext))
    );
    setFiles((prev) => [...prev, ...droppedFiles]);
  }, []);

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files) {
        setFiles((prev) => [...prev, ...Array.from(e.target.files!)]);
      }
    },
    []
  );

  const removeFile = useCallback((index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const removeAllFiles = useCallback(() => setFiles([]), []);

  /* ── Navigation ── */
  const canProceedStep1 =
    companyName.trim() && abn.trim() && industry && fleetSize && carrier;

  const canProceedStep2 = consentChecked && hasSignature && authorizedName.trim();

  const canProceedStep3 = files.length > 0;

  const handleSubmit = async () => {
    if (!canProceedStep3 || !clientId) return;
    setLoading(true);
    setError(null);
    try {
      for (const file of files) {
        await uploadFile(clientId, file);
      }
      router.push(`/dashboard/${clientId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  const handleStep1Next = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await registerClient({
        company_name: companyName,
        abn,
        industry,
        fleet_size: parseInt(fleetSize, 10),
        carrier,
      });
      setClientId(result.client_id);
      setStep(2);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-8 sm:px-6 sm:py-12">
      <div className="mx-auto max-w-2xl">
        {/* Title */}
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold text-gray-900 sm:text-3xl">
            Start Your Audit
          </h1>
          <p className="mt-2 text-sm text-gray-500">
            Complete the three steps below to begin uncovering overcharges
          </p>
        </div>

        {/* Step Indicator */}
        <div className="mb-10 flex items-center justify-center gap-0">
          {steps.map((s, i) => (
            <div key={s.id} className="flex items-center">
              <div className="flex flex-col items-center">
                <div
                  className={cn(
                    "flex h-9 w-9 items-center justify-center rounded-full text-xs font-semibold transition-colors sm:h-10 sm:w-10",
                    step === s.id
                      ? "bg-[#2563eb] text-white"
                      : step > s.id
                        ? "bg-green-500 text-white"
                        : "bg-gray-200 text-gray-400"
                  )}
                >
                  {step > s.id ? (
                    <CheckCircleIcon className="h-5 w-5" />
                  ) : (
                    <s.icon className="h-4 w-4" />
                  )}
                </div>
                <span
                  className={cn(
                    "mt-1 hidden text-xs font-medium sm:block",
                    step >= s.id ? "text-[#2563eb]" : "text-gray-400"
                  )}
                >
                  {s.label}
                </span>
              </div>
              {i < steps.length - 1 && (
                <div
                  className={cn(
                    "mx-2 h-0.5 w-12 sm:w-20",
                    step > s.id ? "bg-green-500" : "bg-gray-200"
                  )}
                />
              )}
            </div>
          ))}
        </div>

        {/* Error */}
        {error && (
          <div className="mb-6 flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            <AlertCircleIcon className="h-4 w-4 shrink-0" />
            {error}
          </div>
        )}

        {/* Step 1: Company Profile */}
        {step === 1 && (
          <Card className="border-0 shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Building2Icon className="h-5 w-5 text-[#2563eb]" />
                Company Profile
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label htmlFor="companyName">Company Name</Label>
                  <Input
                    id="companyName"
                    placeholder="Acme Corp"
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="abn">ABN</Label>
                  <Input
                    id="abn"
                    placeholder="XX XXX XXX XXX"
                    value={abn}
                    onChange={(e) => setAbn(e.target.value)}
                  />
                </div>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label>Industry</Label>
                  <Select value={industry} onValueChange={(v) => v && setIndustry(v)}>
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select industry" />
                    </SelectTrigger>
                    <SelectContent>
                      {industries.map((ind) => (
                        <SelectItem key={ind} value={ind}>
                          {ind}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="fleetSize">Fleet Size (devices)</Label>
                  <Input
                    id="fleetSize"
                    type="number"
                    placeholder="e.g. 250"
                    value={fleetSize}
                    onChange={(e) => setFleetSize(e.target.value)}
                  />
                </div>
              </div>
              <div className="space-y-1.5">
                <Label>Primary Carrier</Label>
                <Select value={carrier} onValueChange={(v) => v && setCarrier(v)}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select carrier" />
                  </SelectTrigger>
                  <SelectContent>
                    {carriers.map((c) => (
                      <SelectItem key={c} value={c}>
                        {c}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
            <div className="flex justify-end border-t px-6 py-4">
              <Button
                onClick={handleStep1Next}
                disabled={!canProceedStep1 || loading}
              >
                {loading ? (
                  <Loader2Icon className="mr-2 h-4 w-4 animate-spin" />
                ) : null}
                Next — Legal Authorization
                <ChevronRightIcon className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </Card>
        )}

        {/* Step 2: Legal Authorization */}
        {step === 2 && (
          <Card className="border-0 shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <PenToolIcon className="h-5 w-5 text-[#2563eb]" />
                Legal Authorization
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-xs leading-relaxed text-gray-600">
                <p className="mb-2 font-semibold text-gray-900">
                  Letter of Authority
                </p>
                <p>
                  I/We, the undersigned, being a duly authorized representative
                  of the Company, hereby authorize 1st 4 Mobile to act as our
                  agent for the purpose of reviewing, auditing, and disputing
                  charges on our corporate mobile and fleet data invoices with
                  the nominated carrier(s).
                </p>
                <p className="mt-2">
                  This authority includes accessing billing records, usage data,
                  and contract terms for the sole purpose of identifying
                  overcharges and submitting disputes on our behalf.
                </p>
                <p className="mt-2">
                  I confirm that I have the legal authority to bind the Company
                  to this agreement.
                </p>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="authorizedName">Authorized Person Name</Label>
                <Input
                  id="authorizedName"
                  placeholder="Full name as per company records"
                  value={authorizedName}
                  onChange={(e) => setAuthorizedName(e.target.value)}
                />
              </div>

              {/* Signature Pad */}
              <div className="space-y-1.5">
                <Label>Signature</Label>
                <div className="relative">
                  <canvas
                    ref={canvasRef}
                    width={500}
                    height={150}
                    className="w-full rounded-lg border border-gray-300 bg-white"
                    style={{ touchAction: "none" }}
                    onMouseDown={startDrawing}
                    onMouseMove={draw}
                    onMouseUp={stopDrawing}
                    onMouseLeave={stopDrawing}
                    onTouchStart={startDrawing}
                    onTouchMove={draw}
                    onTouchEnd={stopDrawing}
                  />
                  {!hasSignature && (
                    <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
                      <span className="text-xs text-gray-400">
                        Sign above using mouse or touch
                      </span>
                    </div>
                  )}
                </div>
                {hasSignature && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={clearSignature}
                    className="h-7 text-xs text-gray-500"
                  >
                    <XIcon className="mr-1 h-3 w-3" />
                    Clear
                  </Button>
                )}
              </div>

              <div className="flex items-start gap-2">
                <Checkbox
                  id="consent"
                  checked={consentChecked}
                  onCheckedChange={(v) => setConsentChecked(v === true)}
                />
                <Label htmlFor="consent" className="text-xs leading-relaxed text-gray-600">
                  I confirm that I have read and understood the Letter of
                  Authority above and have the legal authority to bind the
                  Company.
                </Label>
              </div>
            </CardContent>
            <div className="flex items-center justify-between border-t px-6 py-4">
              <Button variant="ghost" onClick={() => setStep(1)}>
                <ChevronLeftIcon className="mr-2 h-4 w-4" />
                Back
              </Button>
              <Button
                onClick={() => setStep(3)}
                disabled={!canProceedStep2}
              >
                Next — Upload Invoices
                <ChevronRightIcon className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </Card>
        )}

        {/* Step 3: File Upload */}
        {step === 3 && (
          <Card className="border-0 shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <UploadIcon className="h-5 w-5 text-[#2563eb]" />
                Upload Invoices
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Drop zone */}
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={cn(
                  "flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 text-center transition-colors",
                  isDragging
                    ? "border-[#2563eb] bg-[#2563eb]/5"
                    : "border-gray-300 bg-gray-50 hover:border-gray-400"
                )}
              >
                <UploadIcon className="mb-3 h-8 w-8 text-gray-400" />
                <p className="text-sm font-medium text-gray-700">
                  Drag & drop your invoices here
                </p>
                <p className="mt-1 text-xs text-gray-400">
                  or click to browse files
                </p>
                <p className="mt-2 text-xs text-gray-400">
                  Accepted formats: CSV, PDF, XLSX
                </p>
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept=".csv,.pdf,.xlsx"
                  className="hidden"
                  onChange={handleFileChange}
                />
              </div>

              {/* File list */}
              {files.length > 0 && (
                <div className="rounded-lg border border-gray-200">
                  <div className="flex items-center justify-between border-b px-4 py-2">
                    <span className="text-xs font-medium text-gray-700">
                      {files.length} file{files.length !== 1 ? "s" : ""}{" "}
                      selected
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={removeAllFiles}
                      className="h-6 text-xs text-gray-500"
                    >
                      Remove all
                    </Button>
                  </div>
                  <div className="divide-y divide-gray-100">
                    {files.map((file, i) => (
                      <div
                        key={i}
                        className="flex items-center justify-between px-4 py-2.5"
                      >
                        <div className="flex items-center gap-2">
                          <FileIcon className="h-4 w-4 text-[#2563eb]" />
                          <span className="text-sm text-gray-700">
                            {file.name}
                          </span>
                          <span className="text-xs text-gray-400">
                            {formatFileSize(file.size)}
                          </span>
                        </div>
                        <button
                          onClick={() => removeFile(i)}
                          className="text-gray-400 hover:text-red-500"
                        >
                          <XIcon className="h-4 w-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
            <div className="flex items-center justify-between border-t px-6 py-4">
              <Button variant="ghost" onClick={() => setStep(2)}>
                <ChevronLeftIcon className="mr-2 h-4 w-4" />
                Back
              </Button>
              <Button
                onClick={handleSubmit}
                disabled={!canProceedStep3 || loading}
                className="bg-[#2563eb] text-white hover:bg-[#2563eb]/90"
              >
                {loading ? (
                  <Loader2Icon className="mr-2 h-4 w-4 animate-spin" />
                ) : null}
                Start Audit
              </Button>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
