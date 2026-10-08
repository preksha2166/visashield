import { Check, ListChecks } from 'lucide-react'
import { useState } from 'react'

/** "What to do now" — numbered steps the user can tick off (local state only). */
export function ActionChecklist({ actions }: { actions: string[] }) {
  const [done, setDone] = useState<Set<number>>(() => new Set())

  if (!actions.length) return null

  const toggle = (i: number) =>
    setDone((prev) => {
      const next = new Set(prev)
      if (next.has(i)) next.delete(i)
      else next.add(i)
      return next
    })

  return (
    <section aria-labelledby="actions-title">
      <div className="flex items-baseline justify-between gap-3">
        <h3 id="actions-title" className="section-title">
          <ListChecks className="size-4.5 text-teal-700 dark:text-teal-400" aria-hidden />
          What to do now
        </h3>
        <span className="text-xs text-slate-500 tabular-nums dark:text-slate-400">
          {done.size}/{actions.length} done
        </span>
      </div>
      <ol className="mt-3 space-y-2">
        {actions.map((action, i) => {
          const checked = done.has(i)
          const id = `action-${i}`
          return (
            <li key={i}>
              <label
                htmlFor={id}
                className={`flex gap-3 rounded-xl border p-3 transition-colors has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-teal-600 ${
                  checked
                    ? 'border-teal-200 bg-teal-50/70 dark:border-teal-900/70 dark:bg-teal-950/30'
                    : 'border-slate-200 bg-white hover:border-slate-300 dark:border-slate-800 dark:bg-slate-900 dark:hover:border-slate-700'
                }`}
              >
                <input id={id} type="checkbox" checked={checked} onChange={() => toggle(i)} className="peer sr-only" />
                <span
                  aria-hidden
                  className={`flex size-6 shrink-0 items-center justify-center rounded-full border-2 text-xs font-bold ${
                    checked
                      ? 'border-teal-600 bg-teal-600 text-white dark:border-teal-400 dark:bg-teal-400 dark:text-slate-950'
                      : 'border-slate-300 text-slate-600 dark:border-slate-600 dark:text-slate-300'
                  }`}
                >
                  {checked ? <Check className="size-3.5" strokeWidth={3} /> : i + 1}
                </span>
                <span
                  className={`text-[15px] leading-snug ${
                    checked ? 'text-slate-500 line-through dark:text-slate-500' : 'text-slate-800 dark:text-slate-200'
                  }`}
                >
                  {action}
                </span>
              </label>
            </li>
          )
        })}
      </ol>
    </section>
  )
}
