import Link from 'next/link';
import Image from 'next/image';
import {
  FileText, Cpu, GitMerge, ShieldCheck, Upload, ArrowRight, CheckCircle,
  Zap, ScanText, Copy, ClipboardCheck, History, Scale, Clock, ChevronDown,
  LayoutDashboard, PlayCircle,
} from 'lucide-react';

/* ─── data ────────────────────────────────────────────────────────────────── */
const stats = [
  { v: '10', l: 'Pipeline stages' },
  { v: '11', l: 'Business rules' },
  { v: '3', l: 'Possible decisions' },
  { v: '100%', l: 'Audit-trailed' },
];

const pipeline = [
  {
    img: 'https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=800&h=520&fit=crop&auto=format',
    icon: FileText, tag: 'Step 1',
    title: 'PDF Extraction & OCR',
    desc: 'Accepts any vendor invoice PDF — digital or scanned. The document is classified and its full text is extracted using PyMuPDF or Tesseract OCR.',
    points: ['Digital & scanned PDFs', 'Document-type classification', 'Instant file validation'],
  },
  {
    img: 'https://images.unsplash.com/photo-1677442135703-1787eea5ce01?w=800&h=520&fit=crop&auto=format',
    icon: Cpu, tag: 'Step 2',
    title: 'AI Field Extraction',
    desc: 'Google Gemini reads the raw text and returns structured JSON — vendor name, invoice number, PO reference, line items, amounts and dates.',
    points: ['Structured JSON output', 'Line items & totals', 'Arithmetic and date checks'],
  },
  {
    img: 'https://images.unsplash.com/photo-1600880292203-757bb62b4baf?w=800&h=520&fit=crop&auto=format',
    icon: GitMerge, tag: 'Step 3',
    title: 'Vendor & PO Matching',
    desc: 'Vendors are matched by GSTIN first, then by name and aliases. PO ownership is verified, remaining balance checked and currency mismatches flagged.',
    points: ['GSTIN-first vendor match', 'PO ownership & balance', 'Duplicate detection'],
  },
  {
    img: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&h=520&fit=crop&auto=format',
    icon: ShieldCheck, tag: 'Step 4',
    title: 'Rules Engine & Decision',
    desc: '11 deterministic business rules evaluate every invoice and produce a final decision — Approved, Needs Review or Rejected — with a full explanation.',
    points: ['Explainable decisions', 'Recommended next action', 'Complete audit trail'],
  },
];

const benefits = [
  { icon: Clock, t: 'Decisions in seconds', d: 'Upload a PDF and watch the full pipeline run in real time — no manual keying.' },
  { icon: ScanText, t: 'Scanned & digital PDFs', d: 'OCR fallback means photographed or scanned invoices are handled too.' },
  { icon: Copy, t: 'Duplicate detection', d: 'Catch repeat submissions before they turn into duplicate payments.' },
  { icon: Scale, t: 'Rule-based consistency', d: 'The same deterministic rules apply to every invoice, every time.' },
  { icon: ClipboardCheck, t: 'Explained outcomes', d: 'Every decision comes with reasoning and a recommended action.' },
  { icon: History, t: 'Full audit history', d: 'Each processing run is stored and can be reopened stage by stage.' },
];

const steps = [
  { t: 'Upload PDF', d: 'Drag and drop any vendor invoice. The file is validated and classified instantly.' },
  { t: 'Extract & Validate', d: 'AI extracts all fields. Arithmetic, dates and required fields are checked deterministically.' },
  { t: 'Match & Check', d: 'Vendor verified by GSTIN, PO matched with ownership checks, duplicates detected.' },
  { t: 'Decision & Audit', d: 'A final decision is recorded with explanation, recommended action and audit trail.' },
];

const faqs = [
  { q: 'What file types can I upload?', a: 'Vendor invoices in PDF format — both digitally generated and scanned. Scanned documents go through Tesseract OCR.' },
  { q: 'How are fields extracted?', a: 'Google Gemini reads the extracted text and returns structured data (vendor, invoice number, PO, line items, amounts, dates). Results are then validated deterministically.' },
  { q: 'How does vendor matching work?', a: 'Vendors are matched by GSTIN first, then by name and aliases. The matched PO is checked for ownership, remaining balance and currency.' },
  { q: 'What decisions can the system make?', a: 'Approved, Needs Review or Rejected — each with an explanation and a recommended action.' },
  { q: 'Can I see past results?', a: 'Yes. Invoice History lists every processed invoice, and each invoice page lets you reopen its processing runs and audit trail.' },
];

