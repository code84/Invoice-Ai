import type { FinalStatus } from '@/lib/types';

interface Props {
  status: FinalStatus | string | null;
  size?: 'sm' | 'md' | 'lg';
}

const cfg: Record<string, { bg: string; text: string; border: string; dot: string; label: string }> = {
  approved:     { bg: 'bg-emerald-50',  text: 'text-emerald-700', border: 'border-emerald-200', dot: 'bg-emerald-500', label: 'Approved' },
  needs_review: { bg: 'bg-amber-50',    text: 'text-amber-700',   border: 'border-amber-200',   dot: 'bg-amber-400',   label: 'Needs Review' },
  rejected:     { bg: 'bg-red-50',      text: 'text-red-700',     border: 'border-red-200',     dot: 'bg-red-500',     label: 'Rejected' },
  running:      { bg: 'bg-blue-50',     text: 'text-blue-700',    border: 'border-blue-200',    dot: 'bg-blue-500',    label: 'Processing' },
  default:      { bg: 'bg-slate-100',   text: 'text-slate-600',   border: 'border-slate-200',   dot: 'bg-slate-400',   label: 'Pending' },
};

export default function StatusBadge({ status, size = 'md' }: Props) {
  const key = (status as string) ?? 'default';
  const c = cfg[key] ?? cfg.default;
  const px = size === 'sm'
    ? 'px-2 py-0.5 text-xs'
    : size === 'lg'
    ? 'px-3.5 py-1.5 text-sm font-semibold'
    : 'px-2.5 py-1 text-xs font-medium';

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border ${px} ${c.bg} ${c.text} ${c.border}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${c.dot} ${key === 'running' ? 'animate-pulse' : ''}`} />
      {c.label}
    </span>
  );
}
