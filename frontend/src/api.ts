import { FALLBACK_EXAMPLES } from './examples'
import { pickMockResponse } from './mock'
import type {
  AnalyzeAudioRequest,
  AnalyzeImageRequest,
  AnalyzeResponse,
  AnalyzeTextRequest,
  Example,
  HealthResponse,
} from './types'

/**
 * Base URL of the backend. Empty string (the default) means same origin, which in
 * development is the Vite dev server that proxies /api to http://127.0.0.1:8000.
 */
const API_BASE = (import.meta.env.VITE_API_BASE ?? '').replace(/\/+$/, '')

const ANALYZE_TIMEOUT_MS = 90_000
const HEALTH_TIMEOUT_MS = 6_000

export class ApiError extends Error {
  status: number
  /** True when the request never reached the backend (network error, timeout). */
  offline: boolean

  constructor(message: string, status = 0, offline = false) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.offline = offline
  }
}

/** `?mock=1` in the URL serves canned responses so the UI can be demoed without a backend. */
export function isMockMode(): boolean {
  if (typeof window === 'undefined') return false
  const value = new URLSearchParams(window.location.search).get('mock')
  return value === '1' || value === 'true'
}

function url(path: string): string {
  return `${API_BASE}${path}`
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/** FastAPI errors are {"detail": string} or, for 422s, {"detail": [{msg, loc}, ...]}. */
function detailFromBody(body: unknown): string | null {
  if (!body || typeof body !== 'object' || !('detail' in body)) return null
  const detail = (body as { detail: unknown }).detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    const messages = detail
      .map((d) => (d && typeof d === 'object' && 'msg' in d ? String((d as { msg: unknown }).msg) : null))
      .filter((m): m is string => Boolean(m))
    if (messages.length) return messages.join('; ')
  }
  return null
}

async function request<T>(path: string, init: RequestInit, timeoutMs: number): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  let response: Response
  try {
    response = await fetch(url(path), { ...init, signal: controller.signal })
  } catch (err) {
    const timedOut = err instanceof DOMException && err.name === 'AbortError'
    throw new ApiError(
      timedOut
        ? 'The check took too long. The server may be busy — please try again.'
        : "We couldn't reach the VisaShield server. Check your connection and try again.",
      0,
      true,
    )
  } finally {
    clearTimeout(timer)
  }

  let body: unknown = null
  const text = await response.text()
  if (text) {
    try {
      body = JSON.parse(text)
    } catch {
      body = null
    }
  }

  if (!response.ok) {
    const detail = detailFromBody(body)
    // A dev proxy with no backend behind it answers 502/503/504 with no JSON body.
    const offline = !detail && response.status >= 502 && response.status <= 504
    throw new ApiError(
      detail ??
        (offline
          ? "The VisaShield server isn't responding right now."
          : `Something went wrong (HTTP ${response.status}). Please try again.`),
      response.status,
      offline,
    )
  }

  if (body === null) {
    throw new ApiError('The server sent an unexpected response. Please try again.', response.status)
  }
  return body as T
}

export async function getHealth(): Promise<HealthResponse> {
  if (isMockMode()) return { status: 'ok', llm_available: true, classifier_loaded: true }
  return request<HealthResponse>('/api/health', { method: 'GET' }, HEALTH_TIMEOUT_MS)
}

export async function getExamples(): Promise<Example[]> {
  if (isMockMode()) return FALLBACK_EXAMPLES
  try {
    const examples = await request<Example[]>('/api/examples', { method: 'GET' }, HEALTH_TIMEOUT_MS)
    const valid = Array.isArray(examples)
      ? examples.filter((e) => e && typeof e.title === 'string' && typeof e.text === 'string')
      : []
    return valid.length ? valid : FALLBACK_EXAMPLES
  } catch {
    return FALLBACK_EXAMPLES
  }
}

export async function analyzeText(req: AnalyzeTextRequest): Promise<AnalyzeResponse> {
  if (isMockMode()) {
    await delay(1200)
    return pickMockResponse(req.text, req.language, req.situation)
  }
  return request<AnalyzeResponse>(
    '/api/analyze',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    },
    ANALYZE_TIMEOUT_MS,
  )
}

export async function analyzeImage(req: AnalyzeImageRequest): Promise<AnalyzeResponse> {
  if (isMockMode()) {
    await delay(1600)
    const mock = pickMockResponse('', req.language, req.situation)
    return { ...mock, extracted_text: mock.redacted_text }
  }
  const form = new FormData()
  form.append('file', req.file)
  form.append('language', req.language)
  form.append('situation', req.situation)
  return request<AnalyzeResponse>('/api/analyze/image', { method: 'POST', body: form }, ANALYZE_TIMEOUT_MS)
}

export async function analyzeAudio(req: AnalyzeAudioRequest): Promise<AnalyzeResponse> {
  if (isMockMode()) {
    await delay(2000)
    const mock = pickMockResponse('', req.language, req.situation)
    return { ...mock, extracted_text: mock.redacted_text }
  }
  const form = new FormData()
  form.append('file', req.file)
  form.append('language', req.language)
  form.append('situation', req.situation)
  return request<AnalyzeResponse>('/api/analyze/audio', { method: 'POST', body: form }, ANALYZE_TIMEOUT_MS)
}
