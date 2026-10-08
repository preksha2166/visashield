import { Info, Radar } from 'lucide-react'
import { useState } from 'react'
import { tacticInfo } from '../constants'

/**
 * Tactic chips. Hover, focus, or tap a chip to see what the tactic means. The description
 * is shown in a panel under the chips (instead of a floating tooltip) so it never overflows
 * small screens and works with touch.
 */
export function TacticChips({ tactics }: { tactics: string[] }) {
  const unique = Array.from(new Set(tactics))
  const [active, setActive] = useState<string | null>(null)
  const [pinned, setPinned] = useState<string | null>(null)
  const shown = active ?? pinned

  if (!unique.length) return null

  return (
    <section aria-labelledby="tactics-title">
      <h3 id="tactics-title" className="section-title">
        <Radar className="size-4.5 text-amber-600 dark:text-amber-400" aria-hidden />
        Pressure tactics used
      </h3>
      <ul className="mt-3 flex flex-wrap gap-2" onMouseLeave={() => setActive(null)}>
        {unique.map((t) => {
          const info = tacticInfo(t)
          const selected = shown === t
          return (
            <li key={t}>
              <button
                type="button"
                title={info.description}
                aria-describedby={selected ? 'tactic-description' : undefined}
                aria-pressed={pinned === t}
                onMouseEnter={() => setActive(t)}
                onFocus={() => setActive(t)}
                onBlur={() => setActive(null)}
                onClick={() => setPinned((p) => (p === t ? null : t))}
                className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm font-medium transition-colors ${
                  selected
                    ? 'border-amber-500 bg-amber-100 text-amber-900 dark:border-amber-400 dark:bg-amber-900/50 dark:text-amber-100'
                    : 'border-amber-200 bg-amber-50 text-amber-900 hover:border-amber-400 dark:border-amber-900/70 dark:bg-amber-950/40 dark:text-amber-200'
                }`}
              >
                {info.label}
                <Info className="size-3.5 opacity-60" aria-hidden />
              </button>
            </li>
          )
        })}
      </ul>
      <p
        id="tactic-description"
        aria-live="polite"
        className="mt-2 min-h-5 text-sm text-slate-600 dark:text-slate-400"
      >
        {shown ? (
          <>
            <span className="font-semibold text-slate-800 dark:text-slate-200">{tacticInfo(shown).label}:</span>{' '}
            {tacticInfo(shown).description}.
          </>
        ) : (
          <span className="text-slate-500 dark:text-slate-500">Tap a tactic to see what it means.</span>
        )}
      </p>
    </section>
  )
}
