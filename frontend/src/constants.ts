import type { Situation, Verdict } from './types'

export const LANGUAGES: { code: string; label: string }[] = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'हिन्दी' },
  { code: 'zh', label: '中文' },
  { code: 'es', label: 'Español' },
  { code: 'ko', label: '한국어' },
  { code: 'vi', label: 'Tiếng Việt' },
  { code: 'te', label: 'తెలుగు' },
  { code: 'pt', label: 'Português' },
  { code: 'ar', label: 'العربية' },
]

export const SITUATIONS: { value: Situation; label: string }[] = [
  { value: 'not_responded', label: "I haven't responded" },
  { value: 'paid', label: 'I paid money' },
  { value: 'shared_info', label: 'I shared personal info' },
]

export interface TacticInfo {
  label: string
  description: string
}

export const TACTICS: Record<string, TacticInfo> = {
  authority: { label: 'Authority', description: 'Claims to be an official' },
  urgency: { label: 'Urgency', description: 'Pressures you to act now' },
  fear_threat: { label: 'Threats', description: 'Threatens arrest, deportation or visa loss' },
  secrecy: { label: 'Secrecy', description: 'Tells you not to tell anyone' },
  payment_demand: { label: 'Unusual payment', description: 'Demands payment in an unusual way' },
  pii_request: { label: 'Personal info request', description: 'Asks for SSN, passport or bank details' },
  advance_fee: { label: 'Upfront fee', description: 'Asks you to pay to get a job/money' },
  too_good: { label: 'Unrealistic offer', description: 'Too good to be true' },
}

export function humanize(key: string): string {
  const text = key.replace(/[_:-]+/g, ' ').trim()
  return text.charAt(0).toUpperCase() + text.slice(1)
}

export function tacticInfo(key: string): TacticInfo {
  return TACTICS[key] ?? { label: humanize(key), description: 'A pressure tactic often used in scams' }
}

export const CATEGORY_LABELS: Record<string, string> = {
  gov_impersonation: 'Government impersonation',
  opt_employer_fraud: 'OPT employer fraud',
  fake_job_task: 'Fake job / task scam',
  other_scam: 'Other scam',
  legitimate: 'Legitimate',
}

export function categoryLabel(key: string): string {
  return CATEGORY_LABELS[key] ?? humanize(key)
}

export interface VerdictStyle {
  label: string
  /** Banner background + border */
  banner: string
  /** Strong text / icon color */
  accent: string
  /** Gauge stroke color (CSS color) */
  gauge: string
  /** Icon tile background */
  tile: string
}

export const VERDICT_STYLES: Record<Verdict, VerdictStyle> = {
  likely_scam: {
    label: 'Likely scam',
    banner: 'bg-red-50 border-red-200 dark:bg-red-950/40 dark:border-red-900/70',
    accent: 'text-red-700 dark:text-red-300',
    gauge: 'var(--color-red-600)',
    tile: 'bg-red-600 text-white dark:bg-red-500',
  },
  suspicious: {
    label: 'Suspicious',
    banner: 'bg-amber-50 border-amber-200 dark:bg-amber-950/40 dark:border-amber-900/70',
    accent: 'text-amber-800 dark:text-amber-300',
    gauge: 'var(--color-amber-500)',
    tile: 'bg-amber-500 text-white dark:bg-amber-500 dark:text-amber-950',
  },
  likely_safe: {
    label: 'Likely safe',
    banner: 'bg-emerald-50 border-emerald-200 dark:bg-emerald-950/40 dark:border-emerald-900/70',
    accent: 'text-emerald-700 dark:text-emerald-300',
    gauge: 'var(--color-emerald-600)',
    tile: 'bg-emerald-600 text-white dark:bg-emerald-500 dark:text-emerald-950',
  },
}

export function verdictStyle(verdict: string): VerdictStyle {
  return VERDICT_STYLES[verdict as Verdict] ?? VERDICT_STYLES.suspicious
}

export const MAX_IMAGE_BYTES = 10 * 1024 * 1024
export const MAX_AUDIO_BYTES = 20 * 1024 * 1024
export const MAX_TEXT_CHARS = 10_000
export const MIN_TEXT_CHARS = 10
