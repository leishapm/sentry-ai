import { useState, useEffect, useRef } from "react";
import {
  LayoutDashboard, Activity, ClipboardList, ShieldAlert,
  FileText, BarChart2, Settings, ChevronLeft, ChevronRight,
  Bell, User, Shield, CheckCircle2, XCircle, Clock,
  AlertTriangle, Check, X, ChevronDown, Zap, Bot,
  Terminal, Database, Globe, Mail, Cpu, TrendingUp,
  Filter, Search, Play, Lock, RefreshCw, Eye, ArrowRight,
  Layers, GitBranch, ToggleLeft, ToggleRight,
} from "lucide-react";

// ─── Types ────────────────────────────────────────────────────────────────────
type Decision = "ALLOW" | "BLOCK" | "CONFIRM";
type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
type Page = "dashboard" | "live" | "queue" | "policies" | "audit" | "analytics" | "settings";

interface AIRequest {
  id: string;
  agentName: string;
  action: string;
  tool: string;
  riskLevel: RiskLevel;
  riskScore: number;
  decision: Decision;
  reason: string;
  policyViolated: string | null;
  suggestedFix: string;
  timestamp: string;
  toolIcon: string;
  confidence: number;
}

interface ApprovalItem {
  id: string;
  agentName: string;
  action: string;
  tool: string;
  riskLevel: RiskLevel;
  riskScore: number;
  requestedAt: string;
  details: string;
  reason: string;
}

interface AuditRow {
  id: string;
  time: string;
  agent: string;
  action: string;
  tool: string;
  decision: Decision;
  risk: RiskLevel;
  policy: string;
  reason: string;
  status: "completed" | "pending" | "overridden";
}

interface Policy {
  id: string;
  name: string;
  description: string;
  category: string;
  severity: RiskLevel;
  enabled: boolean;
  triggered: number;
}

// ─── Constants ────────────────────────────────────────────────────────────────
const C = {
  allow: "#22c55e",
  block: "#ef4444",
  confirm: "#facc15",
  blue: "#3b82f6",
  bg: "#0f172a",
  panel: "#1e293b",
  border: "rgba(148,163,184,0.1)",
  muted: "#64748b",
  fg: "#e2e8f0",
};

// ─── Seed Data ────────────────────────────────────────────────────────────────
const SEED_REQUESTS: AIRequest[] = [
  {
    id: "r1", agentName: "Sales Assistant", action: "Delete Customer Record",
    tool: "PostgreSQL CRM", riskLevel: "CRITICAL", riskScore: 92,
    decision: "BLOCK", reason: "Agent attempted to modify records outside its approved scope.",
    policyViolated: "RBAC-04", suggestedFix: "Request elevated permissions via IAM portal.",
    timestamp: "14:32:18", toolIcon: "database", confidence: 97,
  },
  {
    id: "r2", agentName: "Finance Bot", action: "Transfer $48,000",
    tool: "Stripe Payments", riskLevel: "HIGH", riskScore: 87,
    decision: "CONFIRM", reason: "Transaction exceeds $10,000 approval threshold.",
    policyViolated: "PAYMENT-01", suggestedFix: "Route through dual-auth workflow.",
    timestamp: "14:31:55", toolIcon: "zap", confidence: 94,
  },
  {
    id: "r3", agentName: "Data Analyst", action: "Read Inventory Table",
    tool: "BigQuery", riskLevel: "LOW", riskScore: 12,
    decision: "ALLOW", reason: "Read access to approved dataset within scope.",
    policyViolated: null, suggestedFix: "No action required.",
    timestamp: "14:31:40", toolIcon: "database", confidence: 99,
  },
  {
    id: "r4", agentName: "Email Copilot", action: "Send Company-Wide Email",
    tool: "SendGrid", riskLevel: "MEDIUM", riskScore: 55,
    decision: "CONFIRM", reason: "Mass email to >500 recipients requires review.",
    policyViolated: "EMAIL-02", suggestedFix: "Verify recipient list and content before approving.",
    timestamp: "14:30:59", toolIcon: "mail", confidence: 89,
  },
  {
    id: "r5", agentName: "DevOps Agent", action: "Execute Shell Script",
    tool: "Bash Runner", riskLevel: "CRITICAL", riskScore: 96,
    decision: "BLOCK", reason: "Unrestricted shell access with root privileges detected.",
    policyViolated: "INFRA-07", suggestedFix: "Use sandboxed execution environment.",
    timestamp: "14:30:44", toolIcon: "terminal", confidence: 99,
  },
  {
    id: "r6", agentName: "Web Scraper", action: "HTTP GET /products",
    tool: "Fetch API", riskLevel: "LOW", riskScore: 8,
    decision: "ALLOW", reason: "Request to pre-approved domain within rate limits.",
    policyViolated: null, suggestedFix: "No action required.",
    timestamp: "14:30:10", toolIcon: "globe", confidence: 99,
  },
];

const SEED_QUEUE: ApprovalItem[] = [
  {
    id: "q1", agentName: "Finance Bot", action: "Transfer $48,000",
    tool: "Stripe Payments", riskLevel: "HIGH", riskScore: 87,
    requestedAt: "14:31:55", reason: "Transaction exceeds $10,000 threshold — irreversible financial action.",
    details: "Transfer $48,000.00 from ops-account-7821 → vendor-payout-332. Memo: Q3 Contract Settlement.",
  },
  {
    id: "q2", agentName: "Email Copilot", action: "Send Company-Wide Email",
    tool: "SendGrid", riskLevel: "MEDIUM", riskScore: 55,
    requestedAt: "14:30:59", reason: "Mass communication to all 847 employees requires human verification.",
    details: "To: all-staff@corp.com · Subject: Urgent: Security Policy Update · Body: 3 paragraphs, 1 attachment.",
  },
  {
    id: "q3", agentName: "HR Agent", action: "Export Employee PII",
    tool: "Workday API", riskLevel: "CRITICAL", riskScore: 94,
    requestedAt: "14:29:10", reason: "PII export to external partner requires GDPR approval.",
    details: "Export 2,841 employee records (name, DOB, salary) → s3://partner-audits/Q3-2024.csv",
  },
];

const SEED_AUDIT: AuditRow[] = [
  { id: "a1", time: "14:32:18", agent: "Sales Assistant", action: "Delete Customer Record", tool: "PostgreSQL CRM", decision: "BLOCK", risk: "CRITICAL", policy: "RBAC-04", reason: "Outside approved scope", status: "completed" },
  { id: "a2", time: "14:31:55", agent: "Finance Bot", action: "Transfer $48,000", tool: "Stripe", decision: "CONFIRM", risk: "HIGH", policy: "PAYMENT-01", reason: "Exceeds threshold", status: "pending" },
  { id: "a3", time: "14:31:40", agent: "Data Analyst", action: "Read Inventory Table", tool: "BigQuery", decision: "ALLOW", risk: "LOW", policy: "—", reason: "Within approved scope", status: "completed" },
  { id: "a4", time: "14:30:59", agent: "Email Copilot", action: "Send Mass Email", tool: "SendGrid", decision: "CONFIRM", risk: "MEDIUM", policy: "EMAIL-02", reason: "Mass communication", status: "pending" },
  { id: "a5", time: "14:30:44", agent: "DevOps Agent", action: "Execute Shell Script", tool: "Bash Runner", decision: "BLOCK", risk: "CRITICAL", policy: "INFRA-07", reason: "Unrestricted shell access", status: "completed" },
  { id: "a6", time: "14:30:10", agent: "Web Scraper", action: "HTTP GET /products", tool: "Fetch API", decision: "ALLOW", risk: "LOW", policy: "—", reason: "Pre-approved domain", status: "completed" },
  { id: "a7", time: "14:29:10", agent: "HR Agent", action: "Export Employee PII", tool: "Workday API", decision: "CONFIRM", risk: "CRITICAL", policy: "GDPR-03", reason: "PII export to external", status: "pending" },
  { id: "a8", time: "14:28:35", agent: "Research Bot", action: "Web Search", tool: "Bing API", decision: "ALLOW", risk: "LOW", policy: "—", reason: "Read-only web access", status: "completed" },
];

