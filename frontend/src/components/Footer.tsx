import { Lock } from 'lucide-react'

export function Footer() {
  return (
    <footer className="mt-10 border-t border-slate-200 py-6 text-sm text-slate-600 dark:border-slate-800 dark:text-slate-400">
      <p className="flex gap-2">
        <Lock className="mt-0.5 size-4 shrink-0" aria-hidden />
        <span>
          VisaShield is a hackathon prototype and can be wrong. It never stores your messages. When in doubt, contact
          your school's international student office (DSO) using the number on your school's official website.
        </span>
      </p>
    </footer>
  )
}
