interface SkillChipProps {
  label: string
  variant: 'good' | 'critical'
}

export default function SkillChip({ label, variant }: SkillChipProps) {
  const isGood = variant === 'good'
  const textColor = isGood ? 'var(--status-good-text)' : 'var(--status-critical)'
  const background = isGood ? 'var(--status-good-wash)' : 'var(--status-critical-wash)'

  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium"
      style={{ backgroundColor: background, color: textColor }}
    >
      {isGood ? (
        <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <path d="M3 8.5l3 3 7-7" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      ) : (
        <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <path d="M4 4l8 8M12 4l-8 8" strokeLinecap="round" />
        </svg>
      )}
      {label}
    </span>
  )
}
