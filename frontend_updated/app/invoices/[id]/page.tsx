'use client';
import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  CheckCircle, AlertCircle, XCircle, FileText,
  ChevronRight, ExternalLink, ArrowLeft, Zap,
} from 'lucide-react';
import { getInvoice, getInvoiceRuns, getRun, API_BASE } from '@/lib/api';
import type { InvoiceDetail, ProcessingRunDetail, ValidationResult } from '@/lib/types';
import StatusBadge from '@/components/StatusBadge';

function fmt(val: number | null, currency = 'INR') {
  if (val == null) return '—';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency', currency, maximumFractionDigits: 2,
  }).format(val);
}

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">{label}</p>
      <p className="text-sm font-semibold text-slate-900 break-words">
        {value ?? <span className="text-slate-300 italic font-normal">—</span>}
      </p>
    </div>
  );
}

function ValidationRow({ vr }: { vr: ValidationResult }) {
  const isPassed  = vr.result === 'passed';
  const isFailed  = vr.result === 'failed';
  const isReview  = vr.result === 'review';
  const isWarning = vr.result === 'warning';

  const icon =
    isPassed            ? <CheckCircle size={14} className="text-emerald-500 shrink-0 mt-0.5" /> :
    isFailed            ? <XCircle     size={14} className="text-red-500 shrink-0 mt-0.5" />     :
    (isReview||isWarning)? <AlertCircle size={14} className="text-amber-500 shrink-0 mt-0.5" />  :
                          <AlertCircle size={14} className="text-slate-400 shrink-0 mt-0.5" />;

  const bg =
    isPassed             ? 'bg-emerald-50 border-emerald-100' :
    isFailed             ? 'bg-red-50 border-red-100'         :
    (isReview||isWarning)? 'bg-amber-50 border-amber-100'     :
                           'bg-slate-50 border-slate-100';

  return (
    <div className={`flex gap-3 p-3.5 rounded-xl border text-xs ${bg}`}>
      {icon}
      <div className="flex-1 min-w-0">
        <span className="font-mono text-slate-500 text-[11px]">{vr.check_name}</span>
        <p className="text-slate-700 mt-0.5 leading-relaxed">{vr.message}</p>
        {vr.observed_value && (
          <p className="text-slate-500 mt-1">
            Observed: <span className="font-semibold text-slate-700">{vr.observed_value}</span>
          </p>
        )}
      </div>
    </div>
  );
}