const SEED_POLICIES: Policy[] = [
  { id: "RBAC-04", name: "Role-Based Record Access", description: "Sales assistants cannot delete or modify customer records outside their assigned accounts.", category: "Access Control", severity: "CRITICAL", enabled: true, triggered: 14 },
  { id: "PAYMENT-01", name: "High-Value Transaction Gate", description: "Transactions above $10,000 require dual human authorization before execution.", category: "Financial", severity: "HIGH", enabled: true, triggered: 8 },
  { id: "EMAIL-02", name: "Mass Communication Review", description: "Emails sent to more than 100 recipients require explicit human approval.", category: "Communication", severity: "MEDIUM", enabled: true, triggered: 5 },
  { id: "INFRA-07", name: "Sandboxed Execution Only", description: "All shell and code execution must occur within approved sandboxed environments.", category: "Infrastructure", severity: "CRITICAL", enabled: true, triggered: 22 },
  { id: "GDPR-03", name: "PII Export Controls", description: "Exports containing personally identifiable information require legal & compliance sign-off.", category: "Compliance", severity: "CRITICAL", enabled: true, triggered: 3 },
  { id: "API-05", name: "Rate Limit Enforcement", description: "API calls exceeding 1,000 req/min are automatically throttled and flagged.", category: "API", severity: "MEDIUM", enabled: true, triggered: 31 },
  { id: "DATA-09", name: "Database Write Scope", description: "Write operations on production databases require change-ticket reference.", category: "Data", severity: "HIGH", enabled: false, triggered: 0 },
];

const RISK_TIMELINE = [
  { t: "13:00", v: 22 }, { t: "13:10", v: 35 }, { t: "13:20", v: 28 },
  { t: "13:30", v: 41 }, { t: "13:40", v: 38 }, { t: "13:50", v: 52 },
  { t: "14:00", v: 61 }, { t: "14:10", v: 48 }, { t: "14:20", v: 67 },
  { t: "14:30", v: 74 }, { t: "14:32", v: 71 },
];

const BLOCKED_AGENTS = [
  { name: "DevOps Agent", count: 22 },
  { name: "Sales Assistant", count: 14 },
  { name: "Finance Bot", count: 9 },
  { name: "HR Agent", count: 6 },
  { name: "Email Copilot", count: 4 },
];

const POLICY_HEATMAP = [
  { policy: "INFRA-07", mon: 4, tue: 6, wed: 3, thu: 5, fri: 4 },
  { policy: "RBAC-04",  mon: 3, tue: 2, wed: 4, thu: 3, fri: 2 },
  { policy: "PAYMENT-01", mon: 1, tue: 2, wed: 1, thu: 2, fri: 2 },
  { policy: "EMAIL-02", mon: 1, tue: 1, wed: 2, thu: 0, fri: 1 },
  { policy: "API-05",   mon: 7, tue: 8, wed: 6, thu: 9, fri: 1 },
];

const DIST_DATA = [
  { name: "ALLOW", value: 58, fill: C.allow },
  { name: "BLOCK", value: 24, fill: C.block },
  { name: "CONFIRM", value: 18, fill: C.confirm },
];

const SPARKLINE_ALLOWED = [42, 48, 45, 55, 58, 62, 59, 67, 71, 68, 74];
const SPARKLINE_BLOCKED = [12, 15, 11, 18, 14, 22, 19, 16, 21, 17, 24];
const SPARKLINE_PENDING = [3, 4, 2, 5, 3, 4, 6, 3, 5, 4, 3];
const SPARKLINE_RISK = [38, 42, 35, 48, 44, 52, 47, 55, 51, 57, 43];

// ─── Helpers ──────────────────────────────────────────────────────────────────
const decisionColor = (d: Decision) =>
  d === "ALLOW" ? C.allow : d === "BLOCK" ? C.block : C.confirm;

const decisionBg = (d: Decision) =>
  d === "ALLOW" ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/25"
  : d === "BLOCK" ? "bg-red-500/10 text-red-400 border-red-500/25"
  : "bg-yellow-400/10 text-yellow-400 border-yellow-400/25";

const riskCls = (r: RiskLevel) =>
  r === "LOW" ? "text-emerald-400 bg-emerald-500/10"
  : r === "MEDIUM" ? "text-yellow-400 bg-yellow-400/10"
  : r === "HIGH" ? "text-orange-400 bg-orange-500/10"
  : "text-red-400 bg-red-500/10";

const DecisionIcon = ({ d, size = 12 }: { d: Decision; size?: number }) =>
  d === "ALLOW" ? <CheckCircle2 size={size} className="text-emerald-400" />
  : d === "BLOCK" ? <XCircle size={size} className="text-red-400" />
  : <Clock size={size} className="text-yellow-400" />;

const ToolIcon = ({ name }: { name: string }) => {
  const cls = "size-4 text-blue-400";
  if (name === "terminal") return <Terminal className={cls} />;
  if (name === "database") return <Database className={cls} />;
  if (name === "mail") return <Mail className={cls} />;
  if (name === "globe") return <Globe className={cls} />;
  if (name === "cpu") return <Cpu className={cls} />;
  return <Zap className={cls} />;
};

// ─── Chart Components ─────────────────────────────────────────────────────────

