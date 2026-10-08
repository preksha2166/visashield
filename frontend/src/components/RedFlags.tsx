import {
  BadgeAlert,
  CircleCheck,
  ExternalLink,
  EyeOff,
  Flag,
  Gift,
  HandCoins,
  Hourglass,
  KeyRound,
  Link,
  Mail,
  MessageCircleWarning,
  Phone,
  Siren,
  TriangleAlert,
  type LucideIcon,
} from 'lucide-react'
import type { Reason } from '../types'

const ICON_RULES: [RegExp, LucideIcon][] = [
  [/payment|gift|fee|bond|money|crypto|wire|zelle|advance/i, HandCoins],
  [/pii|ssn|passport|bank|credential|personal/i, KeyRound],
  [/secre/i, EyeOff],
  [/fear|threat|arrest|deport/i, Siren],
  [/urgen|deadline/i, Hourglass],
  [/too_good|unrealistic/i, Gift],
  [/email|reply_to|spf|dkim|dmarc|sender/i, Mail],
  [/phone|number|caller/i, Phone],
  [/domain|url|link|website/i, Link],
  [/messag|whatsapp|unsolicited/i, MessageCircleWarning],
  [/authority|gov|agency|official_rule/i, BadgeAlert],
]

function iconFor(signal: string): LucideIcon {
  return ICON_RULES.find(([re]) => re.test(signal))?.[1] ?? TriangleAlert
}

function strength(weight: number, max: number): { label: string; className: string } {
  // Relative to the strongest flag, but with a floor so a lone weak signal isn't called "Strong".
  const ratio = Math.abs(weight) / Math.max(max, 0.3)
  if (ratio >= 0.66)
    return { label: 'Strong', className: 'bg-red-100 text-red-800 dark:bg-red-950/60 dark:text-red-200' }
  if (ratio >= 0.33)
    return { label: 'Moderate', className: 'bg-amber-100 text-amber-900 dark:bg-amber-950/60 dark:text-amber-200' }
  return { label: 'Minor', className: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300' }
}

function SourceLink({ reason }: { reason: Reason }) {
  if (!reason.source_url) return null
  return (
    <a
      href={reason.source_url}
      target="_blank"
      rel="noopener noreferrer"
      className="mt-1 inline-flex items-center gap-1 text-xs font-medium text-teal-700 hover:underline dark:text-teal-300"
    >
      Source: {reason.source_title || hostname(reason.source_url)}
      <ExternalLink className="size-3" aria-hidden />
    </a>
  )
}

function hostname(url: string): string {
  try {
    return new URL(url).hostname
  } catch {
    return url
  }
}

export function RedFlags({ reasons, safe = false }: { reasons: Reason[]; safe?: boolean }) {
  const flags = reasons.filter((r) => r.weight > 0)
  const reassuring = reasons.filter((r) => r.weight <= 0)
  const max = Math.max(0, ...flags.map((r) => Math.abs(r.weight)))

  if (!reasons.length) return null

  return (
    <section aria-labelledby="red-flags-title">
      <h3 id="red-flags-title" className="section-title">
        <Flag className="size-4.5 text-red-600 dark:text-red-400" aria-hidden />
        {safe ? 'Worth double-checking' : 'Red flags we found'}
      </h3>
      {flags.length ? (
        <ul className="mt-3 space-y-2">
          {flags.map((r, i) => {
            const Icon = iconFor(r.signal)
            const s = strength(r.weight, max)
            return (
              <li
                key={`${r.signal}-${i}`}
                className="flex gap-3 rounded-xl border border-slate-200 bg-slate-50/60 p-3 dark:border-slate-800 dark:bg-slate-950/40"
              >
                <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-red-100 text-red-700 dark:bg-red-950/70 dark:text-red-300">
                  <Icon className="size-4" aria-hidden />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-[15px] leading-snug text-slate-800 dark:text-slate-200">{r.text}</p>
                  <div className="flex flex-wrap items-center gap-x-3">
                    <SourceLink reason={r} />
                  </div>
                </div>
                <span
                  className={`h-fit shrink-0 rounded-full px-2 py-0.5 text-[11px] font-semibold ${s.className}`}
                  title={`Signal weight ${r.weight.toFixed(2)}`}
                >
                  {s.label}
                </span>
              </li>
            )
          })}
        </ul>
      ) : (
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">We didn't find any strong red flags.</p>
      )}

      {reassuring.length > 0 && (
        <>
          <h4 className="mt-4 text-sm font-semibold text-slate-700 dark:text-slate-300">Reassuring signs</h4>
          <ul className="mt-2 space-y-2">
            {reassuring.map((r, i) => (
              <li key={`${r.signal}-${i}`} className="flex gap-3 text-[15px] leading-snug text-slate-700 dark:text-slate-300">
                <CircleCheck className="mt-0.5 size-4.5 shrink-0 text-emerald-600 dark:text-emerald-400" aria-hidden />
                <div className="min-w-0">
                  <p>{r.text}</p>
                  <SourceLink reason={r} />
                </div>
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  )
}
