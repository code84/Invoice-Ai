'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  FileText, Upload, RefreshCw, Search,
  ArrowRight, ChevronDown, Zap,
} from 'lucide-react';
import { getInvoices } from '@/lib/api';
import type { InvoiceSummary } from '@/lib/types';
import StatusBadge from '@/components/StatusBadge';

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

const FILTERS = ['all', 'approved', 'needs_review', 'rejected'] as const;
type Filter = typeof FILTERS[number];

const FILTER_LABELS: Record<Filter, string> = {
  all: 'All', approved: 'Approved', needs_review: 'Needs Review', rejected: 'Rejected',
};

export default function InvoicesPage() {
  const [invoices, setInvoices] = useState<InvoiceSummary[]>([]);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState('');
  const [filter, setFilter]     = useState<Filter>('all');
  const [search, setSearch]     = useState('');
  const [sortBy, setSortBy]     = useState<'date' | 'amount'>('date');

  async function load() {
    try { setLoading(true); setError(''); setInvoices(await getInvoices()); }
    catch { setError('Failed to load invoices.'); }
    finally { setLoading(false); }
  }
  useEffect(() => { load(); }, []);

  const filtered = invoices
    .filter(inv => {
      const matchStatus = filter === 'all' || inv.final_status === filter;
      const q = search.toLowerCase();
      const matchSearch = !q ||
        (inv.invoice_number ?? '').toLowerCase().includes(q) ||
        (inv.vendor_name ?? '').toLowerCase().includes(q) ||
        (inv.po_number ?? '').toLowerCase().includes(q);
      return matchStatus && matchSearch;
    })
    .sort((a, b) => {
      if (sortBy === 'amount') return (b.total ?? 0) - (a.total ?? 0);
      return new Date(b.upload_time).getTime() - new Date(a.upload_time).getTime();
    });

  const counts = {
    all:          invoices.length,
    approved:     invoices.filter(i => i.final_status === 'approved').length,
    needs_review: invoices.filter(i => i.final_status === 'needs_review').length,
    rejected:     invoices.filter(i => i.final_status === 'rejected').length,
  };

  return (
    <div className="min-h-screen bg-slate-50">

      {/* Hero */}
      <div className="bg-[#0f172a] px-8 py-10">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Zap size={14} className="text-blue-400" />
              <span className="text-blue-400 text-xs font-semibold uppercase tracking-widest">Invoice History</span>
            </div>
            <h1 className="text-2xl font-extrabold text-white">All Processed Invoices</h1>
            <p className="text-slate-400 text-sm mt-1">Search, filter and inspect every invoice and its outcome.</p>
          </div>
          <div className="flex gap-3 shrink-0">
            <button
              onClick={load}
              className="flex items-center gap-2 px-4 py-2.5 text-sm text-slate-300 border border-slate-600 rounded-xl hover:bg-slate-800 transition-colors"
            >
              <RefreshCw size={14} /> Refresh
            </button>
            <Link
              href="/upload"
              className="flex items-center gap-2 px-5 py-2.5 text-sm font-semibold text-white bg-blue-600 rounded-xl hover:bg-blue-500 transition-colors shadow-lg shadow-blue-900/40"
            >
              <Upload size={14} /> Upload New
            </Link>
          </div>
        </div>

        {/* Summary mini-cards */}
        {!loading && (
          <div className="max-w-7xl mx-auto mt-6 grid grid-cols-2 md:grid-cols-4 gap-3">
            {FILTERS.map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`text-left p-3 rounded-xl border transition-all ${
                  filter === f
                    ? 'bg-blue-600 border-blue-500 shadow-md'
                    : 'bg-slate-800/50 border-slate-700 hover:bg-slate-800'
                }`}
              >
                <p className={`text-2xl font-extrabold ${filter === f ? 'text-white' : 'text-slate-200'}`}>
                  {counts[f]}
                </p>
                <p className={`text-xs font-medium mt-0.5 ${filter === f ? 'text-blue-100' : 'text-slate-400'}`}>
                  {FILTER_LABELS[f]}
                </p>
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="max-w-7xl mx-auto px-8 py-7">

        {/* Search + sort bar */}
        <div className="flex flex-wrap items-center gap-3 mb-5">
          <div className="relative flex-1 min-w-[220px] max-w-sm">
            <Search size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search by invoice #, vendor or PO…"
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2.5 text-sm border border-slate-200 rounded-xl bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-sm"
            />
          </div>

          <div className="flex items-center gap-2 ml-auto">
            <span className="text-xs text-slate-500">Sort by:</span>
            <button
              onClick={() => setSortBy(sortBy === 'date' ? 'amount' : 'date')}
              className="flex items-center gap-1.5 px-3 py-2 text-xs font-medium border border-slate-200 rounded-xl bg-white hover:bg-slate-50 text-slate-600 shadow-sm"
            >
              {sortBy === 'date' ? 'Date' : 'Amount'} <ChevronDown size={12} />
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">{error}</div>
        )}

        {/* Table */}
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          {loading ? (
            <div className="p-8 space-y-3 animate-pulse">
              {[...Array(6)].map((_, i) => <div key={i} className="h-12 bg-slate-100 rounded-xl" />)}
            </div>
          ) : filtered.length === 0 ? (
            <div className="py-20 text-center">
              <div className="w-16 h-16 bg-slate-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <FileText size={28} className="text-slate-400" />
              </div>
              <p className="font-semibold text-slate-700">No invoices found</p>
              {search || filter !== 'all' ? (
                <p className="text-sm text-slate-400 mt-1">Try adjusting your search or filter</p>
              ) : (
                <Link href="/upload" className="inline-flex items-center gap-2 mt-5 px-5 py-2.5 text-sm font-semibold text-white bg-blue-600 rounded-xl hover:bg-blue-500 transition-colors">
                  <Upload size={14} /> Upload First Invoice
                </Link>
              )}
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-100 text-xs text-slate-400 uppercase tracking-wider">
                      <th className="px-5 py-3.5 text-left font-semibold">Invoice #</th>
                      <th className="px-5 py-3.5 text-left font-semibold">Vendor</th>
                      <th className="px-5 py-3.5 text-right font-semibold">Amount</th>
                      <th className="px-5 py-3.5 text-left font-semibold">Invoice Date</th>
                      <th className="px-5 py-3.5 text-left font-semibold">PO Reference</th>
                      <th className="px-5 py-3.5 text-left font-semibold">Status</th>
                      <th className="px-5 py-3.5 text-left font-semibold">Uploaded</th>
                      <th className="px-5 py-3.5" />
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((inv, i) => (
                      <tr
                        key={inv.id}
                        className={`hover:bg-slate-50 transition-colors ${
                          i < filtered.length - 1 ? 'border-b border-slate-50' : ''
                        }`}
                      >
                        <td className="px-5 py-3.5">
                          <span className="font-mono text-xs text-slate-700 font-semibold">
                            {inv.invoice_number ?? <span className="italic text-slate-400 font-sans font-normal">missing</span>}
                          </span>
                          {inv.is_duplicate && (
                            <span className="ml-2 text-[10px] font-semibold text-red-600 bg-red-50 border border-red-200 px-1.5 py-0.5 rounded-full">
                              DUP
                            </span>
                          )}
                        </td>
                        <td className="px-5 py-3.5 text-slate-700 max-w-[180px]">
                          <span className="truncate block text-sm">
                            {inv.vendor_name ?? <span className="italic text-slate-400">unknown</span>}
                          </span>
                        </td>
                        <td className="px-5 py-3.5 text-right font-bold text-slate-900">
                          {fmt(inv.total, inv.currency ?? 'INR')}
                        </td>
                        <td className="px-5 py-3.5 text-xs text-slate-500">
                          {inv.invoice_date ?? '—'}
                        </td>
                        <td className="px-5 py-3.5 font-mono text-xs text-slate-500">
                          {inv.po_number ?? <span className="text-slate-300">—</span>}
                        </td>
                        <td className="px-5 py-3.5">
                          <StatusBadge status={inv.final_status} />
                        </td>
                        <td className="px-5 py-3.5 text-xs text-slate-400">
                          {fmtDate(inv.upload_time)}
                        </td>
                        <td className="px-5 py-3.5">
                          <Link
                            href={`/invoices/${inv.id}`}
                            className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-700"
                          >
                            View <ArrowRight size={11} />
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="px-5 py-3 border-t border-slate-100 flex items-center justify-between">
                <p className="text-xs text-slate-400">
                  Showing <span className="font-semibold text-slate-600">{filtered.length}</span> of{' '}
                  <span className="font-semibold text-slate-600">{invoices.length}</span> invoices
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
