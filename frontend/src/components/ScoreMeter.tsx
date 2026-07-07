interface ScoreMeterProps {
  score: number
}

interface ScoreBand {
  fill: string
  textColor: string
  label: string
}

function getScoreBand(score: number): ScoreBand {
  if (score >= 75) {
    return { fill: 'var(--status-good)', textColor: 'var(--status-good-text)', label: 'Strong match' }
  }
  if (score >= 50) {
    return { fill: 'var(--status-warning)', textColor: 'var(--status-warning-text)', label: 'Partial match' }
  }
  return { fill: 'var(--status-critical)', textColor: 'var(--status-critical)', label: 'Weak match' }
}

export default function ScoreMeter({ score }: ScoreMeterProps) {
  const band = getScoreBand(score)

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-baseline gap-3">
        <span className="text-5xl font-semibold" style={{ color: band.textColor }}>
          {score}
        </span>
        <span className="text-sm font-medium" style={{ color: band.textColor }}>
          {band.label}
        </span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full" style={{ backgroundColor: 'var(--gridline)' }}>
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${score}%`, backgroundColor: band.fill }}
        />
      </div>
    </div>
  )
}
