import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Signup() {
  const { signup } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await signup(email, password)
      navigate('/dashboard')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Signup failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-sm flex-col justify-center gap-4 px-4">
      <h1 className="text-2xl font-semibold">Sign up</h1>
      <form
        onSubmit={handleSubmit}
        className="flex flex-col gap-3 rounded-xl border p-5 shadow-sm"
        style={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border)' }}
      >
        <input
          type="email"
          required
          placeholder="Email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          className="rounded-lg border px-3 py-2 outline-none focus:ring-2 focus:ring-[var(--accent)]"
          style={{ borderColor: 'var(--border)' }}
        />
        <input
          type="password"
          required
          minLength={8}
          placeholder="Password (min 8 characters)"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          className="rounded-lg border px-3 py-2 outline-none focus:ring-2 focus:ring-[var(--accent)]"
          style={{ borderColor: 'var(--border)' }}
        />
        {error && (
          <p
            className="rounded-lg p-2 text-sm"
            style={{ backgroundColor: 'var(--status-critical-wash)', color: 'var(--status-critical)' }}
          >
            {error}
          </p>
        )}
        <button
          type="submit"
          disabled={submitting}
          className="rounded-lg bg-[var(--accent-button-bg)] px-4 py-2 font-medium text-[var(--accent-button-text)] transition-colors hover:bg-[var(--accent-button-bg-hover)] disabled:opacity-50"
        >
          {submitting ? 'Signing up...' : 'Sign up'}
        </button>
      </form>
      <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
        Already have an account?{' '}
        <Link to="/login" className="underline">
          Log in
        </Link>
      </p>
    </main>
  )
}
