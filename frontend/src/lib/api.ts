const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

let _authToken: string | null = null;

export function setAuthToken(token: string | null) {
  _authToken = token;
  if (token) {
    localStorage.setItem('1st4_auth_token', token);
  } else {
    localStorage.removeItem('1st4_auth_token');
  }
}

export function getAuthToken(): string | null {
  if (!_authToken && typeof window !== 'undefined') {
    _authToken = localStorage.getItem('1st4_auth_token');
  }
  return _authToken;
}

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string>),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
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
    total_clients: number;
    leads_uploaded: number;
    audits_processing: number;
    disputes_active: number;
    invoices_settled: number;
  };
  clients: Array<{
    id: string;
    company_name: string;
    abn?: string;
    industry: string;
    fleet_size: number;
    primary_carrier: string;
    email?: string;
    status: string;
    created_at: string;
    updated_at: string;
    authorized_at?: string | null;
    authorized_by?: string | null;
  }>;
  total_invoiced: number;
  total_collected: number;
  outstanding: number;
  recent_activity: Array<{
    client_id: string;
    company_name: string;
    status: string;
    timestamp: string;
  }>;
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

export interface BookingData {
  name: string;
  email: string;
  company: string;
  phone?: string;
  employees?: string;
  date: string;
  time: string;
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
  const raw: any = await apiFetch('/api/owner/dashboard');
  return {
    pipeline: raw.pipeline_stats,
    clients: raw.client_queue?.map((c: any) => ({
      ...c,
      primary_carrier: c.primary_carrier || "",
      created_at: c.created_at,
      updated_at: c.updated_at,
    })) || [],
    total_invoiced: raw.total_invoiced || 0,
    total_collected: raw.total_collected || 0,
    outstanding: raw.outstanding || 0,
    recent_activity: raw.recent_activity || [],
  };
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

export interface BookingResponse {
  status: string;
  message: string;
  booking_id: string;
}

export async function submitBooking(data: BookingData): Promise<BookingResponse> {
  return apiFetch('/api/book', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
