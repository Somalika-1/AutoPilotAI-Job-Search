interface CoverLetterViewProps {
  text: string
}

export default function CoverLetterView({ text }: CoverLetterViewProps) {
  const lines = text
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)

  return (
    <div className="flex flex-col gap-2 text-sm">
      {lines.map((line, index) =>
        line.startsWith('- ') ? (
          <div key={index} className="flex gap-2 pl-1">
            <span style={{ color: 'var(--status-good)' }} aria-hidden="true">
              •
            </span>
            <span>{line.slice(2)}</span>
          </div>
        ) : (
          <p key={index}>{line}</p>
        ),
      )}
    </div>
  )
}