function Sparkline({ data, color, height = 36 }: { data: number[]; color: string; height?: number }) {
  const w = 100, h = height;
  const min = Math.min(...data), max = Math.max(...data);
  const pts = data.map((v, i) => ({
    x: (i / (data.length - 1)) * w,
    y: h - ((v - min) / (max - min || 1)) * h * 0.85 - h * 0.075,
  }));
  const path = pts.map((p, i) => `${i === 0 ? "M" : "L"}${p.x},${p.y}`).join(" ");
  const fill = `${path} L${w},${h} L0,${h} Z`;
  return (
    <svg viewBox={`0 0 ${w} ${h}`} style={{ width: "100%", height }} preserveAspectRatio="none">
      <defs>
        <linearGradient id={`sg-${color.replace("#", "")}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity={0.3} />
          <stop offset="100%" stopColor={color} stopOpacity={0} />
        </linearGradient>
      </defs>
      <path d={fill} fill={`url(#sg-${color.replace("#", "")})`} />
      <path d={path} fill="none" stroke={color} strokeWidth={1.5} strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}

function DonutChart({ data }: { data: { name: string; value: number; fill: string }[] }) {
  const cx = 70, cy = 70, ro = 58, ri = 38;
  const total = data.reduce((s, d) => s + d.value, 0);
  let angle = -90;
  const slices = data.map((d) => {
    const sweep = (d.value / total) * 360;
    const s = angle; angle += sweep;
    return { ...d, start: s, sweep };
  });
  function arcPath(start: number, sweep: number, r: number, gap = 2) {
    const s = start + gap / 2, e = start + sweep - gap / 2;
    const rad = (deg: number) => (deg * Math.PI) / 180;
    const x1 = cx + r * Math.cos(rad(s)), y1 = cy + r * Math.sin(rad(s));
    const x2 = cx + r * Math.cos(rad(e)), y2 = cy + r * Math.sin(rad(e));
    const xi1 = cx + ri * Math.cos(rad(e)), yi1 = cy + ri * Math.sin(rad(e));
    const xi2 = cx + ri * Math.cos(rad(s)), yi2 = cy + ri * Math.sin(rad(s));
    const lg = sweep > 180 ? 1 : 0;
    return `M${x1},${y1} A${r},${r} 0 ${lg} 1 ${x2},${y2} L${xi1},${yi1} A${ri},${ri} 0 ${lg} 0 ${xi2},${yi2} Z`;
  }
  return (
    <svg width={140} height={140} viewBox="0 0 140 140">
      {slices.map((s) => (
        <path key={s.name} d={arcPath(s.start, s.sweep, ro)} fill={s.fill} opacity={0.9} />
      ))}
      <text x={cx} y={cy - 6} textAnchor="middle" fill={C.fg} fontSize={18} fontWeight={700} fontFamily="monospace">100</text>
      <text x={cx} y={cy + 11} textAnchor="middle" fill={C.muted} fontSize={9} fontFamily="monospace">TOTAL %</text>
    </svg>
  );
}

function LineChartSVG({ data }: { data: { t: string; v: number }[] }) {
  const W = 340, H = 110, px = 32, py = 12;
  const cw = W - px * 2, ch = H - py * 2;
  const max = 100;
  const pts = data.map((d, i) => ({
    x: px + (i / (data.length - 1)) * cw,
    y: py + ch - (d.v / max) * ch,
    ...d,
  }));
  const path = pts.map((p, i) => `${i === 0 ? "M" : "L"}${p.x},${p.y}`).join(" ");
  const fill = `${path} L${pts[pts.length - 1].x},${py + ch} L${pts[0].x},${py + ch} Z`;
  const gridYs = [0, 25, 50, 75, 100].map((v) => py + ch - (v / max) * ch);
  return (
    <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{ height: H }}>
      <defs>
        <linearGradient id="lineGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={C.blue} stopOpacity={0.25} />
          <stop offset="100%" stopColor={C.blue} stopOpacity={0} />
        </linearGradient>
      </defs>
      {gridYs.map((y, i) => (
        <line key={i} x1={px} y1={y} x2={W - px} y2={y} stroke={C.border} strokeDasharray="3 3" />
      ))}
      {[0, 50, 100].map((v) => (
        <text key={v} x={px - 4} y={py + ch - (v / max) * ch + 4} textAnchor="end" fill={C.muted} fontSize={8} fontFamily="monospace">{v}</text>
      ))}
      <path d={fill} fill="url(#lineGrad)" />
      <path d={path} fill="none" stroke={C.blue} strokeWidth={2} strokeLinejoin="round" />
      {pts.filter((_, i) => i % 2 === 0).map((p) => (
        <text key={p.t} x={p.x} y={H - 1} textAnchor="middle" fill={C.muted} fontSize={7.5} fontFamily="monospace">{p.t}</text>
      ))}
      <circle cx={pts[pts.length - 1].x} cy={pts[pts.length - 1].y} r={3} fill={C.blue} />
    </svg>
  );
}

function BarChartSVG({ data }: { data: { name: string; count: number }[] }) {
  const W = 300, H = 120, px = 80, py = 10;
  const cw = W - px - 16, ch = H - py * 2;
  const max = Math.max(...data.map((d) => d.count));
  return (
    <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{ height: H }}>
      {data.map((d, i) => {
        const y = py + i * (ch / data.length) + 2;
        const bh = ch / data.length - 4;
        const bw = (d.count / max) * cw;
        return (
          <g key={d.name}>
            <text x={px - 6} y={y + bh / 2 + 4} textAnchor="end" fill={C.fg} fontSize={9} fontFamily="monospace">{d.name}</text>
            <rect x={px} y={y} width={bw} height={bh} rx={3} fill={C.block} opacity={0.75} />
            <text x={px + bw + 4} y={y + bh / 2 + 4} fill={C.muted} fontSize={9} fontFamily="monospace">{d.count}</text>
          </g>
        );
      })}
    </svg>
  );
}

function HeatmapSVG({ data }: { data: { policy: string; mon: number; tue: number; wed: number; thu: number; fri: number }[] }) {
  const days = ["Mon", "Tue", "Wed", "Thu", "Fri"];
  const cellW = 36, cellH = 24, labelW = 72, padT = 18;
  const W = labelW + days.length * (cellW + 3) + 8;
  const H = padT + data.length * (cellH + 3) + 4;
  const maxV = Math.max(...data.flatMap((r) => [r.mon, r.tue, r.wed, r.thu, r.fri]));
  return (
    <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{ height: H }}>
      {days.map((d, i) => (
        <text key={d} x={labelW + i * (cellW + 3) + cellW / 2} y={padT - 4} textAnchor="middle" fill={C.muted} fontSize={8} fontFamily="monospace">{d}</text>
      ))}
      {data.map((row, ri) => {
        const vals = [row.mon, row.tue, row.wed, row.thu, row.fri];
        const y = padT + ri * (cellH + 3);
        return (
          <g key={row.policy}>
            <text x={labelW - 4} y={y + cellH / 2 + 4} textAnchor="end" fill={C.fg} fontSize={8.5} fontFamily="monospace">{row.policy}</text>
            {vals.map((v, ci) => {
              const intensity = v / maxV;
              return (
                <g key={ci}>
                  <rect x={labelW + ci * (cellW + 3)} y={y} width={cellW} height={cellH} rx={3}
                    fill={C.block} opacity={0.1 + intensity * 0.7} />
                  <text x={labelW + ci * (cellW + 3) + cellW / 2} y={y + cellH / 2 + 4}
                    textAnchor="middle" fill={intensity > 0.5 ? "#fff" : C.muted} fontSize={9} fontFamily="monospace">{v}</text>
                </g>
              );
            })}
          </g>
        );
      })}
    </svg>
  );
}

// ─── Page Components ──────────────────────────────────────────────────────────

function KPICard({ label, value, trend, positive, sparkData, color, icon }: {
  label: string; value: string | number; trend: string; positive: boolean;
  sparkData: number[]; color: string; icon: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-4 flex flex-col gap-2 hover:border-blue-500/30 transition-all group">
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-widest">{label}</span>
        <div className="p-1.5 rounded-lg" style={{ background: color + "20" }}>{icon}</div>
      </div>
      <div className="text-2xl font-bold tracking-tight" style={{ fontFamily: "monospace" }}>{value}</div>
      <div className="flex items-center justify-between gap-2">
        <span className={`text-[10px] font-medium ${positive ? "text-emerald-400" : "text-red-400"}`}>{trend}</span>
        <div className="w-20 opacity-70 group-hover:opacity-100 transition-opacity">
          <Sparkline data={sparkData} color={color} height={28} />
        </div>
      </div>
    </div>
  );
}

