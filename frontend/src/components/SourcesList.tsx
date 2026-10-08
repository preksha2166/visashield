import { BookOpen, ExternalLink } from 'lucide-react'
import type { Source } from '../types'

function hostname(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return url
  }
}

/** Official sources the explanation is grounded in (these come from the curated knowledge base). */
export function SourcesList({ sources }: { sources: Source[] }) {
  const safe = sources.filter((s) => /^https?:\/\//i.test(s.url))
  if (!safe.length) return null

  return (
    <section aria-labelledby="sources-title">
      <h3 id="sources-title" className="section-title">
        <BookOpen className="size-4.5 text-slate-600 dark:text-slate-400" aria-hidden />
        Sources
      </h3>
      <ul className="mt-3 space-y-2">
        {safe.map((s, i) => (
          <li key={`${s.url}-${i}`}>
            <a
              href={s.url}
              target="_blank"
              rel="noopener noreferrer"
              className="group block rounded-xl border border-slate-200 p-3 transition-colors hover:border-teal-600 dark:border-slate-800 dark:hover:border-teal-400"
            >
              <span className="flex items-start justify-between gap-3">
                <span className="min-w-0">
                  <span className="block font-medium text-slate-900 group-hover:text-teal-800 dark:text-slate-100 dark:group-hover:text-teal-300">
                    {s.title || hostname(s.url)}
                  </span>
                  <span className="block text-xs text-slate-500 dark:text-slate-400">{hostname(s.url)}</span>
                </span>
                <ExternalLink className="mt-0.5 size-4 shrink-0 text-slate-400" aria-hidden />
              </span>
              {s.snippet && (
                <span className="mt-1.5 block text-sm text-slate-600 dark:text-slate-400">“{s.snippet}”</span>
              )}
            </a>
          </li>
        ))}
      </ul>
    </section>
  )
}
