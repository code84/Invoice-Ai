'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import {
  CheckCircle, AlertCircle, XCircle, FileText,
  Upload, RefreshCw, ArrowRight, Cpu, ShieldCheck,
  GitMerge, ClipboardList, Zap,
} from 'lucide-react';
import { getDashboard } from '@/lib/api';
import type { DashboardStats } from '@/lib/types';
import StatusBadge from '@/components/StatusBadge';

/* ─── helpers ─────────────────────────────────────────────────────────────── */
function fmt(val: number | null, currency = 'INR') {
  if (val == null) return '—';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency', currency, maximumFractionDigits: 0,
  }).format(val);
}
function fmtDate(d: string) {
  return new Date(d).toLocaleDateString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
  });
}

/* ─── stat card ───────────────────────────────────────────────────────────── */
function StatCard({
  label, value, icon: Icon, iconBg, change,
}: {
  label: string; value: number; icon: React.ElementType;
  iconBg: string; change?: string;
}) {
  return (
    <div className="bg-white rounded-2xl border border-slate-100 p-6 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${iconBg}`}>
          <Icon size={20} className="text-white" />
        </div>
        {change && (
          <span className="text-xs font-medium text-emerald-600 bg-emerald-50 border border-emerald-100 px-2 py-0.5 rounded-full">
            {change}
          </span>
        )}
      </div>
      <p className="text-3xl font-bold text-slate-900 mb-1">{value}</p>
      <p className="text-sm text-slate-500 font-medium">{label}</p>
    </div>
  );
}

/* ─── feature photo card ──────────────────────────────────────────────────── */
function FeatureCard({
  img, title, desc, icon: Icon,
}: {
  img: string; title: string; desc: string; icon: React.ElementType;
}) {
  return (
    <div className="bg-white rounded-2xl overflow-hidden border border-slate-100 shadow-sm hover:shadow-lg transition-all duration-300 hover:-translate-y-1 group">
      <div className="relative h-52 overflow-hidden">
        <Image
          src={img}
          alt={title}
          fill
          className="object-cover group-hover:scale-105 transition-transform duration-500"
          unoptimized
        />
        <div className="absolute inset-0 bg-gradient-to-t from-[#0f172a]/70 via-transparent to-transparent" />
        <div className="absolute bottom-3 left-4">
          <div className="w-9 h-9 bg-blue-600 rounded-xl flex items-center justify-center shadow-lg">
            <Icon size={16} className="text-white" />
          </div>
        </div>
      </div>
      <div className="p-5">
        <h3 className="font-bold text-slate-900 text-base mb-2">{title}</h3>
        <p className="text-sm text-slate-500 leading-relaxed">{desc}</p>
      </div>
    </div>
  );
}

/* ─── how it works step ───────────────────────────────────────────────────── */
function Step({ n, title, desc }: { n: number; title: string; desc: string }) {
  return (
    <div className="flex gap-4">
      <div className="flex flex-col items-center">
        <div className="w-10 h-10 rounded-full bg-[#0f172a] text-white text-sm font-bold flex items-center justify-center shrink-0 shadow-md">
          {n}
        </div>
        {n < 4 && <div className="w-px flex-1 bg-slate-200 mt-2 min-h-[32px]" />}
      </div>
      <div className="pb-6">
        <p className="font-semibold text-slate-900 text-sm mb-1">{title}</p>
        <p className="text-sm text-slate-500 leading-relaxed">{desc}</p>
      </div>
    </div>
  );
}

