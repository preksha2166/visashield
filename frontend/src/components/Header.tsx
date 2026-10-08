import { GraduationCap, ShieldCheck } from 'lucide-react'

export type BackendStatus = 'checking' | 'online' | 'degraded' | 'offline' | 'mock'

const STATUS: Record<BackendStatus, { dot: string; label: string }> = {
  checking: { dot: 'bg-slate-400 animate-pulse', label: 'Connecting…' },
  online: { dot: 'bg-emerald-500', label: 'Online' },
  degraded: { dot: 'bg-amber-500', label: 'Limited mode' },
  offline: { dot: 'bg-red-500', label: 'Offline' },
  mock: { dot: 'bg-violet-500', label: 'Demo data' },
}

export function Header({ status }: { status: BackendStatus }) {
  const s = STATUS[status]
  return (
    <header className="pt-6 pb-5 sm:pt-10 sm:pb-8">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <span className="flex size-10 items-center justify-center rounded-xl bg-teal-700 text-white shadow-sm dark:bg-teal-500 dark:text-slate-950">
            <ShieldCheck className="size-6" aria-hidden />
          </span>
          <span className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">VisaShield</span>
        </div>
        <span
          className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400"
          title="Backend status"
        >
          <span className={`size-2 rounded-full ${s.dot}`} aria-hidden />
          {s.label}
        </span>
      </div>
      <h1 className="mt-5 text-2xl leading-tight font-semibold tracking-tight text-balance text-slate-900 sm:text-3xl dark:text-white">
        Check a suspicious call, text, or job offer before you respond.
      </h1>
      <p className="mt-2 max-w-2xl text-[15px] text-slate-600 dark:text-slate-400">
        Fake ICE, USCIS and SEVIS calls and fake OPT jobs target international students. Paste what you received and
        we'll tell you how risky it looks and what to do next.
      </p>
      <span className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-teal-50 px-3 py-1 text-xs font-semibold text-teal-800 ring-1 ring-teal-200 dark:bg-teal-950/50 dark:text-teal-200 dark:ring-teal-900">
        <GraduationCap className="size-3.5" aria-hidden />
        Built for international students · F-1, OPT &amp; STEM OPT
      </span>
    </header>
  )
}
