// Thin client for the SENTRY backend (src/execution/router.py).
// Base URL comes from VITE_API_URL, defaulting to the local docker-compose port.

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export type Decision = "ALLOW" | "BLOCK" | "CONFIRM";
export type Severity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface ExecuteRequestPayload {
  agent_name: string;
  tool_name: string;
  action: string;
  parameters?: Record<string, unknown>;
  requested_scope?: string | null;
  allowed_scopes?: string[];
  estimated_cost_usd?: number | null;
  is_irreversible?: boolean;
  user_confirmed?: boolean;
  recent_requests_count?: number;
  context?: Record<string, unknown>;
}

export interface RuleResult {
  rule: string;
  policy_code: string;
  passed: boolean;
  severity: Severity;
  reason: string;
  suggested_fix: string | null;
}

export interface ExecuteResponse {
  risk_score: number;
  decision: Decision;
  reason: string;
  violated_policy: string | null;
  suggested_fix: string | null;
  confidence_score: number;
  audit_log_id: string;
  approval_request_id: string | null;
  rule_results: RuleResult[];
  execution_time_ms: number;
}

export interface AuditEntry {
  id: string;
  timestamp: string;
  agent_name: string;
  tool_name: string;
  action: string;
  decision: Decision;
  risk_score: number;
  reason: string | null;
  violated_policy: string | null;
  suggested_fix: string | null;
  execution_time_ms: number | null;
  request_payload: Record<string, unknown> | null;
  response_payload: Record<string, unknown> | null;
  approval_request_id: string | null;
  approval_status: "PENDING" | "APPROVED" | "REJECTED" | null;
}

export interface AuditListResponse {
  items: AuditEntry[];
  total: number;
  limit: number;
  offset: number;
}

export interface StatsResponse {
  total_requests: number;
  allowed_requests: number;
  blocked_requests: number;
  confirmation_requests: number;
  average_risk_score: number;
  average_execution_time_ms: number;
  high_risk_requests: number;
}

export interface PolicyResponse {
  id: string;
  policy_code: string;
  name: string;
  description: string;
  severity: Severity;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`SENTRY API ${res.status}: ${body || res.statusText}`);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  execute: (payload: ExecuteRequestPayload) =>
    request<ExecuteResponse>("/execute", { method: "POST", body: JSON.stringify(payload) }),

  listAudit: (params: { limit?: number; offset?: number } = {}) => {
    const qs = new URLSearchParams();
    if (params.limit) qs.set("limit", String(params.limit));
    if (params.offset) qs.set("offset", String(params.offset));
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return request<AuditListResponse>(`/audit${suffix}`);
  },

  getStats: () => request<StatsResponse>("/stats"),

  listPolicies: () => request<PolicyResponse[]>("/policies"),

  decideApproval: (id: string, status: "APPROVED" | "REJECTED", approvedBy = "A. Chen") =>
    request<unknown>(`/approve/${id}`, {
      method: "POST",
      body: JSON.stringify({ status, approved_by: approvedBy }),
    }),
};

export { API_URL };
