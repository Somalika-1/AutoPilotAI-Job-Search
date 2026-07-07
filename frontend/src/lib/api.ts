const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

export interface UserOut {
  id: number
  email: string
  created_at: string
}

export interface Token {
  access_token: string
  token_type: string
}

export interface ResumeOut {
  id: number
  original_filename: string
  extracted_text: string
  uploaded_at: string
}

export interface MatchOut {
  id: number
  resume_id: number
  job_description_id: number
  score: number
  missing_skills: string[]
  strengths: string[]
  cover_letter: string | null
  created_at: string
}

async function request<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const headers = new Headers(options.headers)
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers })

  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new ApiError(response.status, body.detail ?? `Request failed with status ${response.status}`)
  }

  return response.json()
}

export function getHealth(): Promise<{ status: string }> {
  return request('/health')
}

export function signup(email: string, password: string): Promise<UserOut> {
  return request('/auth/signup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
}

export function login(email: string, password: string): Promise<Token> {
  return request('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
}

export function getMe(token: string): Promise<UserOut> {
  return request('/auth/me', {}, token)
}

export function uploadResume(token: string, file: File): Promise<ResumeOut> {
  const formData = new FormData()
  formData.append('file', file)
  return request('/resumes/upload', { method: 'POST', body: formData }, token)
}

export function createMatch(token: string, resumeId: number, jobDescriptionText: string): Promise<MatchOut> {
  return request(
    '/matches',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resume_id: resumeId, job_description_text: jobDescriptionText }),
    },
    token,
  )
}

export function generateCoverLetter(token: string, matchId: number): Promise<MatchOut> {
  return request(`/matches/${matchId}/cover-letter`, { method: 'POST' }, token)
}
