import { Building2, CreditCard, DollarSign, Link, Mail, Phone, ScanSearch, type LucideIcon } from 'lucide-react'
import type { Entities } from '../types'

interface Row {
  label: string
  icon: LucideIcon
  values: string[]
  mono?: boolean
}

/**
 * Extracted contact details. URLs and emails are deliberately rendered as plain text,
 * never as links — they may be malicious.
 */
export function EntitiesTable({ entities }: { entities: Entities }) {
  const rows: Row[] = [
    { label: 'Claims to be', icon: Building2, values: entities.claimed_agency ? [entities.claimed_agency] : [] },
    { label: 'Phone numbers', icon: Phone, values: entities.phone_numbers ?? [], mono: true },
    { label: 'Links', icon: Link, values: (entities.urls ?? []).map(defang), mono: true },
    { label: 'Emails', icon: Mail, values: entities.emails ?? [], mono: true },
    { label: 'Payment methods', icon: CreditCard, values: entities.payment_methods ?? [] },
    { label: 'Amounts', icon: DollarSign, values: entities.amounts ?? [] },
  ].filter((r) => r.values.length > 0)

  if (!rows.length) return null
  const hasLinks = (entities.urls ?? []).length > 0

  return (
    <section aria-labelledby="entities-title">
      <h3 id="entities-title" className="section-title">
        <ScanSearch className="size-4.5 text-slate-600 dark:text-slate-400" aria-hidden />
        Details we pulled out
      </h3>
      <div className="mt-3 overflow-hidden rounded-xl border border-slate-200 dark:border-slate-800">
        <table className="w-full table-fixed text-sm">
          <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
            {rows.map(({ label, icon: Icon, values, mono }) => (
              <tr key={label} className="align-top">
                <th
                  scope="row"
                  className="w-[38%] bg-slate-50 px-3 py-2.5 text-left font-medium text-slate-600 sm:w-44 dark:bg-slate-950/50 dark:text-slate-400"
                >
                  <span className="flex items-center gap-1.5">
                    <Icon className="size-3.5 shrink-0" aria-hidden />
                    {label}
                  </span>
                </th>
                <td className="px-3 py-2.5 text-slate-800 dark:text-slate-200">
                  <ul className="space-y-1">
                    {values.map((v, i) => (
                      <li key={`${v}-${i}`} className={mono ? 'font-mono text-[13px] break-all' : 'break-words'}>
                        {v}
                      </li>
                    ))}
                  </ul>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {hasLinks && (
        <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
          Links are shown as plain text with <span className="font-mono">[.]</span> so they can't be opened by
          accident. Don't visit them.
        </p>
      )}
    </section>
  )
}

/** "Defang" a URL (http -> hxxp, . -> [.]) so it can't be auto-linked by the browser or OS. */
function defang(url: string): string {
  return url.replace(/^http/i, 'hxxp').replace(/\./g, '[.]')
}
