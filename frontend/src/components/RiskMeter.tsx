interface Props {
  /** 0..1 */
  score: number
  /** CSS color for the filled arc */
  color: string
  className?: string
}

const ARC = 'M 12 62 A 50 50 0 0 1 112 62'

/** Semicircle gauge showing the risk score as a percentage. */
export function RiskMeter({ score, color, className = '' }: Props) {
  const clamped = Number.isFinite(score) ? Math.min(1, Math.max(0, score)) : 0
  const pct = Math.round(clamped * 100)

  return (
    <div
      role="meter"
      aria-label="Risk score"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={pct}
      aria-valuetext={`${pct}% risk`}
      className={`w-32 shrink-0 sm:w-36 ${className}`}
    >
      <svg viewBox="0 0 124 70" className="block w-full overflow-visible" aria-hidden>
        <path
          d={ARC}
          pathLength={100}
          fill="none"
          strokeWidth={11}
          strokeLinecap="round"
          className="stroke-slate-900/10 dark:stroke-white/10"
        />
        <path
          d={ARC}
          pathLength={100}
          fill="none"
          stroke={color}
          strokeWidth={11}
          strokeLinecap="round"
          strokeDasharray={`${Math.max(pct, 0.5)} 100`}
          style={{ transition: 'stroke-dasharray 700ms ease-out' }}
        />
        {/* Band thresholds: 40% suspicious, 70% likely scam */}
        {[0.4, 0.7].map((t) => {
          const angle = Math.PI * (1 - t)
          const x1 = 62 + Math.cos(angle) * 41
          const y1 = 62 - Math.sin(angle) * 41
          const x2 = 62 + Math.cos(angle) * 36
          const y2 = 62 - Math.sin(angle) * 36
          return (
            <line
              key={t}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              strokeWidth={1.5}
              strokeLinecap="round"
              className="stroke-slate-900/25 dark:stroke-white/25"
            />
          )
        })}
        <text
          x={62}
          y={59}
          textAnchor="middle"
          className="fill-slate-900 font-sans text-[28px] font-bold tabular-nums dark:fill-white"
        >
          {pct}
          <tspan className="fill-slate-500 text-[14px] font-semibold dark:fill-slate-400">%</tspan>
        </text>
      </svg>
      <div className="mt-1 text-center text-[11px] leading-none font-semibold tracking-wider text-slate-500 uppercase dark:text-slate-400">
        Risk score
      </div>
    </div>
  )
}