function Section({ title, subtitle, children }: {
  title: string; subtitle?: string; children: React.ReactNode;
}) {
  return (
    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden mb-5">
      <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/60">
        <h3 className="text-sm font-bold text-slate-800">{title}</h3>
        {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
      </div>
      <div className="p-6">{children}</div>
    </div>
  );
}

export default function InvoiceDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [invoice, setInvoice] = useState<InvoiceDetail | null>(null);
  const [run, setRun]         = useState<ProcessingRunDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [inv, runs] = await Promise.all([getInvoice(id), getInvoiceRuns(id)]);
        setInvoice(inv);
        if (runs.length > 0) {
          const detail = await getRun(runs[0].id);
          setRun(detail);
        }
      } finally { setLoading(false); }
    }
    load();
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 p-8 max-w-4xl mx-auto space-y-4 animate-pulse">
        <div className="h-32 bg-white rounded-2xl border border-slate-100" />
        {[...Array(3)].map((_, i) => <div key={i} className="h-48 bg-white rounded-2xl border border-slate-100" />)}
      </div>
    );
  }
  if (!invoice) {
    return <div className="p-8 text-center text-slate-500">Invoice not found.</div>;
  }

  const validations = run?.validation_results.filter(v => !v.check_name.startsWith('R')) ?? [];
  const ruleResults = run?.validation_results.filter(v => v.check_name.startsWith('R')) ?? [];
  const currency    = invoice.currency ?? 'INR';
  const isApproved  = invoice.final_status === 'approved';
  const isRejected  = invoice.final_status === 'rejected';

  return (
    <div className="min-h-screen bg-slate-50">

      {/* Hero */}
      <div className={`px-8 py-8 ${
        isApproved ? 'bg-gradient-to-r from-[#0f172a] to-emerald-900' :
        isRejected ? 'bg-gradient-to-r from-[#0f172a] to-red-900'    :
                     'bg-gradient-to-r from-[#0f172a] to-slate-800'
      }`}>
        <div className="max-w-4xl mx-auto">
          {/* Breadcrumb */}
          <div className="flex items-center gap-2 text-sm text-slate-400 mb-4">
            <Link href="/invoices" className="flex items-center gap-1 hover:text-slate-200 transition-colors">
              <ArrowLeft size={13} /> Invoices
            </Link>
            <ChevronRight size={13} />
            <span className="text-slate-300 font-medium">
              {invoice.invoice_number ?? invoice.filename}
            </span>
          </div>

          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Zap size={14} className="text-blue-400" />
                <span className="text-blue-400 text-xs font-semibold uppercase tracking-widest">Invoice Detail</span>
              </div>
              <h1 className="text-2xl font-extrabold text-white leading-tight">
                {invoice.invoice_number ?? <span className="italic text-slate-400">No invoice number</span>}
              </h1>
              <p className="text-slate-400 text-sm mt-1">{invoice.vendor_name ?? 'Unknown vendor'}</p>
            </div>

            <div className="flex flex-col items-start md:items-end gap-2 shrink-0">
              <StatusBadge status={invoice.final_status} size="lg" />
              {invoice.is_duplicate && (
                <span className="text-xs font-bold text-red-400 bg-red-900/30 border border-red-700/40 px-2.5 py-1 rounded-full">
                  ⚠ Duplicate Detected
                </span>
              )}
              {invoice.duplicate_of_id && !invoice.is_duplicate && (
                <span className="text-xs font-bold text-amber-400 bg-amber-900/30 border border-amber-700/40 px-2.5 py-1 rounded-full">
                  ↩ Resubmission
                </span>
              )}
              <p className="text-2xl font-extrabold text-white">
                {fmt(invoice.total, currency)}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-8 py-8">

        {/* Decision box */}
        {invoice.decision_explanation && (
          <div className={`mb-5 p-5 rounded-2xl border ${
            isApproved ? 'bg-emerald-50 border-emerald-200' :
            isRejected ? 'bg-red-50 border-red-200'         :
                         'bg-amber-50 border-amber-200'
          }`}>
            <p className={`text-xs font-bold uppercase tracking-wider mb-2 ${
              isApproved ? 'text-emerald-700' :
              isRejected ? 'text-red-700'     :
                           'text-amber-700'
            }`}>
              Decision
            </p>
            <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-line">
              {invoice.decision_explanation}
            </p>
            {invoice.recommended_action && (
              <div className={`mt-3 pt-3 border-t text-sm font-semibold ${
                isApproved ? 'border-emerald-200 text-emerald-800' :
                isRejected ? 'border-red-200 text-red-800'         :
                             'border-amber-200 text-amber-800'
              }`}>
                → {invoice.recommended_action}
              </div>
            )}
          </div>
        )}

        {/* Invoice fields */}
        <Section title="Extracted Invoice Fields" subtitle="All fields extracted by AI and normalized">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
            <Field label="Vendor"         value={invoice.vendor_name} />
            <Field label="Invoice Number" value={invoice.invoice_number} />
            <Field label="Invoice Date"   value={invoice.invoice_date} />
            <Field label="Due Date"       value={invoice.due_date} />
            <Field label="PO Reference"   value={invoice.po_number} />
            <Field label="Currency"       value={invoice.currency} />
            <Field label="Subtotal"       value={fmt(invoice.subtotal, currency)} />
            <Field label="Tax"            value={
              invoice.tax != null
                ? `${fmt(invoice.tax, currency)}${invoice.tax_rate ? ` (${invoice.tax_rate}%)` : ''}`
                : null
            } />
            <Field label="Total"          value={
              <span className="text-lg font-extrabold">{fmt(invoice.total, currency)}</span>
            } />
            <Field label="Payment Terms"  value={invoice.payment_terms} />
            <Field label="GSTIN / Tax ID" value={invoice.tax_id} />
            <Field label="PDF Type"       value={
              invoice.pdf_type
                ? <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                    invoice.pdf_type === 'digital'
                      ? 'bg-blue-100 text-blue-700'
                      : 'bg-purple-100 text-purple-700'
                  }`}>{invoice.pdf_type}</span>
                : null
            } />
          </div>

          {/* Confidence bar */}
          {invoice.extraction_confidence != null && (
            <div className="mt-6 pt-5 border-t border-slate-100">
              <div className="flex items-center justify-between text-xs mb-2">
                <span className="font-semibold text-slate-600">Extraction Confidence</span>
                <span className={`font-extrabold text-sm ${
                  invoice.extraction_confidence >= 0.8 ? 'text-emerald-600' :
                  invoice.extraction_confidence >= 0.6 ? 'text-amber-600'   :
                                                         'text-red-600'
                }`}>
                  {Math.round(invoice.extraction_confidence * 100)}%
                </span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                <div
                  className={`h-2 rounded-full transition-all ${
                    invoice.extraction_confidence >= 0.8 ? 'bg-emerald-500' :
                    invoice.extraction_confidence >= 0.6 ? 'bg-amber-500'   :
                                                           'bg-red-500'
                  }`}
                  style={{ width: `${invoice.extraction_confidence * 100}%` }}
                />
              </div>
            </div>
          )}

          {/* Missing fields */}
          {invoice.missing_fields.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              <span className="text-xs font-semibold text-slate-500 self-center">Missing fields:</span>
              {invoice.missing_fields.map(f => (
                <span key={f} className="text-xs bg-amber-50 text-amber-700 border border-amber-200 px-2.5 py-1 rounded-full font-medium">
                  {f}
                </span>
              ))}
            </div>
          )}
        </Section>

        {/* Line items */}
        {invoice.line_items.length > 0 && (
          <Section title="Line Items" subtitle={`${invoice.line_items.length} items`}>
            <div className="overflow-x-auto -mx-2">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-xs text-slate-400 uppercase tracking-wider border-b border-slate-100">
                    <th className="pb-2.5 text-left font-semibold px-2">Description</th>
                    <th className="pb-2.5 text-right font-semibold px-2">Qty</th>
                    <th className="pb-2.5 text-right font-semibold px-2">Unit Price</th>
                    <th className="pb-2.5 text-right font-semibold px-2">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {invoice.line_items.map((li, i) => (
                    <tr key={i} className="border-b border-slate-50 last:border-0">
                      <td className="py-3 text-slate-700 px-2">{li.description}</td>
                      <td className="py-3 text-right text-slate-500 px-2">{li.quantity ?? '—'}</td>
                      <td className="py-3 text-right text-slate-500 px-2">{fmt(li.unit_price, currency)}</td>
                      <td className="py-3 text-right font-bold text-slate-900 px-2">{fmt(li.amount, currency)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Section>
        )}

        {/* Field Validation */}
        {validations.length > 0 && (
          <Section title="Field Validation" subtitle="Arithmetic and required field checks">
            <div className="space-y-2">
              {validations.map(vr => <ValidationRow key={vr.id} vr={vr} />)}
            </div>
          </Section>
        )}

        {/* Business Rules */}
        {ruleResults.length > 0 && (
          <Section title="Business Rules" subtitle={`${ruleResults.length} rules evaluated`}>
            <div className="space-y-2">
              {ruleResults.map(vr => <ValidationRow key={vr.id} vr={vr} />)}
            </div>
          </Section>
        )}

        {/* Audit Trail */}
        {run && run.audit_events.length > 0 && (
          <Section title="Audit Trail" subtitle="Chronological processing events">
            <ol className="relative border-l-2 border-slate-100 ml-2 space-y-5">
              {[...run.audit_events]
                .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
                .map(ev => (
                  <li key={ev.id} className="ml-5">
                    <div className="absolute w-3 h-3 bg-blue-500 rounded-full -left-[7px] border-2 border-white shadow-sm mt-1" />
                    <p className="text-[11px] text-slate-400 font-medium mb-0.5">
                      {new Date(ev.created_at).toLocaleTimeString('en-IN', {
                        hour: '2-digit', minute: '2-digit', second: '2-digit',
                      })}
                      <span className="ml-2 font-mono bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded text-[10px]">
                        {ev.event_type}
                      </span>
                    </p>
                    <p className="text-sm text-slate-700 font-medium">{ev.description}</p>
                  </li>
                ))}
            </ol>
          </Section>
        )}

        {/* PDF link */}
        <div className="mt-2 text-center pb-8">
          <a
            href={`${API_BASE}/uploads/${invoice.file_path?.split(/[\\/]/).pop() ?? invoice.filename}`}
            target="_blank" rel="noreferrer"
            className="inline-flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 font-medium border border-blue-200 bg-blue-50 px-5 py-2.5 rounded-xl hover:bg-blue-100 transition-colors"
          >
            <FileText size={15} />
            View Original PDF
            <ExternalLink size={12} />
          </a>
        </div>
      </div>
    </div>
  );
}