/* ─── page ────────────────────────────────────────────────────────────────── */
export default function LandingPage() {
  return (
    <div className="bg-white">

      {/* ── Hero ─────────────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden bg-gradient-to-b from-blue-50 via-white to-white">
        <div className="max-w-7xl mx-auto px-6 pt-16 pb-12 text-center">
          <span className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-blue-100 text-blue-700 text-xs font-semibold">
            <Zap size={13} /> AI-powered · 10-stage pipeline · Explainable decisions
          </span>
          <h1 className="mt-6 text-4xl md:text-6xl font-extrabold tracking-tight text-slate-900 leading-[1.1]">
            Intelligent <span className="text-blue-600">Invoice Processing</span>
          </h1>
          <p className="mt-5 max-w-2xl mx-auto text-lg text-slate-600 leading-relaxed">
            End-to-end accounts payable automation. Upload any vendor invoice and get a
            reasoned decision in seconds — extracted, validated, matched and audited.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Link href="/upload" className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 transition-colors shadow-lg shadow-blue-600/20">
              <Upload size={16} /> Upload an Invoice
            </Link>
            <Link href="#how-it-works" className="inline-flex items-center gap-2 px-6 py-3 rounded-lg border border-slate-300 bg-white text-slate-800 font-semibold hover:bg-slate-50 transition-colors">
              <PlayCircle size={16} /> See How It Works
            </Link>
          </div>

          {/* Product preview */}
          <div className="mt-14 mx-auto max-w-4xl rounded-2xl border border-slate-200 bg-white shadow-2xl shadow-blue-900/10 overflow-hidden text-left">
            <div className="flex items-center gap-1.5 px-4 py-3 bg-slate-100 border-b border-slate-200">
              <span className="w-3 h-3 rounded-full bg-red-400" /><span className="w-3 h-3 rounded-full bg-amber-400" /><span className="w-3 h-3 rounded-full bg-emerald-400" />
              <span className="ml-3 text-xs text-slate-500">Invoice #INV-2041 · Decision</span>
            </div>
            <div className="p-6 grid md:grid-cols-3 gap-4">
              {[
                ['Vendor', 'Matched by GSTIN', 'text-emerald-600'],
                ['PO & balance', 'Verified', 'text-emerald-600'],
                ['Duplicate check', 'No duplicates', 'text-emerald-600'],
              ].map(([k, v, c]) => (
                <div key={k} className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                  <p className="text-xs text-slate-500">{k}</p>
                  <p className={`mt-1 font-semibold flex items-center gap-1.5 ${c}`}><CheckCircle size={15} />{v}</p>
                </div>
              ))}
              <div className="md:col-span-3 rounded-xl bg-emerald-50 border border-emerald-200 p-4 flex items-center justify-between">
                <div>
                  <p className="text-xs text-emerald-700 font-semibold uppercase tracking-wide">Final decision</p>
                  <p className="text-emerald-900 font-bold">Approved — all 11 rules passed</p>
                </div>
                <ShieldCheck className="text-emerald-600" size={28} />
              </div>
            </div>
          </div>

          <p className="mt-3 text-xs text-slate-400">Illustrative preview</p>

          {/* Stats row */}
          <div className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto">
            {stats.map((s) => (
              <div key={s.l}>
                <p className="text-3xl md:text-4xl font-extrabold text-blue-600">{s.v}</p>
                <p className="mt-1 text-sm text-slate-500 font-medium">{s.l}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── What is ──────────────────────────────────────────────────────── */}
      <section className="py-20 bg-white">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <p className="text-xs font-semibold text-blue-600 uppercase tracking-widest mb-2">Overview</p>
          <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900">What is automated invoice processing?</h2>
          <p className="mt-5 text-slate-600 leading-relaxed text-lg">
            Invoice processing is the accounts-payable workflow of capturing a vendor invoice,
            checking it against vendors and purchase orders, and deciding whether to pay. InvoiceAI
            automates every step — combining AI extraction with deterministic business rules, so each
            decision is fast, consistent and explainable.
          </p>
        </div>
      </section>

      {/* ── Pipeline (alternating) ───────────────────────────────────────── */}
      <section id="features" className="py-20 bg-slate-50 scroll-mt-20">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <p className="text-xs font-semibold text-blue-600 uppercase tracking-widest mb-2">Features</p>
            <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900">The complete invoice processing pipeline</h2>
          </div>
          <div className="space-y-20">
            {pipeline.map((p, i) => (
              <div key={p.title} className={`grid md:grid-cols-2 gap-10 items-center ${i % 2 ? 'md:[&>div:first-child]:order-2' : ''}`}>
                <div className="relative h-72 rounded-2xl overflow-hidden shadow-xl">
                  <Image src={p.img} alt={p.title} fill className="object-cover" unoptimized />
                  <div className="absolute inset-0 bg-gradient-to-t from-[#0f172a]/50 to-transparent" />
                </div>
                <div>
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center"><p.icon size={18} className="text-white" /></div>
                    <span className="text-xs font-semibold text-blue-600 uppercase tracking-widest">{p.tag}</span>
                  </div>
                  <h3 className="text-2xl font-extrabold text-slate-900">{p.title}</h3>
                  <p className="mt-3 text-slate-600 leading-relaxed">{p.desc}</p>
                  <ul className="mt-5 space-y-2">
                    {p.points.map((pt) => (
                      <li key={pt} className="flex items-center gap-2 text-sm text-slate-700 font-medium">
                        <CheckCircle size={16} className="text-emerald-500 shrink-0" /> {pt}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Benefits ─────────────────────────────────────────────────────── */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-12">
            <p className="text-xs font-semibold text-blue-600 uppercase tracking-widest mb-2">Why InvoiceAI</p>
            <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900">Built for accounts payable teams</h2>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {benefits.map((b) => (
              <div key={b.t} className="rounded-2xl border border-slate-200 bg-white p-6 hover:shadow-lg hover:-translate-y-1 transition-all">
                <div className="w-11 h-11 rounded-xl bg-blue-50 flex items-center justify-center mb-4"><b.icon size={20} className="text-blue-600" /></div>
                <h3 className="font-bold text-slate-900 mb-1.5">{b.t}</h3>
                <p className="text-sm text-slate-500 leading-relaxed">{b.d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How it works ─────────────────────────────────────────────────── */}
      <section id="how-it-works" className="py-20 bg-slate-50 scroll-mt-20">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-14">
            <p className="text-xs font-semibold text-blue-600 uppercase tracking-widest mb-2">Process</p>
            <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900">How it works</h2>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {steps.map((s, i) => (
              <div key={s.t} className="relative rounded-2xl bg-white border border-slate-200 p-6">
                <div className="w-10 h-10 rounded-full bg-[#0f172a] text-white font-bold flex items-center justify-center mb-4">{i + 1}</div>
                <h3 className="font-bold text-slate-900 mb-1.5">{s.t}</h3>
                <p className="text-sm text-slate-500 leading-relaxed">{s.d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Mid CTA ──────────────────────────────────────────────────────── */}
      <section className="py-16 bg-white">
        <div className="max-w-5xl mx-auto px-6">
          <div className="rounded-3xl bg-gradient-to-br from-[#0f172a] to-blue-900 px-8 py-12 text-center">
            <h2 className="text-2xl md:text-3xl font-extrabold text-white">Invoice backlog slowing your AP team?</h2>
            <p className="mt-3 text-slate-300 max-w-xl mx-auto">Upload a PDF and watch the full pipeline run in real time.</p>
            <div className="mt-7 flex flex-wrap justify-center gap-3">
              <Link href="/upload" className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-blue-500 hover:bg-blue-400 text-white font-semibold transition-colors">
                <Upload size={16} /> Upload Invoice
              </Link>
              <Link href="/dashboard" className="inline-flex items-center gap-2 px-6 py-3 rounded-lg border border-slate-500 text-white font-semibold hover:bg-white/10 transition-colors">
                <LayoutDashboard size={16} /> Open Dashboard
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ── FAQ ──────────────────────────────────────────────────────────── */}
      <section id="faq" className="py-20 bg-slate-50 scroll-mt-20">
        <div className="max-w-3xl mx-auto px-6">
          <div className="text-center mb-10">
            <p className="text-xs font-semibold text-blue-600 uppercase tracking-widest mb-2">FAQ</p>
            <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900">Frequently asked questions</h2>
          </div>
          <div className="space-y-3">
            {faqs.map((f) => (
              <details key={f.q} className="group rounded-xl bg-white border border-slate-200 px-5 py-4">
                <summary className="flex items-center justify-between cursor-pointer font-semibold text-slate-900 list-none">
                  {f.q}
                  <ChevronDown size={18} className="text-slate-400 group-open:rotate-180 transition-transform" />
                </summary>
                <p className="mt-3 text-sm text-slate-600 leading-relaxed">{f.a}</p>
              </details>
            ))}
          </div>
        </div>
      </section>

      {/* ── Closing CTA ──────────────────────────────────────────────────── */}
      <section className="py-20 bg-white text-center">
        <div className="max-w-2xl mx-auto px-6">
          <h2 className="text-3xl md:text-4xl font-extrabold text-slate-900">Ready to automate your invoice processing?</h2>
          <Link href="/upload" className="mt-8 inline-flex items-center gap-2 px-7 py-3.5 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 transition-colors shadow-lg shadow-blue-600/20">
            Get Started <ArrowRight size={16} />
          </Link>
        </div>
      </section>
    </div>
  );
}
