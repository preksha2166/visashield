export type Verdict = 'likely_scam' | 'suspicious' | 'likely_safe'

export type Situation = 'not_responded' | 'paid' | 'shared_info'

export type Category =
  | 'gov_impersonation'
  | 'opt_employer_fraud'
  | 'fake_job_task'
  | 'other_scam'
  | 'legitimate'

export type Tactic =
  | 'authority'
  | 'urgency'
  | 'fear_threat'
  | 'secrecy'
  | 'payment_demand'
  | 'pii_request'
  | 'advance_fee'
  | 'too_good'

export interface Reason {
  signal: string
  text: string
  weight: number
  source_url?: string | null
  source_title?: string | null
}

export interface Source {
  title: string
  url: string
  snippet?: string
}

export interface Entities {
  claimed_agency?: string | null
  phone_numbers: string[]
  urls: string[]
  emails: string[]
  payment_methods: string[]
  amounts: string[]
}

export interface AnalyzeResponse {
  verdict: Verdict
  /** 0..1 */
  risk_score: number
  /** One of {@link Category}; kept as string so unknown backend categories still render. */
  category: string
  category_label: string
  category_probs: Record<string, number>
  summary: string
  explanation: string
  reasons: Reason[]
  /** Usually {@link Tactic} values; unknown ones render with a generic label. */
  tactics: string[]
  entities: Entities
  actions: string[]
  report_text?: string | null
  sources: Source[]
  language: string
  llm_used: boolean
  redacted_text: string
  extracted_text?: string | null
  latency_ms: number
}

export interface AnalyzeTextRequest {
  text: string
  language: string
  situation: Situation
}

export interface AnalyzeImageRequest {
  file: File
  language: string
  situation: Situation
}

export interface HealthResponse {
  status: string
  llm_available: boolean
  classifier_loaded: boolean
}

export interface Example {
  title: string
  text: string
  label: string
}
