import Link from 'next/link';
import { Zap } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="bg-[#0f172a] text-slate-400">
      <div className="max-w-7xl mx-auto px-6 py-12 grid grid-cols-1 md:grid-cols-4 gap-10">
        <div className="md:col-span-2">
          <div className="flex items-center gap-2.5 mb-3">
            <div className="w-9 h-9 bg-gradient-to-br from-blue-500 to-blue-700 rounded-xl flex items-center justify-center">
              <Zap size={18} className="text-white" />
            </div>
            <span className="font-extrabold text-lg text-white">Invoice<span className="text-blue-400">AI</span></span>
          </div>
          <p className="text-sm max-w-sm leading-relaxed">
            AI-powered accounts payable automation — extract, validate, match and decide on vendor
            invoices with a full audit trail.
          </p>
        </div>
        <div>
          <p className="text-xs font-semibold text-slate-300 uppercase tracking-widest mb-3">Product</p>
          <ul className="space-y-2 text-sm">
            <li><Link href="/#features" className="hover:text-white">Features</Link></li>
            <li><Link href="/#how-it-works" className="hover:text-white">How It Works</Link></li>
            <li><Link href="/#faq" className="hover:text-white">FAQ</Link></li>
          </ul>
        </div>
        <div>
          <p className="text-xs font-semibold text-slate-300 uppercase tracking-widest mb-3">Workspace</p>
          <ul className="space-y-2 text-sm">
            <li><Link href="/dashboard" className="hover:text-white">Dashboard</Link></li>
            <li><Link href="/upload" className="hover:text-white">Upload Invoice</Link></li>
            <li><Link href="/invoices" className="hover:text-white">Invoice History</Link></li>
          </ul>
        </div>
      </div>
      <div className="border-t border-slate-800 py-5 text-center text-xs text-slate-500">
        © {new Date().getFullYear()} InvoiceAI · PS-1 · Finance / AP · v2.0
      </div>
    </footer>
  );
}
