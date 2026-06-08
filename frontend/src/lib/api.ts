const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error: ${res.status}`);
  }
  return res.json();
}

export interface RegisterClientData {
  company_name: string;
  abn: string;
  industry: string;
  fleet_size: number;
  carrier: string;
  contact_email?: string;
  contact_name?: string;
}

export interface AuthorizeData {
  signature: string;
  authorized_name: string;
}

export interface DashboardData {
  client_id: string;
  company_name: string;
  status: string;
  total_overcharges: number;
  annualized_savings: number;
  monthly_billing_drift: Array<{ month: string; contracted: number; actual: number }>;
  engine_results: Array<{
    engine: string;
    description: string;
    confidence: number;
    overcharge_amount: number;
    color?: string;
  }>;
  discrepancies: Array<{
    id: string;
    invoice_ref: string;
    description: string;
    amount: number;
    category: string;
    date: string;
    status: string;
  }>;
}

export interface OwnerDashboardData {
  pipeline: {
    leads_uploaded: number;
    audits_processing: number;
    disputes_active: number;
    invoices_settled: number;
  };
  clients: Array<{
    id: string;
    company_name: string;
    industry: string;
    carrier: string;
    status: string;
    uploaded_at: string;
  }>;
  disputes: Array<{
    id: string;
    company_name: string;
    audit_findings: string;
    dispute_letter: string;
    status: string;
    completed_at: string;
  }>;
  cash_collector: {
    total_invoiced: number;
    total_collected: number;
    outstanding: number;
    fee_percentage: number;
  };
}

export interface DocumentData {
  id: string;
  client_id: string;
  name: string;
  type: 'dispute_schedule' | 'dispute_letter' | 'executive_summary' | 'evidence_pack';
  file_size: number;
  generated_at: string;
  download_url: string;
  content?: string;
}

export async function registerClient(data: RegisterClientData): Promise<{ client_id: string }> {
  return apiFetch('/api/client/register', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function authorizeClient(
  id: string,
  sig: string,
  name: string
): Promise<{ status: string }> {
  return apiFetch(`/api/client/${id}/authorize`, {
    method: 'POST',
    body: JSON.stringify({ signature: sig, authorized_name: name }),
  });
}

export async function uploadFile(
  id: string,
  file: File
): Promise<{ status: string; file_count: number }> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/api/upload?client_id=${id}`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Upload failed');
  }
  return res.json();
}

export async function getDashboard(id: string): Promise<DashboardData> {
  return apiFetch(`/api/client/${id}/dashboard`);
}

export async function runAudit(id: string): Promise<{ status: string; audit_id: string }> {
  return apiFetch(`/api/client/${id}/run-audit`, { method: 'POST' });
}

export async function getDocuments(id: string): Promise<DocumentData[]> {
  return apiFetch(`/api/client/${id}/documents`);
}

export async function getOwnerDashboard(): Promise<OwnerDashboardData> {
  return apiFetch('/api/owner/dashboard');
}

export async function triggerWorkerAudit(
  id: string
): Promise<{ status: string; audit_id: string }> {
  return apiFetch(`/api/owner/client/${id}/run-audit`, { method: 'POST' });
}

export async function downloadReport(id: string): Promise<Blob> {
  const res = await fetch(`${API_BASE}/api/client/${id}/download-report`);
  if (!res.ok) throw new Error('Download failed');
  return res.blob();
}
