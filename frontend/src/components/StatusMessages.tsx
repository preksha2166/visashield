import { CircleAlert, FlaskConical, RotateCcw, WifiOff } from 'lucide-react'

export function OfflineBanner({ onRetry, retrying }: { onRetry: () => void; retrying: boolean }) {
  return (
    <div
      role="status"
      className="mb-4 flex flex-col gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900 sm:flex-row sm:items-center sm:justify-between dark:border-amber-900/70 dark:bg-amber-950/40 dark:text-amber-200"
    >
      <p className="flex gap-2">
        <WifiOff className="mt-0.5 size-4 shrink-0" aria-hidden />
        <span>
          <strong className="font-semibold">The VisaShield server is offline right now.</strong> You can still paste
          your message — we'll try again when you press Check. Until then, don't reply, pay, or share anything.
        </span>
      </p>
      <button
        type="button"
        onClick={onRetry}
        disabled={retrying}
        className="inline-flex shrink-0 items-center justify-center gap-1.5 rounded-lg border border-amber-300 bg-white/70 px-3 py-1.5 font-medium hover:bg-white disabled:opacity-60 dark:border-amber-800 dark:bg-amber-950/60 dark:hover:bg-amber-950"
      >
        <RotateCcw className={`size-4 ${retrying ? 'animate-spin' : ''}`} aria-hidden />
        {retrying ? 'Checking…' : 'Try again'}
      </button>
    </div>
  )
}

export function MockBanner() {
  return (
    <div
      role="status"
      className="mb-4 flex gap-2 rounded-2xl border border-violet-200 bg-violet-50 p-3 text-sm text-violet-900 dark:border-violet-900/70 dark:bg-violet-950/40 dark:text-violet-200"
    >
      <FlaskConical className="mt-0.5 size-4 shrink-0" aria-hidden />
      <span>
        <strong className="font-semibold">Demo mode.</strong> Results are sample data, not a real analysis. Remove{' '}
        <code className="rounded bg-violet-100 px-1 dark:bg-violet-900/60">?mock=1</code> from the address to use the
        live checker.
      </span>
    </div>
  )
}

export function ErrorState({
  message,
  offline,
  onRetry,
}: {
  message: string
  offline: boolean
  onRetry: () => void
}) {
  return (
    <div role="alert" className="card border-red-200 p-5 dark:border-red-900/70">
      <div className="flex gap-3">
        <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-red-100 text-red-700 dark:bg-red-950/70 dark:text-red-300">
          {offline ? <WifiOff className="size-5" aria-hidden /> : <CircleAlert className="size-5" aria-hidden />}
        </span>
        <div className="min-w-0 flex-1">
          <h2 className="font-semibold text-slate-900 dark:text-white">
            {offline ? "We couldn't reach the checker" : "We couldn't check this message"}
          </h2>
          <p className="mt-1 text-sm break-words text-slate-600 dark:text-slate-400">{message}</p>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
            While you wait: don't reply, pay, or share personal details. If you're worried, contact your DSO using the
            number on your school's official website.
          </p>
          <button
            type="button"
            onClick={onRetry}
            className="mt-4 inline-flex items-center gap-1.5 rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-200"
          >
            <RotateCcw className="size-4" aria-hidden />
            Try again
          </button>
        </div>
      </div>
    </div>
  )
}

export function LoadingState() {
  return (
    <div className="card p-4 sm:p-6" aria-hidden>
      <div className="animate-pulse space-y-4">
        <div className="flex items-center gap-4 rounded-2xl bg-slate-100 p-5 dark:bg-slate-800/70">
          <div className="size-12 rounded-xl bg-slate-200 dark:bg-slate-700" />
          <div className="flex-1 space-y-2">
            <div className="h-3 w-24 rounded bg-slate-200 dark:bg-slate-700" />
            <div className="h-4 w-3/4 rounded bg-slate-200 dark:bg-slate-700" />
          </div>
        </div>
        <div className="space-y-2 px-1">
          <div className="h-3 w-1/3 rounded bg-slate-200 dark:bg-slate-700" />
          <div className="h-10 rounded-xl bg-slate-100 dark:bg-slate-800/70" />
          <div className="h-10 rounded-xl bg-slate-100 dark:bg-slate-800/70" />
          <div className="h-10 rounded-xl bg-slate-100 dark:bg-slate-800/70" />
        </div>
      </div>
    </div>
  )
}
