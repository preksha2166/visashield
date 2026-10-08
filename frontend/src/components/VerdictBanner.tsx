import { ShieldAlert, ShieldCheck, ShieldX, Tag } from 'lucide-react'
import { verdictStyle } from '../constants'
import type { Verdict } from '../types'
import { RiskMeter } from './RiskMeter'

interface Props {
  verdict: Verdict
  summary: string
  riskScore: number
  categoryLabel: string
  claimedAgency?: string | null
}

const ICONS = {
  likely_scam: ShieldX,
  suspicious: ShieldAlert,
  likely_safe: ShieldCheck,
} as const

export function VerdictBanner({ verdict, summary, riskScore, categoryLabel, claimedAgency }: Props) {
  const style = verdictStyle(verdict)
  const Icon = ICONS[verdict] ?? ShieldAlert

  return (
    <section
      aria-label="Verdict"
      className={`rounded-2xl border p-4 sm:p-6 ${style.banner}`}
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex min-w-0 items-start gap-3 sm:gap-4">
          <span className={`flex size-11 shrink-0 items-center justify-center rounded-xl sm:size-12 ${style.tile}`}>
            <Icon className="size-6 sm:size-7" aria-hidden />
          </span>
          <div className="min-w-0">
            <p className={`text-sm font-bold tracking-wide uppercase ${style.accent}`}>{style.label}</p>
            <h2 className="mt-0.5 text-lg leading-snug font-semibold text-balance text-slate-900 sm:text-xl dark:text-white">
              {summary}
            </h2>
            <div className="mt-2 flex flex-wrap gap-2">
              <span className="inline-flex items-center gap-1 rounded-full bg-white/70 px-2.5 py-0.5 text-xs font-medium text-slate-700 ring-1 ring-slate-900/10 dark:bg-slate-900/60 dark:text-slate-200 dark:ring-white/10">
                <Tag className="size-3" aria-hidden />
                {categoryLabel}
              </span>
              {claimedAgency && (
                <span className="inline-flex items-center rounded-full bg-white/70 px-2.5 py-0.5 text-xs font-medium text-slate-700 ring-1 ring-slate-900/10 dark:bg-slate-900/60 dark:text-slate-200 dark:ring-white/10">
                  Claims to be: {claimedAgency}
                </span>
              )}
            </div>
          </div>
        </div>
        <RiskMeter score={riskScore} color={style.gauge} className="self-center sm:self-auto" />
      </div>
    </section>
  )
}
