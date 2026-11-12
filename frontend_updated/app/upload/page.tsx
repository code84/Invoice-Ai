'use client';
import { useCallback, useState } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import {
  Upload, FileText, AlertCircle, CheckCircle,
  ScanLine, Cpu, Users, GitMerge, ShieldCheck,
  ClipboardCheck, Zap, ArrowRight,
} from 'lucide-react';
import { uploadInvoice } from '@/lib/api';

const STEPS = [
  { icon: ScanLine,       label: 'PDF Classification',      desc: 'Digital or scanned detection' },
  { icon: FileText,       label: 'Text / OCR Extraction',   desc: 'PyMuPDF or Tesseract' },
  { icon: Cpu,            label: 'AI Field Extraction',     desc: 'Gemini structured JSON' },
  { icon: ClipboardCheck, label: 'Field Validation',        desc: 'Arithmetic & required fields' },
  { icon: Users,          label: 'Vendor Verification',     desc: 'GSTIN + fuzzy name match' },
  { icon: GitMerge,       label: 'PO Matching',             desc: 'Ownership + balance check' },
  { icon: ShieldCheck,    label: 'Duplicate Detection',     desc: 'Two-tier smart deduplication' },
  { icon: Zap,            label: 'Business Rules',          desc: '11 deterministic rules' },
  { icon: CheckCircle,    label: 'Decision & Audit Trail',  desc: 'Explanation + recommended action' },
];

export default function UploadPage() {
  const router = useRouter();
  const [dragging, setDragging] = useState(false);
  const [file, setFile]       = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError]     = useState('');

  function handleFile(f: File) {
    setError('');
    if (!f.name.toLowerCase().endsWith('.pdf')) { setError('Only PDF files are accepted.'); return; }
    if (f.size > 20 * 1024 * 1024)             { setError('File must be under 20 MB.'); return; }
    setFile(f);
  }

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }, []);

  async function submit() {
    if (!file) return;
    setUploading(true); setError('');
    try {
      const run = await uploadInvoice(file);
      router.push(`/runs/${run.id}`);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg ?? 'Upload failed. Please try again.');
      setUploading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">

      {/* Hero */}
      <div className="bg-[#0f172a] px-8 py-10">
        <div className="max-w-5xl mx-auto">
          <p className="text-blue-400 text-xs font-semibold uppercase tracking-widest mb-2">Invoice Upload</p>
          <h1 className="text-3xl font-extrabold text-white mb-1">Upload a Vendor Invoice</h1>
          <p className="text-slate-400 text-sm">
            Drop any PDF invoice and the AI pipeline starts automatically — results in under 30 seconds.
          </p>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-8 py-10">
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">

          {/* Left — drop zone + submit */}
          <div className="lg:col-span-3 space-y-5">

            {/* Drop zone */}
            <div
              onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={onDrop}
              onClick={() => document.getElementById('file-input')?.click()}
              className={`
                relative border-2 border-dashed rounded-2xl p-14 text-center cursor-pointer
                transition-all duration-200
                ${dragging
                  ? 'border-blue-500 bg-blue-50 scale-[1.01]'
                  : file
                  ? 'border-emerald-400 bg-emerald-50'
                  : 'border-slate-200 bg-white hover:border-blue-400 hover:bg-blue-50/40'}
              `}
            >
              <input
                id="file-input" type="file" accept=".pdf" className="hidden"
                onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
              />
              {file ? (
                <div className="animate-fade-in">
                  <div className="w-16 h-16 bg-emerald-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                    <CheckCircle size={32} className="text-emerald-500" />
                  </div>
                  <p className="font-bold text-emerald-700 text-lg truncate max-w-xs mx-auto">{file.name}</p>
                  <p className="text-sm text-emerald-600 mt-1">
                    {(file.size / 1024).toFixed(1)} KB &middot; PDF ready
                  </p>
                  <button
                    onClick={(e) => { e.stopPropagation(); setFile(null); }}
                    className="mt-3 text-xs text-slate-400 hover:text-red-500 transition-colors underline"
                  >
                    Remove file
                  </button>
                </div>
              ) : (
                <>
                  <div className="w-16 h-16 bg-slate-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                    <Upload size={28} className={dragging ? 'text-blue-500' : 'text-slate-400'} />
                  </div>
                  <p className="font-bold text-slate-700 text-lg">
                    {dragging ? 'Drop to upload' : 'Drag & drop your invoice PDF'}
                  </p>
                  <p className="text-sm text-slate-400 mt-1">or click to browse files</p>
                  <p className="text-xs text-slate-300 mt-3 bg-slate-50 inline-block px-3 py-1 rounded-full border border-slate-200">
                    PDF only &middot; Max 20 MB
                  </p>
                </>
              )}
            </div>

            {error && (
              <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm animate-fade-in">
                <AlertCircle size={16} className="mt-0.5 shrink-0" />
                {error}
              </div>
            )}

            {/* File card + CTA */}
            {file && (
              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5 animate-slide-up">
                <div className="flex items-center gap-4 mb-5">
                  <div className="w-12 h-12 bg-red-50 rounded-xl flex items-center justify-center shrink-0">
                    <FileText size={22} className="text-red-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-slate-900 truncate">{file.name}</p>
                    <p className="text-xs text-slate-500 mt-0.5">
                      {(file.size / 1024).toFixed(1)} KB &middot; Ready to process
                    </p>
                  </div>
                  <span className="text-xs font-medium text-emerald-600 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-full">
                    PDF
                  </span>
                </div>
                <button
                  onClick={submit}
                  disabled={uploading}
                  className="w-full flex items-center justify-center gap-2.5 py-3.5 px-4 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-400 text-white font-semibold rounded-xl transition-colors shadow-md shadow-blue-200 text-sm"
                >
                  {uploading ? (
                    <>
                      <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Starting pipeline…
                    </>
                  ) : (
                    <>
                      <Upload size={16} />
                      Start Processing
                      <ArrowRight size={14} />
                    </>
                  )}
                </button>
              </div>
            )}

            {/* Photo card */}
            <div className="relative rounded-2xl overflow-hidden h-44 shadow-sm">
              <Image
                src="https://images.unsplash.com/photo-1450101499163-c8848c66ca85?w=800&h=350&fit=crop&auto=format"
                alt="Invoice processing workflow"
                fill className="object-cover"
                unoptimized
              />
              <div className="absolute inset-0 bg-gradient-to-r from-[#0f172a]/80 to-transparent flex items-center px-7">
                <div>
                  <p className="text-white font-bold text-lg leading-tight">
                    Zero manual data entry.
                  </p>
                  <p className="text-slate-300 text-sm mt-1">
                    AI extracts every field automatically.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Right — pipeline steps */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6 sticky top-24">
              <p className="text-xs font-semibold text-blue-600 uppercase tracking-widest mb-1">After upload</p>
              <h3 className="font-extrabold text-slate-900 text-base mb-5">9-Stage Pipeline</h3>
              <ol className="space-y-3">
                {STEPS.map((s, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <div className="w-7 h-7 rounded-lg bg-slate-100 flex items-center justify-center shrink-0 mt-0.5">
                      <s.icon size={14} className="text-slate-600" />
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-slate-800">{s.label}</p>
                      <p className="text-xs text-slate-400">{s.desc}</p>
                    </div>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
