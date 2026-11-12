'use client';
import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  CheckCircle, XCircle, Loader2, Circle,
  ChevronDown, ArrowRight, Zap,
} from 'lucide-react';
import { getRun } from '@/lib/api';
import type { ProcessingRunDetail, ProcessingStage } from '@/lib/types';

const STAGE_ICONS: Record<string, string> = {
  upload:       '📤',
  classify:     '🔍',
  extract_text: '📄',
  ai_extract:   '🤖',
  normalize:    '🔧',
  validate:     '✅',
  vendor_po:    '🏢',
  duplicate:    '🛡️',
  rules:        '⚡',
  decision:     '🎯',
};

function StageRow({ stage, index }: { stage: ProcessingStage; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const hasDetail = !!(stage.output_summary || stage.error_message);

  const isCompleted = stage.status === 'completed';
  const isRunning   = stage.status === 'running';
  const isFailed    = stage.status === 'failed';
  const isPending   = stage.status === 'pending';

  return (
    <div className={`rounded-2xl border transition-all duration-200 overflow-hidden ${
      isRunning   ? 'border-blue-200 bg-blue-50/60 shadow-sm shadow-blue-100'  :
      isCompleted ? 'border-slate-100 bg-white'                               :
      isFailed    ? 'border-red-200 bg-red-50/60'                             :
                    'border-slate-100 bg-white opacity-50'
    }`}>
      <button
        className="w-full flex items-center gap-4 px-5 py-4 text-left"
        onClick={() => hasDetail && setExpanded(!expanded)}
        disabled={!hasDetail}
      >
        {/* Number */}
        <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
          isCompleted ? 'bg-emerald-100 text-emerald-700' :
          isRunning   ? 'bg-blue-100 text-blue-700'       :
          isFailed    ? 'bg-red-100 text-red-700'         :
                        'bg-slate-100 text-slate-400'
        }`}>
          {index + 1}
        </span>

        {/* Emoji */}
        <span className={`text-lg shrink-0 ${isPending ? 'opacity-30' : ''}`}>
          {STAGE_ICONS[stage.stage_name] ?? '📋'}
        </span>

        {/* Label */}
        <span className={`flex-1 text-sm font-semibold ${
          isPending ? 'text-slate-400' : 'text-slate-800'
        }`}>
          {stage.stage_label}
        </span>

        {/* Status pill */}
        <span className={`text-xs font-medium px-2.5 py-1 rounded-full shrink-0 ${
          isCompleted ? 'bg-emerald-100 text-emerald-700' :
          isRunning   ? 'bg-blue-100 text-blue-700'       :
          isFailed    ? 'bg-red-100 text-red-700'         :
                        'bg-slate-100 text-slate-400'
        }`}>
          {isRunning ? (
            <span className="flex items-center gap-1.5">
              <Loader2 size={11} className="animate-spin" /> Running
            </span>
          ) : isCompleted ? (
            <span className="flex items-center gap-1.5">
              <CheckCircle size={11} /> Done
            </span>
          ) : isFailed ? (
            <span className="flex items-center gap-1.5">
              <XCircle size={11} /> Failed
            </span>
          ) : (
            <span className="flex items-center gap-1.5">
              <Circle size={11} /> Pending
            </span>
          )}
        </span>

        {hasDetail && (
          <ChevronDown
            size={14}
            className={`text-slate-400 transition-transform shrink-0 ${expanded ? 'rotate-180' : ''}`}
          />
        )}
      </button>

      {expanded && hasDetail && (
        <div className={`px-5 pb-4 text-xs leading-relaxed border-t ${
          isFailed ? 'border-red-200 text-red-700' : 'border-slate-100 text-slate-600'
        }`}>
          <p className="pt-3">{stage.error_message ?? stage.output_summary}</p>
        </div>
      )}
    </div>
  );
}

export default function RunPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [run, setRun] = useState<ProcessingRunDetail | null>(null);
  const [invoiceId, setInvoiceId] = useState('');

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    async function poll() {
      try {
        const r = await getRun(id);
        setRun(r);
        setInvoiceId(r.invoice_id);
        if (r.status === 'running') timer = setTimeout(poll, 1500);
      } catch {
        timer = setTimeout(poll, 2000);
      }
    }
    poll();
    return () => clearTimeout(timer);
  }, [id]);

  const stages    = run ? [...run.stages].sort((a, b) => a.order_index - b.order_index) : [];
  const completed = stages.filter(s => s.status === 'completed').length;
  const progress  = stages.length ? Math.round((completed / stages.length) * 100) : 0;

  const isComplete = run?.status === 'completed';
  const isFailed   = run?.status === 'failed';

  return (
    <div className="min-h-screen bg-slate-50">

      {/* Hero */}
      <div className="bg-[#0f172a] px-8 py-10">
        <div className="max-w-2xl mx-auto">
          <div className="flex items-center gap-2 mb-2">
            <Zap size={14} className="text-blue-400" />
            <span className="text-blue-400 text-xs font-semibold uppercase tracking-widest">
              Live Processing
            </span>
          </div>
          <h1 className="text-2xl font-extrabold text-white">
            {run?.run_id ?? 'Starting…'}
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            {isComplete ? 'Processing complete — view the full results below.' :
             isFailed   ? 'Processing encountered an error.' :
                          'Pipeline is running — stages update in real time.'}
          </p>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-8 py-8 space-y-6">

        {/* Progress card */}
        {run && (
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm font-semibold text-slate-700">
                {isComplete ? 'All stages complete' :
                 isFailed   ? 'Pipeline stopped' :
                              `Stage ${completed + 1} of ${stages.length} running…`}
              </p>
              <span className={`text-2xl font-extrabold ${
                isComplete ? 'text-emerald-600' :
                isFailed   ? 'text-red-500'     :
                             'text-blue-600'
              }`}>
                {progress}%
              </span>
            </div>

            {/* Progress bar */}
            <div className="w-full bg-slate-100 rounded-full h-3 mb-5 overflow-hidden">
              <div
                className={`h-3 rounded-full transition-all duration-700 ease-out ${
                  isFailed   ? 'bg-red-500'     :
                  isComplete ? 'bg-emerald-500' :
                               'bg-blue-500'
                }`}
                style={{ width: `${progress}%` }}
              />
            </div>

            {/* Stage dots */}
            <div className="flex gap-1.5">
              {stages.map((s) => (
                <div
                  key={s.id}
                  title={s.stage_label}
                  className={`flex-1 h-1.5 rounded-full transition-colors ${
                    s.status === 'completed' ? 'bg-emerald-400' :
                    s.status === 'running'   ? 'bg-blue-400 animate-pulse' :
                    s.status === 'failed'    ? 'bg-red-400'    :
                                              'bg-slate-200'
                  }`}
                />
              ))}
            </div>

            {isComplete && (
              <button
                onClick={() => router.push(`/invoices/${invoiceId}`)}
                className="mt-5 w-full flex items-center justify-center gap-2 py-3.5 bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold rounded-xl transition-colors shadow-md shadow-blue-200"
              >
                View Invoice Results <ArrowRight size={15} />
              </button>
            )}
          </div>
        )}

        {/* Stages */}
        <div className="space-y-2.5">
          {!run ? (
            [...Array(10)].map((_, i) => (
              <div key={i} className="h-14 bg-white border border-slate-100 rounded-2xl animate-pulse" />
            ))
          ) : (
            stages.map((stage, i) => <StageRow key={stage.id} stage={stage} index={i} />)
          )}
        </div>

        {/* Error */}
        {run?.status === 'failed' && run.error_message && (
          <div className="p-5 bg-red-50 border border-red-200 rounded-2xl text-red-700 text-sm">
            <p className="font-bold mb-1">Pipeline Error</p>
            <p className="text-red-600">{run.error_message}</p>
          </div>
        )}

      </div>
    </div>
  );
}
