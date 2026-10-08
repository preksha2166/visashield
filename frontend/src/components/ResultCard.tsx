import { MessageSquareText, RotateCcw } from 'lucide-react'
import type { AnalyzeResponse } from '../types'
import { ActionChecklist } from './ActionChecklist'
import { DecisionDetails } from './DecisionDetails'
import { EntitiesTable } from './EntitiesTable'
import { RedFlags } from './RedFlags'
import { ReportBox } from './ReportBox'
import { SourcesList } from './SourcesList'
import { TacticChips } from './TacticChips'
import { VerdictBanner } from './VerdictBanner'

interface Props {
  result: AnalyzeResponse
  onCheckAnother: () => void
}

function paragraphs(text: string): string[] {
  return (text ?? '')
    .split(/\n\s*\n|\n/)
    .map((p) => p.trim())
    .filter(Boolean)
}

export function ResultCard({ result, onCheckAnother }: Props) {
  const explanation = paragraphs(result.explanation)
  const showReport = Boolean(result.report_text) || result.verdict !== 'likely_safe'

  return (
    <article lang={result.language || undefined} aria-label="Result" className="card overflow-hidden">
      <div className="p-3 sm:p-4">
        <VerdictBanner
          verdict={result.verdict}
          summary={result.summary}
          riskScore={result.risk_score}
          categoryLabel={result.category_label}
          claimedAgency={result.entities?.claimed_agency}
        />
      </div>

      <div className="space-y-8 px-4 pt-3 pb-6 sm:px-7 sm:pb-8">
        <ActionChecklist actions={result.actions ?? []} />

        <RedFlags reasons={result.reasons ?? []} safe={result.verdict === 'likely_safe'} />

        <TacticChips tactics={result.tactics ?? []} />

        {explanation.length > 0 && (
          <section aria-labelledby="explanation-title">
            <h3 id="explanation-title" className="section-title">
              <MessageSquareText className="size-4.5 text-slate-600 dark:text-slate-400" aria-hidden />
              Why we think this
            </h3>
            <div className="mt-2 space-y-3 text-[15px] leading-relaxed text-slate-700 dark:text-slate-300">
              {explanation.map((p, i) => (
                <p key={i}>{p}</p>
              ))}
            </div>
          </section>
        )}

        {result.entities && <EntitiesTable entities={result.entities} />}

        {showReport && <ReportBox reportText={result.report_text} />}

        <DecisionDetails
          category={result.category}
          category_probs={result.category_probs}
          llm_used={result.llm_used}
          latency_ms={result.latency_ms}
          redacted_text={result.redacted_text}
          extracted_text={result.extracted_text}
        />

        <SourcesList sources={result.sources ?? []} />

        <div className="flex justify-center pt-2">
          <button
            type="button"
            onClick={onCheckAnother}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            <RotateCcw className="size-4" aria-hidden />
            Check another message
          </button>
        </div>
      </div>
    </article>
  )
}