/* ─── main component ──────────────────────────────────────────────────────── */
export default function DashboardPage() {
  const [data, setData] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function load() {
    try {
      setLoading(true);
      setError('');
      setData(await getDashboard());
    } catch {
      setError('Could not connect to backend. Make sure the server is running on port 8000.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  return (
    <div className="min-h-screen bg-slate-50">

      {/* ── Hero banner ──────────────────────────────────────────────────── */}
      <div className="bg-[#0f172a] px-8 py-10">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Zap size={16} className="text-blue-400" />
                <span className="text-blue-400 text-xs font-semibold uppercase tracking-widest">
                  Dashboard
                </span>
              </div>
              <h1 className="text-3xl font-extrabold text-white leading-tight">
                Processing Dashboard
              </h1>
              <p className="text-slate-400 mt-2 text-sm max-w-xl">
                AI-powered end-to-end accounts payable automation. Upload any vendor invoice
                and get a reasoned decision in seconds.
              </p>
            </div>
            <div className="flex gap-3 shrink-0">
              <button
                onClick={load}
                className="flex items-center gap-2 px-4 py-2.5 text-sm text-slate-300 border border-slate-600 rounded-xl hover:bg-slate-800 transition-colors"
              >
                <RefreshCw size={14} />
                Refresh
              </button>
              <Link
                href="/upload"
                className="flex items-center gap-2 px-5 py-2.5 text-sm font-semibold text-white bg-blue-600 rounded-xl hover:bg-blue-500 transition-colors shadow-lg shadow-blue-900/40"
              >
                <Upload size={14} />
                Upload Invoice
              </Link>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="mt-5 p-4 bg-red-900/30 border border-red-700/40 rounded-xl text-red-300 text-sm">
              {error}
            </div>
          )}

          {/* Stat cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-8">
            {loading ? (
              [...Array(4)].map((_, i) => (
                <div key={i} className="bg-slate-800 rounded-2xl p-6 h-32 animate-pulse" />
              ))
            ) : data ? (
              <>
                <StatCard label="Total Processed"   value={data.total_processed} icon={FileText}    iconBg="bg-slate-600" />
                <StatCard label="Approved"           value={data.approved}        icon={CheckCircle}  iconBg="bg-emerald-500" change={data.approved > 0 ? 'Auto-approved' : undefined} />
                <StatCard label="Needs Review"       value={data.needs_review}    icon={AlertCircle}  iconBg="bg-amber-500" />
                <StatCard label="Flagged / Rejected" value={data.flagged}         icon={XCircle}      iconBg="bg-red-500" />
              </>
            ) : null}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-8 py-10 space-y-14">

        {/* ── What We Do — photo cards ──────────────────────────────────── */}
        <section>
          <div className="flex items-end justify-between mb-6">
            <div>
              <p className="text-xs font-semibold text-blue-600 uppercase tracking-widest mb-1">Capabilities</p>
              <h2 className="text-2xl font-extrabold text-slate-900">What this system does</h2>
            </div>
            <Link href="/upload" className="hidden md:flex items-center gap-1.5 text-sm font-medium text-blue-600 hover:text-blue-700">
              Try it now <ArrowRight size={14} />
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
            <FeatureCard
              img="https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=640&h=400&fit=crop&auto=format"
              icon={FileText}
              title="PDF Extraction & OCR"
              desc="Accepts any vendor invoice PDF — digital or scanned. Classifies the document type and extracts full text using PyMuPDF or Tesseract OCR."
            />
            <FeatureCard
              img="https://images.unsplash.com/photo-1677442135703-1787eea5ce01?w=640&h=400&fit=crop&auto=format"
              icon={Cpu}
              title="AI Field Extraction"
              desc="Google Gemini reads the raw text and returns structured JSON — vendor name, invoice number, PO reference, line items, amounts and dates."
            />
            <FeatureCard
              img="https://images.unsplash.com/photo-1600880292203-757bb62b4baf?w=640&h=400&fit=crop&auto=format"
              icon={GitMerge}
              title="Vendor & PO Matching"
              desc="Matches vendors by GSTIN first, then name and aliases. Verifies PO ownership, checks remaining balance and flags currency mismatches."
            />
            <FeatureCard
              img="https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=640&h=400&fit=crop&auto=format"
              icon={ShieldCheck}
              title="Rules Engine & Decision"
              desc="11 deterministic business rules evaluate every invoice and produce a final decision: Approved, Needs Review, or Rejected — with full explanation."
            />
          </div>
        </section>

        {/* ── How it works + Recent invoices ───────────────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

          {/* How it works */}
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-7">
            <p className="text-xs font-semibold text-blue-600 uppercase tracking-widest mb-1">Pipeline</p>
            <h2 className="text-lg font-extrabold text-slate-900 mb-6">How it works</h2>
            <Step n={1} title="Upload PDF" desc="Drag-and-drop any vendor invoice. File is validated and classified instantly." />
            <Step n={2} title="Extract & Validate" desc="AI extracts all fields. Arithmetic, dates and required fields are checked deterministically." />
            <Step n={3} title="Match & Check" desc="Vendor verified by GSTIN, PO matched with ownership verification, duplicate detection runs." />
            <Step n={4} title="Decision & Audit" desc="A final decision is recorded with explanation, recommended action and full audit trail." />
          </div>

          {/* Recent invoices */}
          <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
            <div className="px-6 py-5 border-b border-slate-100 flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-blue-600 uppercase tracking-widest mb-0.5">Latest</p>
                <h2 className="font-extrabold text-slate-900">Recent Invoices</h2>
              </div>
              <Link href="/invoices" className="flex items-center gap-1.5 text-sm font-medium text-blue-600 hover:text-blue-700">
                View all <ArrowRight size={13} />
              </Link>
            </div>

            {loading ? (
              <div className="p-6 space-y-3 animate-pulse">
                {[...Array(4)].map((_, i) => <div key={i} className="h-10 bg-slate-100 rounded-lg" />)}
              </div>
            ) : !data || data.recent_invoices.length === 0 ? (
              <div className="py-20 text-center">
                <div className="w-16 h-16 bg-slate-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <ClipboardList size={28} className="text-slate-400" />
                </div>
                <p className="font-semibold text-slate-700">No invoices processed yet</p>
                <p className="text-sm text-slate-400 mt-1 mb-5">Upload your first invoice to get started</p>
                <Link
                  href="/upload"
                  className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-semibold text-white bg-blue-600 rounded-xl hover:bg-blue-500 transition-colors"
                >
                  <Upload size={14} /> Upload Invoice
                </Link>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-100 text-xs text-slate-400 uppercase tracking-wide">
                      <th className="px-5 py-3 text-left font-semibold">Invoice #</th>
                      <th className="px-5 py-3 text-left font-semibold">Vendor</th>
                      <th className="px-5 py-3 text-right font-semibold">Amount</th>
                      <th className="px-5 py-3 text-left font-semibold">Date</th>
                      <th className="px-5 py-3 text-left font-semibold">Status</th>
                      <th className="px-5 py-3" />
                    </tr>
                  </thead>
                  <tbody>
                    {data.recent_invoices.map((inv, i) => (
                      <tr
                        key={inv.id}
                        className={`border-b border-slate-50 hover:bg-slate-50 transition-colors ${
                          i === data.recent_invoices.length - 1 ? 'border-0' : ''
                        }`}
                      >
                        <td className="px-5 py-3.5 font-mono text-xs text-slate-700 font-medium">
                          {inv.invoice_number ?? <span className="text-slate-400 italic font-sans">missing</span>}
                        </td>
                        <td className="px-5 py-3.5 text-slate-700 max-w-[160px] truncate text-sm">
                          {inv.vendor_name ?? <span className="text-slate-400 italic">unknown</span>}
                        </td>
                        <td className="px-5 py-3.5 text-right font-semibold text-slate-900">
                          {fmt(inv.total, inv.currency ?? 'INR')}
                        </td>
                        <td className="px-5 py-3.5 text-slate-500 text-xs">
                          {inv.invoice_date ?? fmtDate(inv.upload_time)}
                        </td>
                        <td className="px-5 py-3.5">
                          <StatusBadge status={inv.final_status} />
                        </td>
                        <td className="px-5 py-3.5">
                          <Link
                            href={`/invoices/${inv.id}`}
                            className="inline-flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-700"
                          >
                            View <ArrowRight size={11} />
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* ── CTA banner ────────────────────────────────────────────────── */}
        <div className="bg-[#0f172a] rounded-2xl p-8 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div>
            <h3 className="text-xl font-extrabold text-white">Ready to process an invoice?</h3>
            <p className="text-slate-400 text-sm mt-1">
              Upload a PDF and watch the full 10-stage pipeline run in real time.
            </p>
          </div>
          <Link
            href="/upload"
            className="shrink-0 flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl transition-colors shadow-lg shadow-blue-900/40 text-sm"
          >
            <Upload size={15} /> Upload Invoice Now
          </Link>
        </div>

      </div>
    </div>
  );
}
