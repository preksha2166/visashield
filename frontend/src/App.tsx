import { useCallback, useEffect, useRef, useState } from 'react'
import { analyzeImage, analyzeText, ApiError, getExamples, getHealth, isMockMode } from './api'
import { Footer } from './components/Footer'
import { Header, type BackendStatus } from './components/Header'
import { InputPanel, type AnalyzeInput } from './components/InputPanel'
import { ResultCard } from './components/ResultCard'
import { ErrorState, LoadingState, MockBanner, OfflineBanner } from './components/StatusMessages'
import { FALLBACK_EXAMPLES } from './examples'
import type { AnalyzeResponse, Example } from './types'

interface UiError {
  message: string
  offline: boolean
}

export default function App() {
  const mock = isMockMode()
  const [status, setStatus] = useState<BackendStatus>(mock ? 'mock' : 'checking')
  const [checkingHealth, setCheckingHealth] = useState(false)
  const [examples, setExamples] = useState<Example[]>(FALLBACK_EXAMPLES)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AnalyzeResponse | null>(null)
  const [resultId, setResultId] = useState(0)
  const [error, setError] = useState<UiError | null>(null)
  const lastInput = useRef<AnalyzeInput | null>(null)
  const resultRef = useRef<HTMLDivElement>(null)

  const refreshHealth = useCallback(async () => {
    if (mock) return
    try {
      const h = await getHealth()
      setStatus(h.status === 'ok' && h.classifier_loaded && h.llm_available ? 'online' : 'degraded')
    } catch {
      setStatus('offline')
    }
  }, [mock])

  const checkHealth = useCallback(async () => {
    setCheckingHealth(true)
    await refreshHealth()
    setCheckingHealth(false)
  }, [refreshHealth])

  useEffect(() => {
    void refreshHealth()
    let cancelled = false
    getExamples().then((ex) => {
      if (!cancelled) setExamples(ex)
    })
    return () => {
      cancelled = true
    }
  }, [refreshHealth])

  const scrollToResult = () =>
    requestAnimationFrame(() => resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }))

  const run = useCallback(
    async (input: AnalyzeInput) => {
      lastInput.current = input
      setLoading(true)
      setError(null)
      setResult(null)
      scrollToResult()
      try {
        const res =
          input.mode === 'image' && input.file
            ? await analyzeImage({ file: input.file, language: input.language, situation: input.situation })
            : await analyzeText({ text: input.text, language: input.language, situation: input.situation })
        setResult(res)
        setResultId((n) => n + 1)
        if (!mock && status === 'offline') void refreshHealth()
      } catch (err) {
        const apiErr = err instanceof ApiError ? err : null
        if (apiErr?.offline && !mock) setStatus('offline')
        setError({
          message: apiErr?.message ?? 'Something unexpected went wrong. Please try again.',
          offline: apiErr?.offline ?? false,
        })
      } finally {
        setLoading(false)
        scrollToResult()
      }
    },
    [mock, status, refreshHealth],
  )

  const retry = () => {
    if (lastInput.current) void run(lastInput.current)
  }

  const checkAnother = () => {
    setResult(null)
    setError(null)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <div className="mx-auto w-full max-w-3xl px-4 sm:px-6">
      <Header status={status} />

      <main>
        {mock && <MockBanner />}
        {status === 'offline' && <OfflineBanner onRetry={checkHealth} retrying={checkingHealth} />}

        <InputPanel examples={examples} loading={loading} onSubmit={run} />

        <div ref={resultRef} className="scroll-mt-4 pt-6" aria-live="polite" aria-busy={loading}>
          {loading && <LoadingState />}
          {!loading && error && <ErrorState message={error.message} offline={error.offline} onRetry={retry} />}
          {!loading && result && <ResultCard key={resultId} result={result} onCheckAnother={checkAnother} />}
        </div>
      </main>

      <Footer />
    </div>
  )
}
