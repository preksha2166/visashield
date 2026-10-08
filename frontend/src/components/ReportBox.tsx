import { Check, Copy, ExternalLink, Megaphone } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

const REPORT_LINKS = [
  {
    href: 'https://reportfraud.ftc.gov',
    title: 'ReportFraud.ftc.gov',
    note: 'Federal Trade Commission — scams, imposters, fake jobs',
  },
  {
    href: 'https://www.ic3.gov',
    title: 'IC3.gov',
    note: "FBI Internet Crime Complaint Center — especially if you lost money",
  },
]

async function copyText(text: string, fallbackEl: HTMLTextAreaElement | null): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    // Older browsers / insecure contexts: select the textarea and use execCommand.
    if (!fallbackEl) return false
    fallbackEl.focus()
    fallbackEl.select()
    try {
      return document.execCommand('copy')
    } catch {
      return false
    }
  }
}

export function ReportBox({ reportText }: { reportText?: string | null }) {
  const [copied, setCopied] = useState<'idle' | 'ok' | 'fail'>('idle')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (copied === 'idle') return
    const t = setTimeout(() => setCopied('idle'), 2500)
    return () => clearTimeout(t)
  }, [copied])

  return (
    <section aria-labelledby="report-title">
      <h3 id="report-title" className="section-title">
        <Megaphone className="size-4.5 text-teal-700 dark:text-teal-400" aria-hidden />
        Report it
      </h3>
      <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
        Reporting helps stop scammers targeting other students. It's free and doesn't affect your visa status.
      </p>

      {reportText && (
        <div className="mt-3">
          <div className="mb-1.5 flex items-center justify-between gap-3">
            <label htmlFor="report-text" className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Ready-to-paste report
            </label>
            <button
              type="button"
              onClick={async () => setCopied((await copyText(reportText, textareaRef.current)) ? 'ok' : 'fail')}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              {copied === 'ok' ? (
                <>
                  <Check className="size-4 text-emerald-600 dark:text-emerald-400" aria-hidden />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="size-4" aria-hidden />
                  {copied === 'fail' ? 'Select & copy manually' : 'Copy'}
                </>
              )}
            </button>
          </div>
          <textarea
            id="report-text"
            ref={textareaRef}
            readOnly
            value={reportText}
            rows={6}
            onFocus={(e) => e.currentTarget.select()}
            className="block w-full resize-y rounded-xl border border-slate-300 bg-slate-50 px-3 py-2.5 text-sm leading-relaxed text-slate-800 focus:outline-none dark:border-slate-700 dark:bg-slate-950 dark:text-slate-200"
          />
          <span className="sr-only" aria-live="polite">
            {copied === 'ok' ? 'Report text copied to clipboard' : ''}
          </span>
        </div>
      )}

      <div className="mt-3 grid gap-2 sm:grid-cols-2">
        {REPORT_LINKS.map((l) => (
          <a
            key={l.href}
            href={l.href}
            target="_blank"
            rel="noopener noreferrer"
            className="group flex items-start justify-between gap-3 rounded-xl border border-slate-200 bg-white p-3 transition-colors hover:border-teal-600 dark:border-slate-800 dark:bg-slate-900 dark:hover:border-teal-400"
          >
            <span className="min-w-0">
              <span className="block font-semibold text-teal-800 dark:text-teal-300">{l.title}</span>
              <span className="block text-xs text-slate-600 dark:text-slate-400">{l.note}</span>
            </span>
            <ExternalLink
              className="mt-0.5 size-4 shrink-0 text-slate-400 group-hover:text-teal-700 dark:group-hover:text-teal-300"
              aria-hidden
            />
          </a>
        ))}
      </div>
    </section>
  )
}
