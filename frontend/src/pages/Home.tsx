import { useEffect, useState } from 'react'
import { getHealth } from '../lib/api'

export default function Home() {
  const [apiStatus, setApiStatus] = useState<'checking' | 'ok' | 'unreachable'>('checking')

  useEffect(() => {
    getHealth()
      .then((data) => setApiStatus(data.status === 'ok' ? 'ok' : 'unreachable'))
      .catch(() => setApiStatus('unreachable'))
  }, [])

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col items-center justify-center gap-4 px-4 text-center">
      <h1 className="text-3xl font-semibold">AutoPilotAI</h1>
      <p className="text-gray-500">Resume + job description intelligence platform — Checkpoint 1 skeleton.</p>
      <p className="text-sm">
        Backend status:{' '}
        <span
          className={
            apiStatus === 'ok'
              ? 'text-green-600'
              : apiStatus === 'unreachable'
                ? 'text-red-600'
                : 'text-gray-400'
          }
        >
          {apiStatus}
        </span>
      </p>
    </main>
  )
}
