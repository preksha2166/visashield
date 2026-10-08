import { FileAudio, FileText, ImageUp, Languages, LoaderCircle, Mic, ShieldCheck, Sparkles, Square, X } from 'lucide-react'
import { useEffect, useId, useRef, useState, type DragEvent, type FormEvent } from 'react'
import { LANGUAGES, MAX_AUDIO_BYTES, MAX_IMAGE_BYTES, MAX_TEXT_CHARS, MIN_TEXT_CHARS, SITUATIONS } from '../constants'
import type { Example, Situation } from '../types'

export type InputMode = 'text' | 'image' | 'audio'

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

const AUDIO_EXT = /\.(mp3|m4a|wav|ogg|opus|webm|flac|mp4|mpeg|mpga|aac|amr|3gp)$/i
const MAX_RECORD_SECONDS = 180

function formatSeconds(total: number): string {
  const m = Math.floor(total / 60)
  const s = Math.floor(total % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
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
  const [audio, setAudio] = useState<File | null>(null)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const [recording, setRecording] = useState(false)
  const [recSeconds, setRecSeconds] = useState(0)
  const recorder = useRef<MediaRecorder | null>(null)
  const recTimer = useRef<number | null>(null)
  const audioInput = useRef<HTMLInputElement>(null)
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

  const audioObjectUrl = useRef<string | null>(null)
  function setAudioFile(f: File | null) {
    if (audioObjectUrl.current) URL.revokeObjectURL(audioObjectUrl.current)
    audioObjectUrl.current = f ? URL.createObjectURL(f) : null
    setAudioUrl(audioObjectUrl.current)
    setAudio(f)
  }

  function acceptAudio(f: File | undefined | null) {
    if (!f) return
    if (!f.type.startsWith('audio/') && !AUDIO_EXT.test(f.name)) {
      setFormError('Please choose an audio file (MP3, M4A, WAV, OGG or WEBM).')
      return
    }
    if (f.size > MAX_AUDIO_BYTES) {
      setFormError('That recording is larger than 20 MB. Try a shorter clip.')
      return
    }
    setFormError(null)
    setAudioFile(f)
  }

  function clearAudio() {
    setAudioFile(null)
    if (audioInput.current) audioInput.current.value = ''
  }

  function stopRecording() {
    if (recTimer.current) window.clearInterval(recTimer.current)
    recTimer.current = null
    if (recorder.current && recorder.current.state !== 'inactive') recorder.current.stop()
  }

  async function startRecording() {
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      setFormError("Your browser can't record audio here. Upload a recording instead.")
      return
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mr = new MediaRecorder(stream)
      const chunks: Blob[] = []
      mr.ondataavailable = (e) => {
        if (e.data.size) chunks.push(e.data)
      }
      mr.onstop = () => {
        stream.getTracks().forEach((t) => t.stop())
        setRecording(false)
        const type = mr.mimeType || 'audio/webm'
        const ext = type.includes('mp4') ? 'm4a' : type.includes('ogg') ? 'ogg' : 'webm'
        if (chunks.length) setAudioFile(new File(chunks, `recording.${ext}`, { type }))
      }
      recorder.current = mr
      setFormError(null)
      setRecSeconds(0)
      setRecording(true)
      mr.start()
      recTimer.current = window.setInterval(() => {
        setRecSeconds((sec) => {
          if (sec + 1 >= MAX_RECORD_SECONDS) stopRecording()
          return sec + 1
        })
      }, 1000)
    } catch {
      setFormError('Microphone access was blocked. Allow it in your browser, or upload a recording instead.')
    }
  }

  // Release the microphone if the user switches tabs or leaves mid-recording.
  useEffect(() => {
    if (mode !== 'audio') stopRecording()
  }, [mode])
  useEffect(() => () => stopRecording(), [])

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
    if (mode === 'audio' && (recording || !audio)) {
      setFormError(recording ? 'Stop the recording first.' : 'Upload or record the voicemail first.')
      return
    }
    setFormError(null)
    onSubmit({ mode, text: text.trim(), file: mode === 'audio' ? audio : file, language, situation })
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
        <button
          type="button"
          role="tab"
          id={`${ids}-tab-audio`}
          aria-selected={mode === 'audio'}
          aria-controls={`${ids}-panel-audio`}
          className={tabClass(mode === 'audio')}
          onClick={() => setMode('audio')}
        >
          <Mic className="size-4" aria-hidden />
          Voicemail
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

      {/* Audio panel */}
      <div
        role="tabpanel"
        id={`${ids}-panel-audio`}
        aria-labelledby={`${ids}-tab-audio`}
        hidden={mode !== 'audio'}
        className="mt-4"
      >
        <input
          ref={audioInput}
          id={`${ids}-audio`}
          type="file"
          accept="audio/*,.mp3,.m4a,.wav,.ogg,.opus,.webm,.amr,.3gp"
          className="sr-only"
          onChange={(e) => acceptAudio(e.target.files?.[0])}
        />
        {audio && audioUrl ? (
          <div className="rounded-xl border border-slate-300 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-950">
            <div className="flex items-center gap-3">
              <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-teal-100 text-teal-700 dark:bg-teal-900/60 dark:text-teal-300">
                <FileAudio className="size-5" aria-hidden />
              </span>
              <span className="min-w-0 flex-1 truncate text-sm font-medium text-slate-700 dark:text-slate-200">{audio.name}</span>
              <button
                type="button"
                onClick={() => audioInput.current?.click()}
                className="rounded-md px-2 py-1 text-sm font-medium text-teal-700 hover:bg-teal-50 dark:text-teal-300 dark:hover:bg-teal-950/50"
              >
                Replace
              </button>
              <button
                type="button"
                onClick={clearAudio}
                aria-label="Remove recording"
                className="rounded-md p-1 text-slate-500 hover:bg-slate-100 hover:text-slate-800 dark:hover:bg-slate-800 dark:hover:text-slate-200"
              >
                <X className="size-4" aria-hidden />
              </button>
            </div>
            <audio controls src={audioUrl} className="mt-3 w-full" />
          </div>
        ) : recording ? (
          <div className="flex min-h-48 flex-col items-center justify-center gap-3 rounded-xl border-2 border-red-300 bg-red-50 px-4 py-8 text-center dark:border-red-800 dark:bg-red-950/30">
            <span className="flex items-center gap-2 font-medium text-red-800 dark:text-red-200">
              <span className="size-2.5 animate-pulse rounded-full bg-red-600" aria-hidden />
              Recording… {formatSeconds(recSeconds)}
            </span>
            <span className="text-sm text-slate-600 dark:text-slate-400">Play the voicemail on speaker near your microphone.</span>
            <button
              type="button"
              onClick={stopRecording}
              className="inline-flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700"
            >
              <Square className="size-4" aria-hidden />
              Stop
            </button>
          </div>
        ) : (
          <div
            onDragOver={(e) => {
              e.preventDefault()
              setDragging(true)
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault()
              setDragging(false)
              acceptAudio(e.dataTransfer.files?.[0])
            }}
            className={`flex min-h-48 flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed px-4 py-8 text-center transition-colors ${
              dragging
                ? 'border-teal-600 bg-teal-50 dark:border-teal-400 dark:bg-teal-950/40'
                : 'border-slate-300 bg-slate-50 dark:border-slate-700 dark:bg-slate-950'
            }`}
          >
            <span className="flex size-12 items-center justify-center rounded-full bg-teal-100 text-teal-700 dark:bg-teal-900/60 dark:text-teal-300">
              <Mic className="size-6" aria-hidden />
            </span>
            <span className="font-medium text-slate-800 dark:text-slate-200">Check a voicemail or call recording</span>
            <div className="flex flex-wrap justify-center gap-2">
              <button
                type="button"
                onClick={() => audioInput.current?.click()}
                className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-800 hover:border-teal-600 hover:text-teal-800 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:border-teal-400"
              >
                <FileAudio className="size-4" aria-hidden />
                Upload recording
              </button>
              <button
                type="button"
                onClick={startRecording}
                className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-800 hover:border-red-500 hover:text-red-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:border-red-400"
              >
                <span className="size-2.5 rounded-full bg-red-600" aria-hidden />
                Record now
              </button>
            </div>
            <span className="text-sm text-slate-500 dark:text-slate-400">
              MP3, M4A, WAV, OGG or WEBM, up to 20 MB. We transcribe it, then check what the caller said.
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
