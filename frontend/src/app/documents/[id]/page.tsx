"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getDocuments, type DocumentData } from "@/lib/api";
import {
  FileTextIcon,
  FileSpreadsheetIcon,
  FileIcon,
  FileStackIcon,
  DownloadIcon,
  Loader2Icon,
  AlertCircleIcon,
  CalendarIcon,
  HardDriveIcon,
  EyeIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";

const typeConfig: Record<
  string,
  { label: string; icon: typeof FileTextIcon; color: string }
> = {
  dispute_schedule: {
    label: "Dispute Schedule",
    icon: FileSpreadsheetIcon,
    color: "bg-emerald-100 text-emerald-700 border-emerald-200",
  },
  dispute_letter: {
    label: "Dispute Letter",
    icon: FileTextIcon,
    color: "bg-blue-100 text-blue-700 border-blue-200",
  },
  executive_summary: {
    label: "Executive Summary",
    icon: FileIcon,
    color: "bg-violet-100 text-violet-700 border-violet-200",
  },
  evidence_pack: {
    label: "Evidence Pack",
    icon: FileStackIcon,
    color: "bg-amber-100 text-amber-700 border-amber-200",
  },
};

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-AU", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export default function DocumentLockerPage() {
  const params = useParams();
  const id = params.id as string;
  const [documents, setDocuments] = useState<DocumentData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [previewDoc, setPreviewDoc] = useState<DocumentData | null>(null);

  useEffect(() => {
    const fetchDocs = async () => {
      try {
        const result = await getDocuments(id);
        setDocuments(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load documents");
      } finally {
        setLoading(false);
      }
    };
    fetchDocs();
  }, [id]);

  const handleDownload = async (doc: DocumentData) => {
    try {
      const url = doc.download_url.startsWith("http")
        ? doc.download_url
        : `${API_BASE}${doc.download_url}`;
      const res = await fetch(url);
      const blob = await res.blob();
      const blobUrl = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = doc.name;
      a.click();
      URL.revokeObjectURL(blobUrl);
    } catch {
      // Silently handle
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <Loader2Icon className="h-8 w-8 animate-spin text-[#2563eb]" />
          <p className="text-sm text-gray-500">Loading documents...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center px-4">
        <div className="flex flex-col items-center gap-3 text-center">
          <AlertCircleIcon className="h-10 w-10 text-red-400" />
          <h2 className="text-lg font-semibold text-gray-900">
            Failed to Load Documents
          </h2>
          <p className="text-sm text-gray-500">{error}</p>
          <Button variant="outline" onClick={() => window.location.reload()}>
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 px-4 py-8 sm:px-6 sm:py-12">
        <div className="mx-auto max-w-4xl">
          <div className="mb-8">
            <h1 className="text-xl font-bold text-gray-900 sm:text-2xl">
              Document Locker
            </h1>
            <p className="text-sm text-gray-500">
              Generated audit documents and reports
            </p>
          </div>
          <Card className="border-0 shadow-sm">
            <CardContent className="flex flex-col items-center py-16">
              <FileTextIcon className="h-12 w-12 text-gray-300" />
              <h3 className="mt-4 text-sm font-semibold text-gray-900">
                No Documents Yet
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                Documents will appear here once your audit is complete.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-8 sm:px-6 sm:py-12">
      <div className="mx-auto max-w-4xl">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-xl font-bold text-gray-900 sm:text-2xl">
            Document Locker
          </h1>
          <p className="text-sm text-gray-500">
            All generated audit documents for this client
          </p>
        </div>

        {/* Document list */}
        <div className="space-y-4">
          {documents.map((doc) => {
            const config = typeConfig[doc.type] || {
              label: doc.type,
              icon: FileIcon,
              color: "bg-gray-100 text-gray-700 border-gray-200",
            };
            const Icon = config.icon;

            return (
              <Card key={doc.id} className="border-0 shadow-sm transition-shadow hover:shadow-md">
                <CardContent className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex items-start gap-3">
                    <div
                      className={cn(
                        "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl",
                        config.color.split(" ")[0]
                      )}
                    >
                      <Icon className="h-5 w-5" />
                    </div>
                    <div className="min-w-0">
                      <h3 className="text-sm font-semibold text-gray-900">
                        {doc.name}
                      </h3>
                      <div className="mt-1 flex flex-wrap items-center gap-2">
                        <Badge
                          variant="outline"
                          className={cn("text-xs", config.color)}
                        >
                          {config.label}
                        </Badge>
                        <span className="flex items-center gap-1 text-xs text-gray-400">
                          <HardDriveIcon className="h-3 w-3" />
                          {formatFileSize(doc.file_size)}
                        </span>
                        <span className="flex items-center gap-1 text-xs text-gray-400">
                          <CalendarIcon className="h-3 w-3" />
                          {formatDate(doc.generated_at)}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex shrink-0 gap-2">
                    {doc.type === "dispute_letter" && doc.content && (
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-8 text-xs"
                        onClick={() => setPreviewDoc(doc)}
                      >
                        <EyeIcon className="mr-1 h-3 w-3" />
                        Preview
                      </Button>
                    )}
                    {doc.type === "executive_summary" && doc.content && (
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-8 text-xs"
                        onClick={() => setPreviewDoc(doc)}
                      >
                        <EyeIcon className="mr-1 h-3 w-3" />
                        View
                      </Button>
                    )}
                    <Button
                      size="sm"
                      className="h-8 bg-[#2563eb] text-xs text-white hover:bg-[#2563eb]/90"
                      onClick={() => handleDownload(doc)}
                    >
                      <DownloadIcon className="mr-1 h-3 w-3" />
                      Download
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Preview Modal */}
      {previewDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={() => setPreviewDoc(null)}
          />
          <div className="relative z-50 mx-4 w-full max-w-2xl rounded-xl bg-white p-6 shadow-xl">
            <button
              onClick={() => setPreviewDoc(null)}
              className="absolute right-4 top-4 rounded-sm opacity-70 transition-opacity hover:opacity-100"
            >
              <XIcon className="h-4 w-4" />
            </button>

            <h2 className="text-lg font-semibold text-gray-900">
              {previewDoc.name}
            </h2>
            <Badge
              variant="outline"
              className={cn(
                "mt-2 text-xs",
                typeConfig[previewDoc.type]?.color || "bg-gray-100 text-gray-700 border-gray-200"
              )}
            >
              {typeConfig[previewDoc.type]?.label || previewDoc.type}
            </Badge>

            <div className="mt-4">
              {previewDoc.type === "executive_summary" && previewDoc.content ? (
                <div
                  className="prose prose-sm max-w-none rounded-lg border bg-white p-4 text-sm leading-relaxed text-gray-700"
                  dangerouslySetInnerHTML={{ __html: previewDoc.content }}
                />
              ) : (
                <div className="max-h-96 overflow-y-auto rounded-lg border bg-white p-4 font-mono text-xs leading-relaxed text-gray-700">
                  {previewDoc.content || "No preview available."}
                </div>
              )}
            </div>

            <div className="mt-4 flex justify-end">
              <Button
                className="h-8 bg-[#2563eb] text-xs text-white hover:bg-[#2563eb]/90"
                onClick={() => {
                  handleDownload(previewDoc);
                  setPreviewDoc(null);
                }}
              >
                <DownloadIcon className="mr-1 h-3 w-3" />
                Download
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function XIcon(props: React.ComponentProps<"svg">) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <path d="M18 6 6 18" />
      <path d="m6 6 12 12" />
    </svg>
  );
}
