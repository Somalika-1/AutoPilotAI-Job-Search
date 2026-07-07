import { useState, type FormEvent } from 'react'
import CoverLetterView from '../components/CoverLetterView'
import ScoreMeter from '../components/ScoreMeter'
import SkillChip from '../components/SkillChip'
import { useAuth } from '../context/AuthContext'
import { createMatch, generateCoverLetter, uploadResume, type MatchOut, type ResumeOut } from '../lib/api'

export default function Dashboard() {
  const { token, user, logout } = useAuth()
  const [resume, setResume] = useState<ResumeOut | null>(null)
  const [jobDescription, setJobDescription] = useState('')
  const [match, setMatch] = useState<MatchOut | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [copied, setCopied] = useState(false)

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    const fileInput = event.currentTarget.elements.namedItem('file') as HTMLInputElement
    const file = fileInput.files?.[0]
    if (!file || !token) return

    setBusy(true)
    try {
      setResume(await uploadResume(token, file))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setBusy(false)
    }
  }

  async function handleMatch(event: FormEvent) {
    event.preventDefault()
    setError(null)
    if (!resume || !token) return

    setBusy(true)
    try {
      setMatch(await createMatch(token, resume.id, jobDescription))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Matching failed')
    } finally {
      setBusy(false)
    }
  }

  async function handleCoverLetter() {
    setError(null)
    if (!match || !token) return

    setBusy(true)
    try {
      setMatch(await generateCoverLetter(token, match.id))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Cover letter generation failed')
    } finally {
      setBusy(false)
    }
  }

  function handleCopy() {
    if (!match?.cover_letter) return
    navigator.clipboard.writeText(match.cover_letter)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const inputClasses =
    'rounded-lg border px-3 py-2 outline-none focus:ring-2 focus:ring-[var(--accent)]'
  const cardClasses = 'flex flex-col gap-4 rounded-xl border p-5 shadow-sm'
  const primaryButtonClasses =
    'w-fit rounded-lg bg-[var(--accent-button-bg)] px-4 py-2 font-medium text-[var(--accent-button-text)] transition-colors hover:bg-[var(--accent-button-bg-hover)] disabled:opacity-50'

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col gap-6 px-4 py-10">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">AutoPilotAI</h1>
        <div className="flex items-center gap-3 text-sm" style={{ color: 'var(--text-secondary)' }}>
          <span>{user?.email}</span>
          <button onClick={logout} className="underline">
            Log out
          </button>
        </div>
      </div>

      {error && (
        <p
          className="rounded-lg p-3 text-sm"
          style={{ backgroundColor: 'var(--status-critical-wash)', color: 'var(--status-critical)' }}
        >
          {error}
        </p>
      )}

      {!resume && (
        <form
          onSubmit={handleUpload}
          className={cardClasses}
          style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border)' }}
        >
          <h2 className="font-medium">1. Upload your resume</h2>
          <input type="file" name="file" accept=".pdf,.docx" required className="text-sm" />
          <button type="submit" disabled={busy} className={primaryButtonClasses}>
            {busy ? 'Uploading...' : 'Upload'}
          </button>
        </form>
      )}

      {resume && !match && (
        <form
          onSubmit={handleMatch}
          className={cardClasses}
          style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border)' }}
        >
          <h2 className="font-medium">2. Paste a job description</h2>
          <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
            Resume: {resume.original_filename}
          </p>
          <textarea
            required
            rows={8}
            value={jobDescription}
            onChange={(event) => setJobDescription(event.target.value)}
            placeholder="Paste the job description here..."
            className={inputClasses}
            style={{ borderColor: 'var(--border)' }}
          />
          <button type="submit" disabled={busy} className={primaryButtonClasses}>
            {busy ? 'Scoring...' : 'Get match score'}
          </button>
        </form>
      )}

      {match && (
        <div
          className={cardClasses}
          style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border)' }}
        >
          <h2 className="font-medium">3. Match results</h2>

          <ScoreMeter score={match.score} />

          <div className="flex flex-col gap-2">
            <h3 className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>
              Strengths
            </h3>
            <div className="flex flex-wrap gap-2">
              {match.strengths.map((strength) => (
                <SkillChip key={strength} label={strength} variant="good" />
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <h3 className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>
              Missing skills
            </h3>
            <div className="flex flex-wrap gap-2">
              {match.missing_skills.map((skill) => (
                <SkillChip key={skill} label={skill} variant="critical" />
              ))}
            </div>
          </div>

          {!match.cover_letter ? (
            <button onClick={handleCoverLetter} disabled={busy} className={primaryButtonClasses}>
              {busy ? 'Generating...' : 'Generate cover letter'}
            </button>
          ) : (
            <div className="flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>
                  Cover letter
                </h3>
                <button onClick={handleCopy} className="text-sm underline">
                  {copied ? 'Copied!' : 'Copy'}
                </button>
              </div>
              <div className="rounded-lg p-3" style={{ backgroundColor: 'var(--page-bg)' }}>
                <CoverLetterView text={match.cover_letter} />
              </div>
            </div>
          )}
        </div>
      )}
    </main>
  )
}
