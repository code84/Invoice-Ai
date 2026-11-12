'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Menu, X, Zap, Upload } from 'lucide-react';
import { useState } from 'react';

const links = [
  { href: '/',          label: 'Home' },
  { href: '/#features', label: 'Features' },
  { href: '/#how-it-works', label: 'How It Works' },
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/invoices',  label: 'Invoice History' },
];

export default function Navbar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  const isActive = (href: string) =>
    href === '/' ? pathname === '/' : !href.includes('#') && pathname.startsWith(href);

  return (
    <header className="sticky top-0 z-50 bg-white/90 backdrop-blur border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between gap-6">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-2.5 shrink-0" onClick={() => setOpen(false)}>
          <div className="w-9 h-9 bg-gradient-to-br from-blue-500 to-blue-700 rounded-xl flex items-center justify-center shadow-md shadow-blue-900/20">
            <Zap size={18} className="text-white" />
          </div>
          <span className="font-extrabold text-lg tracking-tight text-slate-900">
            Invoice<span className="text-blue-600">AI</span>
          </span>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden lg:flex items-center gap-1">
          {links.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className={`px-3.5 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive(href)
                  ? 'text-blue-600 bg-blue-50'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              {label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <span className="hidden xl:flex items-center gap-2 text-xs text-slate-500">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" /> System online
          </span>
          <Link
            href="/upload"
            className="hidden sm:inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors shadow-sm"
          >
            <Upload size={14} /> Upload Invoice
          </Link>
          <button
            className="lg:hidden p-2 rounded-lg border border-slate-200 text-slate-700"
            onClick={() => setOpen(!open)}
            aria-label="Toggle menu"
          >
            {open ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {open && (
        <div className="lg:hidden border-t border-slate-200 bg-white px-6 py-4 space-y-1">
          {links.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              onClick={() => setOpen(false)}
              className={`block px-3 py-2.5 rounded-lg text-sm font-medium ${
                isActive(href) ? 'text-blue-600 bg-blue-50' : 'text-slate-700 hover:bg-slate-100'
              }`}
            >
              {label}
            </Link>
          ))}
          <Link
            href="/upload"
            onClick={() => setOpen(false)}
            className="flex items-center justify-center gap-2 mt-3 px-4 py-2.5 text-sm font-semibold text-white bg-blue-600 rounded-lg"
          >
            <Upload size={14} /> Upload Invoice
          </Link>
        </div>
      )}
    </header>
  );
}