function RequestCard({ req, featured }: { req: AIRequest; featured?: boolean }) {
  const [open, setOpen] = useState(!!featured);
  return (
    <div className={`rounded-xl border bg-card transition-all ${
      req.decision === "BLOCK" ? "border-red-500/20" :
      req.decision === "CONFIRM" ? "border-yellow-400/20" : "border-border"
    } ${featured ? "ring-1 ring-blue-500/30" : ""}`}>
      <button className="w-full text-left p-4 flex items-start gap-3" onClick={() => setOpen(!open)}>
        <div className="shrink-0 mt-0.5 w-8 h-8 rounded-lg bg-secondary flex items-center justify-center">
          <ToolIcon name={req.toolIcon} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold border font-mono ${decisionBg(req.decision)}`}>
              <DecisionIcon d={req.decision} size={10} /> {req.decision}
            </span>
            <span className={`inline-flex px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold ${riskCls(req.riskLevel)}`}>
              {req.riskLevel} {req.riskScore}%
            </span>
            <span className="text-[10px] text-muted-foreground font-mono ml-auto">{req.timestamp}</span>
          </div>
          <div className="text-sm font-semibold text-foreground mb-0.5">{req.action}</div>
          <div className="text-xs text-muted-foreground">
            <span className="text-blue-400 font-medium">{req.agentName}</span>
            <span className="mx-1.5">·</span>
            <span>{req.tool}</span>
          </div>
        </div>
        <ChevronDown size={14} className={`shrink-0 mt-1 text-muted-foreground transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      {open && (
        <div className="px-4 pb-4 border-t border-border/50 pt-3 space-y-2.5">
          <div className="grid gap-1.5 text-xs">
            {[
              ["Reason", req.reason, "text-foreground"],
              req.policyViolated ? ["Policy violated", req.policyViolated, "text-red-400 font-mono font-semibold"] : null,
              ["Suggested fix", req.suggestedFix, "text-emerald-400"],
              ["Confidence", `${req.confidence}%`, "text-blue-400 font-mono"],
            ].filter(Boolean).map((row) => (
              <div key={row![0] as string} className="flex gap-2">
                <span className="text-muted-foreground shrink-0 w-28">{row![0]}:</span>
                <span className={row![2] as string}>{row![1]}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function ApprovalCard({ item, onApprove, onReject }: {
  item: ApprovalItem;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
}) {
  return (
    <div className={`rounded-xl border bg-card p-4 space-y-3 ${
      item.riskLevel === "CRITICAL" ? "border-red-500/25" :
      item.riskLevel === "HIGH" ? "border-yellow-400/25" : "border-border"
    }`}>
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="flex items-center gap-2 mb-0.5">
            <Bot size={12} className="text-blue-400" />
            <span className="text-sm font-semibold text-foreground">{item.action}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">{item.agentName} · {item.tool}</span>
          </div>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-semibold ${riskCls(item.riskLevel)}`}>
            {item.riskLevel}
          </span>
          <span className="text-[10px] text-muted-foreground font-mono">{item.requestedAt}</span>
        </div>
      </div>
      <div className="rounded-lg bg-secondary/50 px-3 py-2 text-xs text-muted-foreground font-mono leading-relaxed break-all">
        {item.details}
      </div>
      <div className="rounded-lg bg-yellow-400/5 border border-yellow-400/15 px-3 py-1.5 text-xs text-yellow-400">
        {item.reason}
      </div>
      <div className="flex gap-2">
        <button onClick={() => onApprove(item.id)}
          className="flex-1 flex items-center justify-center gap-1.5 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 text-xs font-semibold py-2 hover:bg-emerald-500/25 transition-colors">
          <Check size={12} /> Approve
        </button>
        <button onClick={() => onReject(item.id)}
          className="flex-1 flex items-center justify-center gap-1.5 rounded-lg bg-red-500/15 border border-red-500/30 text-red-400 text-xs font-semibold py-2 hover:bg-red-500/25 transition-colors">
          <X size={12} /> Reject
        </button>
      </div>
    </div>
  );
}

function PolicyReasoningPanel({ req }: { req: AIRequest }) {
  const steps = ["Rule-based validation", "LLM policy reasoning", "Risk scoring"];
  return (
    <div className="rounded-xl border border-blue-500/20 bg-gradient-to-br from-blue-950/30 to-card p-4 space-y-4">
      <div className="flex items-center gap-2">
        <div className="w-6 h-6 rounded bg-blue-500/20 flex items-center justify-center">
          <Layers size={12} className="text-blue-400" />
        </div>
        <div>
          <div className="text-xs font-semibold text-foreground">AI Security Policy Engine</div>
          <div className="text-[10px] text-muted-foreground">Granite 3.3 / watsonx.ai</div>
        </div>
      </div>
      <div className="grid grid-cols-3 gap-2 text-center">
        {[
          { label: "Risk Score", val: `${req.riskScore}%`, color: req.riskScore > 70 ? C.block : req.riskScore > 40 ? C.confirm : C.allow },
          { label: "Decision", val: req.decision, color: decisionColor(req.decision) },
          { label: "Confidence", val: `${req.confidence}%`, color: C.blue },
        ].map((m) => (
          <div key={m.label} className="rounded-lg bg-secondary/50 py-2 px-1">
            <div className="text-xs font-bold font-mono" style={{ color: m.color }}>{m.val}</div>
            <div className="text-[9px] text-muted-foreground mt-0.5">{m.label}</div>
          </div>
        ))}
      </div>
      <div className="rounded-lg bg-secondary/40 px-3 py-2.5 text-xs text-foreground leading-relaxed">
        <span className="text-muted-foreground">Reason: </span>
        {req.policyViolated
          ? `The ${req.agentName} role does not have permission to perform "${req.action}". This action violates enterprise policy ${req.policyViolated} and is classified as ${req.riskLevel.toLowerCase()}-risk destructive.`
          : req.reason}
      </div>
      <div className="flex gap-2">
        {steps.map((s, i) => (
          <div key={s} className="flex-1 flex flex-col items-center gap-1">
            <div className={`w-4 h-4 rounded-full flex items-center justify-center text-[8px] font-bold ${i === 0 || i === 1 || i === 2 ? "bg-blue-500/20 text-blue-400" : "bg-secondary text-muted-foreground"}`}>{i + 1}</div>
            <div className="text-[8px] text-muted-foreground text-center leading-tight">{s}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

const PIPELINE_STEPS = [
  { label: "AI Agent", icon: Bot, detail: "Generates tool call" },
  { label: "SENTRY Middleware", icon: Shield, detail: "Intercepts request", accent: true },
  { label: "Scope Check", icon: Lock, detail: "RBAC validation" },
  { label: "Param Validation", icon: CheckCircle2, detail: "Input sanitization" },
  { label: "Rate & Cost Guard", icon: Zap, detail: "Threshold check" },
  { label: "Irreversibility", icon: AlertTriangle, detail: "Destructive detection" },
  { label: "AI Policy Engine", icon: Layers, detail: "LLM reasoning" },
  { label: "Risk Scoring", icon: TrendingUp, detail: "0–100 score" },
  { label: "Decision", icon: GitBranch, detail: "ALLOW / BLOCK / CONFIRM", accent: true },
  { label: "Tool Execution", icon: Terminal, detail: "Approved action runs" },
];

function PipelineViz({ animStep }: { animStep: number }) {
  return (
    <div className="flex flex-col items-center gap-0 py-2">
      {PIPELINE_STEPS.map((step, i) => {
        const Icon = step.icon;
        const active = i === animStep;
        const done = i < animStep;
        return (
          <div key={step.label} className="flex flex-col items-center">
            <div className={`flex items-center gap-3 w-full max-w-xs rounded-lg px-3 py-2 transition-all duration-300 ${
              active ? "bg-blue-500/20 border border-blue-500/40 shadow-[0_0_12px_rgba(59,130,246,0.2)]"
              : done ? "bg-emerald-500/10 border border-emerald-500/20"
              : "bg-secondary/30 border border-border/50"
            } ${step.accent && active ? "ring-1 ring-blue-400/50" : ""}`}>
              <div className={`w-6 h-6 rounded flex items-center justify-center shrink-0 ${
                active ? "bg-blue-500/30" : done ? "bg-emerald-500/20" : "bg-secondary"
              }`}>
                <Icon size={12} className={active ? "text-blue-400" : done ? "text-emerald-400" : "text-muted-foreground"} />
              </div>
              <div className="min-w-0">
                <div className={`text-[11px] font-semibold leading-none ${active ? "text-blue-300" : done ? "text-emerald-400" : "text-muted-foreground"}`}>{step.label}</div>
                <div className="text-[9px] text-muted-foreground mt-0.5">{step.detail}</div>
              </div>
              {done && <CheckCircle2 size={10} className="text-emerald-400 ml-auto shrink-0" />}
              {active && <div className="ml-auto w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse shrink-0" />}
            </div>
            {i < PIPELINE_STEPS.length - 1 && (
              <div className={`w-px h-3 transition-colors ${done ? "bg-emerald-500/40" : "bg-border"}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}

// ─── Demo Modal ───────────────────────────────────────────────────────────────
interface DemoScenario {
  title: string;
  agent: string;
  action: string;
  tool: string;
  decision: Decision;
  risk: RiskLevel;
  score: number;
  policy: string | null;
  reason: string;
  needsApproval?: boolean;
}

const DEMO_SCENARIOS: DemoScenario[] = [
  { title: "Scenario 1: Inventory Read", agent: "Inventory Bot", action: "Read Inventory Table", tool: "BigQuery", decision: "ALLOW", risk: "LOW", score: 8, policy: null, reason: "Read-only access to approved dataset. Within scope." },
  { title: "Scenario 2: Payroll Modification", agent: "Finance Bot", action: "Modify Payroll Records", tool: "Workday API", decision: "BLOCK", risk: "CRITICAL", score: 96, policy: "RBAC-04", reason: "Agent attempted to modify payroll outside its approved scope." },
  { title: "Scenario 3: Delete Customer Record", agent: "Sales Assistant", action: "Delete Customer Record", tool: "PostgreSQL CRM", decision: "CONFIRM", risk: "HIGH", score: 82, policy: "RBAC-04", reason: "Destructive record deletion requires human approval.", needsApproval: true },
];

function DemoModal({ onClose, onComplete }: { onClose: () => void; onComplete: (rows: AuditRow[]) => void }) {
  const [step, setStep] = useState(-1);
  const [phase, setPhase] = useState<"running" | "approval" | "done">("running");
  const [approvalResult, setApprovalResult] = useState<"approved" | "rejected" | null>(null);
  const current = step >= 0 && step < DEMO_SCENARIOS.length ? DEMO_SCENARIOS[step] : null;
  const completed = step >= 0 ? DEMO_SCENARIOS.slice(0, Math.min(step + 1, DEMO_SCENARIOS.length)) : [];

  useEffect(() => {
    if (phase !== "running") return;
    if (step === -1) {
      const t = setTimeout(() => setStep(0), 600);
      return () => clearTimeout(t);
    }
    if (step < DEMO_SCENARIOS.length) {
      const s = DEMO_SCENARIOS[step];
      if (s.needsApproval) { setPhase("approval"); return; }
      const t = setTimeout(() => {
        if (step + 1 < DEMO_SCENARIOS.length) setStep(step + 1);
        else setPhase("done");
      }, 1800);
      return () => clearTimeout(t);
    }
  }, [step, phase]);

  const handleApprovalAction = (result: "approved" | "rejected") => {
    setApprovalResult(result);
    setPhase("running");
    setTimeout(() => {
      const newRows: AuditRow[] = DEMO_SCENARIOS.map((s, i) => ({
        id: `demo-${i}`, time: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false }),
        agent: s.agent, action: s.action, tool: s.tool, decision: s.decision,
        risk: s.risk, policy: s.policy || "—", reason: s.reason,
        status: i === 2 ? (result === "approved" ? "overridden" : "completed") : "completed",
      }));
      onComplete(newRows);
      setPhase("done");
    }, 1200);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: "rgba(0,0,0,0.7)", backdropFilter: "blur(4px)" }}>
      <div className="rounded-2xl border border-blue-500/30 bg-card w-full max-w-lg shadow-2xl">
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <div className="flex items-center gap-2">
            <Play size={14} className="text-blue-400" />
            <span className="text-sm font-semibold">SENTRY Demo Mode</span>
            {phase === "running" && step >= 0 && <div className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />}
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground"><X size={16} /></button>
        </div>
        <div className="p-5 space-y-4">
          {DEMO_SCENARIOS.map((s, i) => {
            const isDone = i < step || (i === step && phase === "done") || (i === 2 && approvalResult !== null);
            const isActive = i === step && (phase === "running" || (phase === "approval" && s.needsApproval));
            const isPending = i > step;
            return (
              <div key={s.title} className={`rounded-xl border p-3.5 transition-all duration-500 ${
                isActive ? "border-blue-500/40 bg-blue-500/5 shadow-[0_0_16px_rgba(59,130,246,0.15)]"
                : isDone ? "border-border bg-secondary/20 opacity-80"
                : "border-border/40 bg-secondary/10 opacity-40"
              }`}>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-[10px] text-muted-foreground font-mono">{s.title}</span>
                  {isActive && phase === "running" && <RefreshCw size={10} className="text-blue-400 animate-spin" />}
                  {isDone && <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold border font-mono ${decisionBg(s.decision)}`}><DecisionIcon d={s.decision} size={9} />{s.decision}</span>}
                  {isDone && i === 2 && approvalResult && (
                    <span className={`text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded ${approvalResult === "approved" ? "text-emerald-400 bg-emerald-500/10" : "text-red-400 bg-red-500/10"}`}>
                      Human: {approvalResult.toUpperCase()}
                    </span>
                  )}
                </div>
                <div className="text-sm font-semibold text-foreground">{s.action}</div>
                <div className="text-xs text-muted-foreground">{s.agent} · {s.tool}</div>
                {(isActive || isDone) && s.policy && (
                  <div className="mt-1.5 text-[10px] text-red-400 font-mono">Policy: {s.policy}</div>
                )}
                {isActive && phase === "approval" && s.needsApproval && (
                  <div className="mt-3 space-y-2">
                    <div className="rounded-lg bg-yellow-400/5 border border-yellow-400/15 px-3 py-2 text-xs text-yellow-400">{s.reason}</div>
                    <div className="flex gap-2">
                      <button onClick={() => handleApprovalAction("approved")}
                        className="flex-1 flex items-center justify-center gap-1.5 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 text-xs font-semibold py-1.5 hover:bg-emerald-500/25 transition-colors">
                        <Check size={12} /> Approve
                      </button>
                      <button onClick={() => handleApprovalAction("rejected")}
                        className="flex-1 flex items-center justify-center gap-1.5 rounded-lg bg-red-500/15 border border-red-500/30 text-red-400 text-xs font-semibold py-1.5 hover:bg-red-500/25 transition-colors">
                        <X size={12} /> Reject
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
          {phase === "done" && (
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-3 text-center">
              <CheckCircle2 size={20} className="text-emerald-400 mx-auto mb-1.5" />
              <div className="text-sm font-semibold text-foreground">Demo Complete</div>
              <div className="text-xs text-muted-foreground mt-0.5">Audit log and statistics have been updated.</div>
              <button onClick={onClose}
                className="mt-3 px-4 py-1.5 rounded-lg bg-blue-500/20 border border-blue-500/30 text-blue-400 text-xs font-semibold hover:bg-blue-500/30 transition-colors">
                Close
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Pages ────────────────────────────────────────────────────────────────────

function DashboardPage({ requests, queue, onApprove, onReject, kpiAllowed, kpiBlocked, kpiPending }: {
  requests: AIRequest[]; queue: ApprovalItem[];
  onApprove: (id: string) => void; onReject: (id: string) => void;
  kpiAllowed: number; kpiBlocked: number; kpiPending: number;
}) {
  const [pipeStep, setPipeStep] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setPipeStep((s) => (s + 1) % PIPELINE_STEPS.length), 900);
    return () => clearInterval(t);
  }, []);
  const featured = requests[0];
  return (
    <div className="space-y-5">
      {/* KPIs */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-3">
        <KPICard label="Allowed Requests" value={kpiAllowed.toLocaleString()} trend="+12% vs last hour" positive sparkData={SPARKLINE_ALLOWED} color={C.allow} icon={<CheckCircle2 size={14} className="text-emerald-400" />} />
        <KPICard label="Blocked Requests" value={kpiBlocked.toLocaleString()} trend="+3 critical events" positive={false} sparkData={SPARKLINE_BLOCKED} color={C.block} icon={<XCircle size={14} className="text-red-400" />} />
        <KPICard label="Pending Approval" value={kpiPending} trend={`${kpiPending} awaiting review`} positive={kpiPending === 0} sparkData={SPARKLINE_PENDING} color={C.confirm} icon={<Clock size={14} className="text-yellow-400" />} />
        <KPICard label="Avg Risk Score" value="42.7" trend="↑ 8.3pts from baseline" positive={false} sparkData={SPARKLINE_RISK} color={C.blue} icon={<TrendingUp size={14} className="text-blue-400" />} />
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
        {/* Live feed */}
        <div className="xl:col-span-2 space-y-4">
          <div className="rounded-xl border border-border bg-card overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-border">
              <div className="flex items-center gap-2">
                <Activity size={14} className="text-blue-400" />
                <span className="text-sm font-semibold">Live AI Requests</span>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              </div>
              <span className="text-[10px] text-muted-foreground font-mono">AUTO-REFRESH 2s</span>
            </div>
            <div className="p-3 space-y-2.5 max-h-72 overflow-auto" style={{ scrollbarWidth: "none" }}>
              {requests.slice(0, 4).map((r) => <RequestCard key={r.id} req={r} />)}
            </div>
          </div>
          {/* Explainable AI panel */}
          <div className="rounded-xl border border-border bg-card overflow-hidden">
            <div className="px-4 py-3 border-b border-border flex items-center gap-2">
              <Layers size={14} className="text-blue-400" />
              <span className="text-sm font-semibold">AI Policy Reasoning</span>
              <span className="text-[10px] text-muted-foreground ml-1">— most recent BLOCK decision</span>
            </div>
            <div className="p-4">
              <PolicyReasoningPanel req={featured} />
            </div>
          </div>
        </div>

        {/* Right column */}
        <div className="space-y-4">
          {/* Approval queue */}
          <div className="rounded-xl border border-border bg-card overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-border">
              <div className="flex items-center gap-2">
                <ClipboardList size={14} className="text-yellow-400" />
                <span className="text-sm font-semibold">Approval Queue</span>
                {queue.length > 0 && <span className="px-1.5 py-0.5 rounded bg-yellow-400/15 text-yellow-400 text-[10px] font-bold">{queue.length}</span>}
              </div>
            </div>
            <div className="p-3 space-y-2.5 max-h-64 overflow-auto" style={{ scrollbarWidth: "none" }}>
              {queue.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
                  <CheckCircle2 size={20} className="text-emerald-500/40 mb-2" />
                  <span className="text-xs">Queue empty — all clear</span>
                </div>
              ) : queue.map((item) => <ApprovalCard key={item.id} item={item} onApprove={onApprove} onReject={onReject} />)}
            </div>
          </div>
          {/* Risk pipeline */}
          <div className="rounded-xl border border-border bg-card overflow-hidden">
            <div className="px-4 py-3 border-b border-border flex items-center gap-2">
              <GitBranch size={14} className="text-blue-400" />
              <span className="text-sm font-semibold">Risk Engine Pipeline</span>
            </div>
            <div className="p-3 max-h-80 overflow-auto" style={{ scrollbarWidth: "none" }}>
              <PipelineViz animStep={pipeStep} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function LiveRequestsPage({ requests }: { requests: AIRequest[] }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <div className="flex-1 relative">
          <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input className="w-full bg-card border border-border rounded-lg pl-9 pr-3 py-2 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-blue-500/50" placeholder="Search requests…" />
        </div>
        {(["ALLOW", "BLOCK", "CONFIRM"] as Decision[]).map((d) => (
          <span key={d} className={`px-2.5 py-1.5 rounded-lg text-[10px] font-bold border cursor-pointer hover:opacity-80 ${decisionBg(d)}`}>{d}</span>
        ))}
      </div>
      <div className="space-y-3">
        {requests.map((r) => <RequestCard key={r.id} req={r} />)}
      </div>
    </div>
  );
}

function ApprovalQueuePage({ queue, onApprove, onReject }: {
  queue: ApprovalItem[]; onApprove: (id: string) => void; onReject: (id: string) => void;
}) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 p-4 rounded-xl border border-yellow-400/20 bg-yellow-400/5">
        <AlertTriangle size={16} className="text-yellow-400 shrink-0" />
        <div>
          <div className="text-sm font-semibold text-yellow-400">{queue.length} Action{queue.length !== 1 ? "s" : ""} Awaiting Human Review</div>
          <div className="text-xs text-muted-foreground mt-0.5">These actions were flagged as potentially dangerous. Review each carefully before approving.</div>
        </div>
      </div>
      {queue.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-muted-foreground rounded-xl border border-border bg-card">
          <CheckCircle2 size={32} className="text-emerald-500/30 mb-3" />
          <div className="text-sm font-medium">All Clear</div>
          <div className="text-xs mt-1">No actions are awaiting review.</div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {queue.map((item) => <ApprovalCard key={item.id} item={item} onApprove={onApprove} onReject={onReject} />)}
        </div>
      )}
    </div>
  );
}

function AuditLogPage({ rows }: { rows: AuditRow[] }) {
  const [search, setSearch] = useState("");
  const [filterDecision, setFilterDecision] = useState<Decision | "ALL">("ALL");
  const filtered = rows.filter((r) =>
    (filterDecision === "ALL" || r.decision === filterDecision) &&
    (search === "" || [r.agent, r.action, r.tool, r.policy, r.reason].join(" ").toLowerCase().includes(search.toLowerCase()))
  );
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex-1 min-w-48 relative">
          <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input value={search} onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-card border border-border rounded-lg pl-9 pr-3 py-2 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-blue-500/50"
            placeholder="Search audit log…" />
        </div>
        {(["ALL", "ALLOW", "BLOCK", "CONFIRM"] as const).map((d) => (
          <button key={d} onClick={() => setFilterDecision(d)}
            className={`px-3 py-1.5 rounded-lg text-[10px] font-bold border transition-colors ${
              filterDecision === d
                ? d === "ALL" ? "bg-blue-500/20 border-blue-500/40 text-blue-400"
                  : decisionBg(d as Decision)
                : "border-border text-muted-foreground hover:text-foreground"
            }`}>{d}</button>
        ))}
      </div>
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-border bg-secondary/30">
                {["Time", "Agent", "Action", "Tool", "Decision", "Risk", "Policy", "Reason", "Status"].map((h) => (
                  <th key={h} className="text-left px-3 py-2.5 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((row, i) => (
                <tr key={row.id} className={`border-b border-border/40 hover:bg-secondary/20 transition-colors ${i % 2 === 0 ? "" : "bg-secondary/10"}`}>
                  <td className="px-3 py-2.5 font-mono text-muted-foreground whitespace-nowrap">{row.time}</td>
                  <td className="px-3 py-2.5 font-medium text-foreground whitespace-nowrap">{row.agent}</td>
                  <td className="px-3 py-2.5 text-foreground whitespace-nowrap">{row.action}</td>
                  <td className="px-3 py-2.5 text-muted-foreground whitespace-nowrap">{row.tool}</td>
                  <td className="px-3 py-2.5">
                    <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold border font-mono whitespace-nowrap ${decisionBg(row.decision)}`}>
                      <DecisionIcon d={row.decision} size={9} />{row.decision}
                    </span>
                  </td>
                  <td className="px-3 py-2.5">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-semibold ${riskCls(row.risk)}`}>{row.risk}</span>
                  </td>
                  <td className="px-3 py-2.5 font-mono text-muted-foreground">{row.policy}</td>
                  <td className="px-3 py-2.5 text-muted-foreground max-w-48 truncate">{row.reason}</td>
                  <td className="px-3 py-2.5">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
                      row.status === "completed" ? "text-emerald-400 bg-emerald-500/10"
                      : row.status === "overridden" ? "text-blue-400 bg-blue-500/10"
                      : "text-yellow-400 bg-yellow-400/10"
                    }`}>{row.status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filtered.length === 0 && (
          <div className="flex items-center justify-center py-12 text-muted-foreground text-xs">No results matching filter.</div>
        )}
      </div>
    </div>
  );
}

function AnalyticsPage() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
      <div className="rounded-xl border border-border bg-card p-4">
        <div className="flex items-center gap-2 mb-4">
          <BarChart2 size={13} className="text-blue-400" />
          <span className="text-sm font-semibold">Decision Distribution</span>
        </div>
        <div className="flex items-center gap-6">
          <DonutChart data={DIST_DATA} />
          <div className="space-y-2.5">
            {DIST_DATA.map((d) => (
              <div key={d.name} className="flex items-center gap-2.5">
                <span className="w-2.5 h-2.5 rounded-sm shrink-0" style={{ background: d.fill }} />
                <span className="text-xs text-foreground font-medium w-14">{d.name}</span>
                <span className="text-xs font-mono text-muted-foreground">{d.value}%</span>
                <div className="h-1.5 rounded-full flex-1 bg-secondary overflow-hidden">
                  <div className="h-full rounded-full" style={{ width: `${d.value}%`, background: d.fill, opacity: 0.7 }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
      <div className="rounded-xl border border-border bg-card p-4">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp size={13} className="text-blue-400" />
          <span className="text-sm font-semibold">Risk Score Over Time</span>
        </div>
        <LineChartSVG data={RISK_TIMELINE} />
      </div>
      <div className="rounded-xl border border-border bg-card p-4">
        <div className="flex items-center gap-2 mb-4">
          <XCircle size={13} className="text-red-400" />
          <span className="text-sm font-semibold">Top Blocked Agents</span>
        </div>
        <BarChartSVG data={BLOCKED_AGENTS} />
      </div>
      <div className="rounded-xl border border-border bg-card p-4">
        <div className="flex items-center gap-2 mb-4">
          <Layers size={13} className="text-blue-400" />
          <span className="text-sm font-semibold">Policy Violation Heatmap</span>
          <span className="text-[10px] text-muted-foreground ml-1">— this week</span>
        </div>
        <HeatmapSVG data={POLICY_HEATMAP} />
        <div className="flex items-center gap-3 mt-3">
          <span className="text-[10px] text-muted-foreground">Low</span>
          {[0.1, 0.3, 0.5, 0.7, 0.9].map((o) => (
            <div key={o} className="w-5 h-3 rounded-sm" style={{ background: C.block, opacity: o }} />
          ))}
          <span className="text-[10px] text-muted-foreground">High</span>
        </div>
      </div>
    </div>
  );
}

function PoliciesPage({ policies, onToggle }: { policies: Policy[]; onToggle: (id: string) => void }) {
  const catColor: Record<string, string> = {
    "Access Control": "text-red-400 bg-red-500/10",
    "Financial": "text-yellow-400 bg-yellow-400/10",
    "Communication": "text-blue-400 bg-blue-500/10",
    "Infrastructure": "text-orange-400 bg-orange-500/10",
    "Compliance": "text-purple-400 bg-purple-500/10",
    "API": "text-cyan-400 bg-cyan-500/10",
    "Data": "text-emerald-400 bg-emerald-500/10",
  };
  return (
    <div className="space-y-3">
      {policies.map((p) => (
        <div key={p.id} className={`rounded-xl border bg-card p-4 flex items-start gap-4 transition-opacity ${p.enabled ? "" : "opacity-50"}`} style={{ borderColor: p.enabled ? C.border : "rgba(100,116,139,0.1)" }}>
          <div className="shrink-0 mt-0.5">
            <div className="w-8 h-8 rounded-lg bg-secondary flex items-center justify-center">
              <Lock size={14} className="text-muted-foreground" />
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <span className="text-sm font-bold font-mono text-foreground">{p.id}</span>
              <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold ${riskCls(p.severity)}`}>{p.severity}</span>
              <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold ${catColor[p.category] ?? "text-muted-foreground bg-secondary"}`}>{p.category}</span>
              <span className="text-[10px] text-muted-foreground ml-auto">Triggered {p.triggered}×</span>
            </div>
            <div className="text-xs font-medium text-foreground mb-0.5">{p.name}</div>
            <div className="text-xs text-muted-foreground">{p.description}</div>
          </div>
          <button onClick={() => onToggle(p.id)} className="shrink-0 flex items-center gap-1.5 text-xs transition-colors mt-0.5">
            {p.enabled
              ? <><ToggleRight size={20} className="text-emerald-400" /><span className="text-emerald-400 text-[10px] font-semibold">ON</span></>
              : <><ToggleLeft size={20} className="text-muted-foreground" /><span className="text-muted-foreground text-[10px] font-semibold">OFF</span></>}
          </button>
        </div>
      ))}
    </div>
  );
}

function SettingsPage() {
  const [notifs, setNotifs] = useState(true);
  const [autoBlock, setAutoBlock] = useState(true);
  const [dualAuth, setDualAuth] = useState(false);
  const Toggle = ({ on, set }: { on: boolean; set: (v: boolean) => void }) => (
    <button onClick={() => set(!on)} className="relative w-10 h-5 rounded-full transition-colors" style={{ background: on ? C.blue : "#334155" }}>
      <div className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-all ${on ? "left-5.5" : "left-0.5"}`} style={{ left: on ? "calc(100% - 18px)" : "2px" }} />
    </button>
  );
  const Row = ({ label, desc, on, set }: { label: string; desc: string; on: boolean; set: (v: boolean) => void }) => (
    <div className="flex items-center justify-between gap-4 py-3 border-b border-border last:border-0">
      <div>
        <div className="text-sm font-medium text-foreground">{label}</div>
        <div className="text-xs text-muted-foreground mt-0.5">{desc}</div>
      </div>
      <Toggle on={on} set={set} />
    </div>
  );
  return (
    <div className="max-w-xl space-y-5">
      <div className="rounded-xl border border-border bg-card p-5">
        <div className="text-sm font-semibold mb-3 flex items-center gap-2"><Settings size={14} className="text-blue-400" /> General</div>
        <Row label="Real-time Notifications" desc="Alert on BLOCK and CONFIRM events" on={notifs} set={setNotifs} />
        <Row label="Auto-Block Critical Risk" desc="Immediately block actions scoring ≥90" on={autoBlock} set={setAutoBlock} />
        <Row label="Dual Authorization" desc="Require two approvals for HIGH+ risk" on={dualAuth} set={setDualAuth} />
      </div>
      <div className="rounded-xl border border-border bg-card p-5">
        <div className="text-sm font-semibold mb-3 flex items-center gap-2"><Shield size={14} className="text-blue-400" /> Policy Engine</div>
        <div className="text-xs text-muted-foreground mb-3">AI model powering policy reasoning decisions.</div>
        <div className="flex gap-2">
          {["Granite 3.3", "Llama 3.1", "GPT-4o"].map((m) => (
            <button key={m} className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${m === "Granite 3.3" ? "bg-blue-500/20 border-blue-500/40 text-blue-400" : "border-border text-muted-foreground hover:text-foreground"}`}>{m}</button>
          ))}
        </div>
      </div>
      <div className="rounded-xl border border-border bg-card p-5">
        <div className="text-sm font-semibold mb-3 flex items-center gap-2"><User size={14} className="text-blue-400" /> User Profile</div>
        <div className="flex items-center gap-3 p-3 bg-secondary/40 rounded-lg">
          <div className="w-10 h-10 rounded-full bg-blue-600/20 border border-blue-500/30 flex items-center justify-center">
            <User size={16} className="text-blue-400" />
          </div>
          <div>
            <div className="text-sm font-medium text-foreground">Alex Chen</div>
            <div className="text-xs text-muted-foreground">SOC Analyst · Enterprise Plan</div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── NAV ──────────────────────────────────────────────────────────────────────
const NAV = [
  { id: "dashboard" as Page, label: "Dashboard", icon: LayoutDashboard },
  { id: "live" as Page, label: "Live Requests", icon: Activity },
  { id: "queue" as Page, label: "Approval Queue", icon: ClipboardList },
  { id: "policies" as Page, label: "Policies", icon: ShieldAlert },
  { id: "audit" as Page, label: "Audit Log", icon: FileText },
  { id: "analytics" as Page, label: "Analytics", icon: BarChart2 },
  { id: "settings" as Page, label: "Settings", icon: Settings },
];

const PAGE_TITLES: Record<Page, string> = {
  dashboard: "Security Operations Center",
  live: "Live AI Requests",
  queue: "Human Approval Queue",
  policies: "Policy Management",
  audit: "Audit Log",
  analytics: "Analytics",
  settings: "Settings",
};

// ─── App ──────────────────────────────────────────────────────────────────────
export default function App() {
  const [page, setPage] = useState<Page>("dashboard");
  const [collapsed, setCollapsed] = useState(false);
  const [time, setTime] = useState(new Date());
  const [requests, setRequests] = useState<AIRequest[]>(SEED_REQUESTS);
  const [queue, setQueue] = useState<ApprovalItem[]>(SEED_QUEUE);
  const [auditLog, setAuditLog] = useState<AuditRow[]>(SEED_AUDIT);
  const [policies, setPolicies] = useState<Policy[]>(SEED_POLICIES);
  const [demo, setDemo] = useState(false);
  const [allowed, setAllowed] = useState(1284);
  const [blocked, setBlocked] = useState(347);

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const handleApprove = (id: string) => {
    setQueue((q) => q.filter((i) => i.id !== id));
    setAllowed((a) => a + 1);
  };
  const handleReject = (id: string) => {
    setQueue((q) => q.filter((i) => i.id !== id));
    setBlocked((b) => b + 1);
  };
  const handleTogglePolicy = (id: string) => {
    setPolicies((ps) => ps.map((p) => p.id === id ? { ...p, enabled: !p.enabled } : p));
  };
  const handleDemoComplete = (rows: AuditRow[]) => {
    setAuditLog((log) => [...rows, ...log]);
    setAllowed((a) => a + 1);
    setBlocked((b) => b + 1);
    setDemo(false);
  };

  const fmt = (d: Date) => d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });

  return (
    <div className="flex h-screen w-full bg-background text-foreground overflow-hidden" style={{ fontFamily: "'Inter', sans-serif" }}>
      {demo && <DemoModal onClose={() => setDemo(false)} onComplete={handleDemoComplete} />}

      {/* ── Sidebar ── */}
      <aside className={`shrink-0 flex flex-col bg-sidebar border-r border-sidebar-border transition-all duration-200 ${collapsed ? "w-14" : "w-54"}`} style={{ width: collapsed ? 56 : 216 }}>
        <div className="flex items-center gap-2.5 px-3.5 h-14 border-b border-sidebar-border">
          <div className="shrink-0 w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center shadow-[0_0_12px_rgba(59,130,246,0.4)]">
            <Shield size={14} className="text-white" />
          </div>
          {!collapsed && (
            <div>
              <div className="text-sm font-bold text-foreground tracking-tight leading-none">SENTRY</div>
              <div className="text-[9px] text-muted-foreground tracking-widest uppercase leading-none mt-0.5">AI Execution Firewall</div>
            </div>
          )}
        </div>
        <nav className="flex-1 py-3 px-2 space-y-0.5">
          {NAV.map(({ id, label, icon: Icon }) => {
            const active = page === id;
            return (
              <button key={id} onClick={() => setPage(id)}
                className={`w-full flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-xs transition-colors relative ${
                  active ? "bg-sidebar-accent text-sidebar-accent-foreground font-semibold" : "text-sidebar-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground"
                }`}>
                <Icon size={15} className={active ? "text-blue-400 shrink-0" : "shrink-0"} />
                {!collapsed && <span>{label}</span>}
                {id === "queue" && queue.length > 0 && (
                  <span className={`${collapsed ? "absolute top-0.5 right-0.5 min-w-[14px] h-[14px] text-[8px]" : "ml-auto min-w-[18px] h-[18px] text-[10px]"} rounded-full bg-yellow-500 font-bold text-black flex items-center justify-center`}>
                    {queue.length}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
        <div className="px-2 pb-3">
          <button onClick={() => setDemo(true)}
            className={`w-full flex items-center justify-center gap-1.5 rounded-lg bg-blue-600/20 border border-blue-500/30 text-blue-400 text-xs font-semibold py-2 hover:bg-blue-600/30 transition-colors ${collapsed ? "px-0" : ""}`}>
            <Play size={12} />
            {!collapsed && "Run Demo"}
          </button>
        </div>
        <button onClick={() => setCollapsed(!collapsed)}
          className="mx-2 mb-3 flex items-center justify-center h-7 rounded-lg border border-sidebar-border text-muted-foreground hover:text-foreground hover:border-blue-500/30 transition-colors">
          {collapsed ? <ChevronRight size={12} /> : <ChevronLeft size={12} />}
        </button>
      </aside>

      {/* ── Main ── */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Topbar */}
        <header className="shrink-0 h-14 border-b border-border flex items-center justify-between px-5 bg-card/60 backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(34,197,94,0.6)] animate-pulse" />
              <span className="text-xs text-emerald-400 font-mono font-semibold">CONNECTED</span>
            </div>
            <span className="w-px h-4 bg-border" />
            <span className="text-xs text-muted-foreground">v2.4.1 <span className="text-blue-400">Enterprise</span></span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-xs font-mono text-muted-foreground tabular-nums">{fmt(time)} UTC</span>
            <button className="relative p-1.5 rounded-lg hover:bg-secondary transition-colors text-muted-foreground hover:text-foreground">
              <Bell size={15} />
              {queue.length > 0 && <span className="absolute top-0.5 right-0.5 w-3.5 h-3.5 rounded-full bg-yellow-500 text-[8px] font-bold text-black flex items-center justify-center">{queue.length}</span>}
            </button>
            <div className="flex items-center gap-2 pl-3 border-l border-border">
              <div className="w-7 h-7 rounded-full bg-blue-600/20 border border-blue-500/30 flex items-center justify-center">
                <User size={13} className="text-blue-400" />
              </div>
              <div className="hidden sm:block">
                <div className="text-xs font-semibold text-foreground leading-none">A. Chen</div>
                <div className="text-[10px] text-muted-foreground leading-none mt-0.5">SOC Analyst</div>
              </div>
            </div>
          </div>
        </header>

        {/* Page header */}
        <div className="shrink-0 px-5 py-3 border-b border-border flex items-center justify-between bg-background/50">
          <div>
            <h1 className="text-sm font-semibold text-foreground">{PAGE_TITLES[page]}</h1>
            <p className="text-[10px] text-muted-foreground mt-0.5">
              {new Date().toLocaleDateString("en-US", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => setDemo(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600/20 border border-blue-500/30 text-blue-400 text-xs font-semibold hover:bg-blue-600/30 transition-colors shadow-[0_0_12px_rgba(59,130,246,0.15)]">
              <Play size={11} /> Run Demo
            </button>
            <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border text-xs text-muted-foreground hover:text-foreground hover:border-blue-500/30 transition-colors">
              <Filter size={11} /> Filter
            </button>
          </div>
        </div>

        {/* Content */}
        <main className="flex-1 overflow-auto p-5" style={{ scrollbarWidth: "none" }}>
          {page === "dashboard" && (
            <DashboardPage requests={requests} queue={queue} onApprove={handleApprove} onReject={handleReject}
              kpiAllowed={allowed} kpiBlocked={blocked} kpiPending={queue.length} />
          )}
          {page === "live" && <LiveRequestsPage requests={requests} />}
          {page === "queue" && <ApprovalQueuePage queue={queue} onApprove={handleApprove} onReject={handleReject} />}
          {page === "audit" && <AuditLogPage rows={auditLog} />}
          {page === "analytics" && <AnalyticsPage />}
          {page === "policies" && <PoliciesPage policies={policies} onToggle={handleTogglePolicy} />}
          {page === "settings" && <SettingsPage />}
        </main>
      </div>
    </div>
  );
}
