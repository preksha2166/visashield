import { FileText, ImageUp, Languages, LoaderCircle, ShieldCheck, Sparkles, X } from 'lucide-react'
import { useEffect, useId, useRef, useState, type DragEvent, type FormEvent } from 'react'
import { LANGUAGES, MAX_IMAGE_BYTES, MAX_TEXT_CHARS, MIN_TEXT_CHARS, SITUATIONS } from '../constants'
import type { Example, Situation } from '../types'

export type InputMode = 'text' | 'image'

export interface AnalyzeInput {
  mode: InputMode
  text: string
  file: File | null
  language: string
  situation: Situation
}

interface Props {
  examples: Example[]
  loading: boolean
  onSubmit: (input: AnalyzeInput) => void
}

const PLACEHOLDER = `Paste the suspicious message here, for example:
• a text or WhatsApp message
• an email (include the sender address if you can)
• what a caller said to you, or a voicemail transcript
• a job post or offer letter`

export function InputPanel({ examples, loading, onSubmit }: Props) {
  const [mode, setMode] = useState<InputMode>('text')
  const [text, setText] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [dragging, setDragging] = useState(false)
  const [situation, setSituation] = useState<Situation>('not_responded')
  const [language, setLanguage] = useState('en')
  const [formError, setFormError] = useState<string | null>(null)
  const fileInput = useRef<HTMLInputElement>(null)
  const textarea = useRef<HTMLTextAreaElement>(null)
  const ids = useId()

  // Object URL for the image preview; the previous one is released whenever it changes.
  const previewUrl = useRef<string | null>(null)
  function setImage(f: File | null) {
    if (previewUrl.current) URL.revokeObjectURL(previewUrl.current)
    previewUrl.current = f ? URL.createObjectURL(f) : null
    setPreview(previewUrl.current)
    setFile(f)
  }

  // Allow pasting a screenshot straight from the clipboard while on the image tab.
  useEffect(() => {
    if (mode !== 'image') return
    const onPaste = (e: ClipboardEvent) => {
      const item = Array.from(e.clipboardData?.files ?? []).find((f) => f.type.startsWith('image/'))
      if (item) {
        e.preventDefault()
        acceptFile(item)
      }
    }
    window.addEventListener('paste', onPaste)
    return () => window.removeEventListener('paste', onPaste)
    // acceptFile only uses state setters and refs, so a stale copy is safe.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode])

  function acceptFile(f: File | undefined | null) {
    if (!f) return
    if (!f.type.startsWith('image/')) {
      setFormError('Please choose an image file (PNG, JPG, or similar).')
      return
    }
    if (f.size > MAX_IMAGE_BYTES) {
      setFormError('That image is larger than 10 MB. Try a smaller screenshot.')
      return
    }
    setFormError(null)
    setImage(f)
  }

  function clearFile() {
    setImage(null)
    if (fileInput.current) fileInput.current.value = ''
  }

  function onDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setDragging(false)
    acceptFile(e.dataTransfer.files?.[0])
  }

  function applyExample(example: Example) {
    setMode('text')
    setText(example.text)
    setFormError(null)
    requestAnimationFrame(() => {
      const el = textarea.current
      if (!el) return
      el.focus({ preventScroll: true })
      el.setSelectionRange(0, 0)
      el.scrollTop = 0
    })
  }

  function submit(e: FormEvent) {
    e.preventDefault()
    if (loading) return
    if (mode === 'text' && text.trim().length < MIN_TEXT_CHARS) {
      setFormError('Paste the message you received first — a sentence or two is enough.')
      textarea.current?.focus()
      return
    }
    if (mode === 'image' && !file) {
      setFormError('Choose a screenshot to check first.')
      return
    }
    setFormError(null)
    onSubmit({ mode, text: text.trim(), file, language, situation })
  }

  const tabClass = (active: boolean) =>
    `flex flex-1 items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
      active
        ? 'bg-white text-slate-900 shadow-sm dark:bg-slate-700 dark:text-white'
        : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200'
    }`

  return (
    <form onSubmit={submit} className="card p-4 sm:p-6" aria-label="Check a message" noValidate>
      {/* Tabs */}
      <div role="tablist" aria-label="Input type" className="flex gap-1 rounded-xl bg-slate-100 p-1 dark:bg-slate-800">
        <button
          type="button"
          role="tab"
          id={`${ids}-tab-text`}
          aria-selected={mode === 'text'}
          aria-controls={`${ids}-panel-text`}
          className={tabClass(mode === 'text')}
          onClick={() => setMode('text')}
        >
          <FileText className="size-4" aria-hidden />
          Paste text
        </button>
        <button
          type="button"
          role="tab"
          id={`${ids}-tab-image`}
          aria-selected={mode === 'image'}
          aria-controls={`${ids}-panel-image`}
          className={tabClass(mode === 'image')}
          onClick={() => setMode('image')}
        >
          <ImageUp className="size-4" aria-hidden />
          <span className="sm:hidden">Screenshot</span>
          <span className="hidden sm:inline">Upload screenshot</span>
        </button>
      </div>

      {/* Text panel */}
      <div
        role="tabpanel"
        id={`${ids}-panel-text`}
        aria-labelledby={`${ids}-tab-text`}
        hidden={mode !== 'text'}
        className="mt-4"
      >
        <label htmlFor={`${ids}-text`} className="sr-only">
          Message to check
        </label>
        <textarea
          id={`${ids}-text`}
          ref={textarea}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={PLACEHOLDER}
          maxLength={MAX_TEXT_CHARS}
          rows={9}
          className="block min-h-48 w-full resize-y rounded-xl border border-slate-300 bg-white px-4 py-3 text-[15px] leading-relaxed text-slate-900 placeholder:text-slate-400 focus:border-teal-600 focus:ring-2 focus:ring-teal-600/20 focus:outline-none dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:placeholder:text-slate-500 dark:focus:border-teal-400"
        />
        <div className="mt-1.5 flex items-center justify-between gap-3 text-xs text-slate-500 dark:text-slate-400">
          <span className="flex items-center gap-1">
            <ShieldCheck className="size-3.5 shrink-0" aria-hidden />
            SSNs, passport and SEVIS numbers are redacted before analysis.
          </span>
          {text.length > 0 && (
            <span className="shrink-0 tabular-nums">
              {text.length.toLocaleString()}/{MAX_TEXT_CHARS.toLocaleString()}
            </span>
          )}
        </div>

        {examples.length > 0 && (
          <div className="mt-4">
            <p className="mb-2 flex items-center gap-1.5 text-xs font-medium tracking-wide text-slate-500 uppercase dark:text-slate-400">
              <Sparkles className="size-3.5" aria-hidden />
              Try an example
            </p>
            <div className="flex flex-wrap gap-2">
              {examples.map((ex) => (
                <button
                  key={ex.title}
                  type="button"
                  onClick={() => applyExample(ex)}
                  className="rounded-full border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700 transition-colors hover:border-teal-600 hover:bg-teal-50 hover:text-teal-800 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:border-teal-400 dark:hover:bg-teal-950/50 dark:hover:text-teal-200"
                >
                  {ex.title}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Image panel */}
      <div
        role="tabpanel"
        id={`${ids}-panel-image`}
        aria-labelledby={`${ids}-tab-image`}
        hidden={mode !== 'image'}
        className="mt-4"
      >
        <input
          ref={fileInput}
          id={`${ids}-file`}
          type="file"
          accept="image/*"
          className="sr-only"
          onChange={(e) => acceptFile(e.target.files?.[0])}
        />
        {file && preview ? (
          <div className="relative overflow-hidden rounded-xl border border-slate-300 bg-slate-100 dark:border-slate-700 dark:bg-slate-950">
            <img src={preview} alt="Screenshot to check" className="mx-auto max-h-80 w-auto object-contain" />
            <div className="flex items-center justify-between gap-3 border-t border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-800 dark:bg-slate-900">
              <span className="min-w-0 truncate text-slate-600 dark:text-slate-300">{file.name}</span>
              <div className="flex shrink-0 gap-1">
                <button
                  type="button"
                  onClick={() => fileInput.current?.click()}
                  className="rounded-md px-2 py-1 font-medium text-teal-700 hover:bg-teal-50 dark:text-teal-300 dark:hover:bg-teal-950/50"
                >
                  Replace
                </button>
                <button
                  type="button"
                  onClick={clearFile}
                  aria-label="Remove screenshot"
                  className="rounded-md p-1 text-slate-500 hover:bg-slate-100 hover:text-slate-800 dark:hover:bg-slate-800 dark:hover:text-slate-200"
                >
                  <X className="size-4" aria-hidden />
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div
            role="button"
            tabIndex={0}
            onClick={() => fileInput.current?.click()}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault()
                fileInput.current?.click()
              }
            }}
            onDragOver={(e) => {
              e.preventDefault()
              setDragging(true)
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            className={`flex min-h-48 flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed px-4 py-8 text-center transition-colors ${
              dragging
                ? 'border-teal-600 bg-teal-50 dark:border-teal-400 dark:bg-teal-950/40'
                : 'border-slate-300 bg-slate-50 hover:border-teal-600 hover:bg-teal-50/50 dark:border-slate-700 dark:bg-slate-950 dark:hover:border-teal-400 dark:hover:bg-teal-950/30'
            }`}
          >
            <span className="flex size-12 items-center justify-center rounded-full bg-teal-100 text-teal-700 dark:bg-teal-900/60 dark:text-teal-300">
              <ImageUp className="size-6" aria-hidden />
            </span>
            <span className="font-medium text-slate-800 dark:text-slate-200">
              Tap to choose a screenshot
              <span className="hidden sm:inline"> or drag it here</span>
            </span>
            <span className="text-sm text-slate-500 dark:text-slate-400">
              Texts, WhatsApp chats, emails, job posts · PNG or JPG, up to 10 MB
              <span className="hidden sm:inline"> · You can also paste with Ctrl/⌘+V</span>
            </span>
          </div>
        )}
      </div>

      {/* Situation */}
      <fieldset className="mt-6">
        <legend className="text-sm font-semibold text-slate-900 dark:text-slate-100">What happened so far?</legend>
        <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">We'll tailor the next steps to your situation.</p>
        <div className="mt-2 grid grid-cols-1 gap-1 rounded-xl bg-slate-100 p-1 sm:grid-cols-3 dark:bg-slate-800">
          {SITUATIONS.map((s) => {
            const active = situation === s.value
            return (
              <label
                key={s.value}
                className={`relative flex items-center justify-center rounded-lg px-3 py-2 text-center text-sm font-medium transition-colors has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-teal-600 ${
                  active
                    ? 'bg-white text-slate-900 shadow-sm dark:bg-slate-700 dark:text-white'
                    : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200'
                }`}
              >
                <input
                  type="radio"
                  name={`${ids}-situation`}
                  value={s.value}
                  checked={active}
                  onChange={() => setSituation(s.value)}
                  className="sr-only"
                />
                {s.label}
              </label>
            )
          })}
        </div>
      </fieldset>

      {/* Language + submit */}
      <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="sm:w-56">
          <label
            htmlFor={`${ids}-lang`}
            className="mb-1.5 flex items-center gap-1.5 text-sm font-semibold text-slate-900 dark:text-slate-100"
          >
            <Languages className="size-4" aria-hidden />
            Answer in
          </label>
          <select
            id={`${ids}-lang`}
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="block w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 focus:border-teal-600 focus:ring-2 focus:ring-teal-600/20 focus:outline-none dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
          >
            {LANGUAGES.map((l) => (
              <option key={l.code} value={l.code}>
                {l.label}
              </option>
            ))}
          </select>
        </div>
        <button
          type="submit"
          disabled={loading}
          aria-busy={loading}
          className="inline-flex flex-1 items-center justify-center gap-2 rounded-xl bg-teal-700 px-5 py-3 text-base font-semibold text-white shadow-sm transition-colors hover:bg-teal-800 disabled:cursor-wait disabled:opacity-80 dark:bg-teal-500 dark:text-slate-950 dark:hover:bg-teal-400"
        >
          {loading ? (
            <>
              <LoaderCircle className="size-5 animate-spin" aria-hidden />
              Checking signals…
            </>
          ) : (
            <>
              <ShieldCheck className="size-5" aria-hidden />
              Check this message
            </>
          )}
        </button>
      </div>

      {formError && (
        <p role="alert" className="mt-3 text-sm font-medium text-red-700 dark:text-red-300">
          {formError}
        </p>
      )}
    </form>
  )
}
