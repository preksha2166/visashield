import { Bot, ChevronDown, Clock, Cpu, Microscope } from 'lucide-react'
import { categoryLabel } from '../constants'
import type { AnalyzeResponse } from '../types'

type Props = Pick<
  AnalyzeResponse,
  'category' | 'category_probs' | 'llm_used' | 'latency_ms' | 'redacted_text' | 'extracted_text'
>

function formatLatency(ms: number): string {
  if (!Number.isFinite(ms)) return '—'
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)} s` : `${Math.round(ms)} ms`
}

/** Collapsible "How we decided": class probabilities, LLM indicator, latency, redacted input. */
export function DecisionDetails({ category, category_probs, llm_used, latency_ms, redacted_text, extracted_text }: Props) {
  const probs = Object.entries(category_probs ?? {})
    .filter(([, p]) => Number.isFinite(p))
    .sort((a, b) => b[1] - a[1])

  return (
    <details className="group rounded-xl border border-slate-200 dark:border-slate-800">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-3 rounded-xl px-4 py-3 select-none hover:bg-slate-50 dark:hover:bg-slate-800/50 [&::-webkit-details-marker]:hidden">
        <span className="section-title">
          <Microscope className="size-4.5 text-slate-600 dark:text-slate-400" aria-hidden />
          How we decided
        </span>
        <ChevronDown
          className="size-5 shrink-0 text-slate-500 transition-transform group-open:rotate-180"
          aria-hidden
        />
      </summary>

      <div className="space-y-5 border-t border-slate-200 px-4 pt-4 pb-5 dark:border-slate-800">
        <p className="text-sm text-slate-600 dark:text-slate-400">
          The verdict comes from a trained scam classifier combined with rule-based checks (official rules, domain
          and payment checks). The AI model only writes the explanation — it can't change the verdict.
        </p>

        <div className="flex flex-wrap gap-2 text-xs font-medium">
          <span
            className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 ${
              llm_used
                ? 'bg-teal-50 text-teal-800 ring-1 ring-teal-200 dark:bg-teal-950/50 dark:text-teal-200 dark:ring-teal-900'
                : 'bg-slate-100 text-slate-700 ring-1 ring-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:ring-slate-700'
            }`}
          >
            <Bot className="size-3.5" aria-hidden />
            {llm_used ? 'AI explanation used' : 'AI explanation unavailable — rules + classifier only'}
          </span>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-1 text-slate-700 ring-1 ring-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:ring-slate-700">
            <Clock className="size-3.5" aria-hidden />
            {formatLatency(latency_ms)}
          </span>
        </div>

        {probs.length > 0 && (
          <div>
            <h4 className="flex items-center gap-1.5 text-sm font-semibold text-slate-800 dark:text-slate-200">
              <Cpu className="size-4" aria-hidden />
              Classifier confidence by category
            </h4>
            <ul className="mt-2 space-y-2">
              {probs.map(([key, p]) => {
                const pct = Math.round(Math.min(1, Math.max(0, p)) * 100)
                const top = key === category
                return (
                  <li key={key}>
                    <div className="flex items-baseline justify-between gap-3 text-sm">
                      <span className={top ? 'font-semibold text-slate-900 dark:text-white' : 'text-slate-600 dark:text-slate-400'}>
                        {categoryLabel(key)}
                      </span>
                      <span className="text-slate-500 tabular-nums dark:text-slate-400">{pct}%</span>
                    </div>
                    <div
                      className="mt-1 h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800"
                      role="progressbar"
                      aria-label={categoryLabel(key)}
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-valuenow={pct}
                    >
                      <div
                        className={`h-full rounded-full ${top ? 'bg-teal-600 dark:bg-teal-400' : 'bg-slate-400 dark:bg-slate-600'}`}
                        style={{ width: `${Math.max(pct, pct > 0 ? 2 : 0)}%` }}
                      />
                    </div>
                  </li>
                )
              })}
            </ul>
          </div>
        )}

        {extracted_text && (
          <div>
            <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">Text we read from your screenshot</h4>
            <pre className="mt-2 max-h-56 overflow-auto rounded-lg bg-slate-50 p-3 font-sans text-sm whitespace-pre-wrap text-slate-700 dark:bg-slate-950 dark:text-slate-300">
              {extracted_text}
            </pre>
          </div>
        )}

        {redacted_text && (
          <div>
            <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">What we analyzed (personal numbers redacted)</h4>
            <pre className="mt-2 max-h-56 overflow-auto rounded-lg bg-slate-50 p-3 font-sans text-sm break-words whitespace-pre-wrap text-slate-700 dark:bg-slate-950 dark:text-slate-300">
              {redacted_text}
            </pre>
          </div>
        )}
      </div>
    </details>
  )
}
