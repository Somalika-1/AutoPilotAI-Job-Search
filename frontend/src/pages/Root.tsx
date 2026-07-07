import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Root() {
  const { token, loading } = useAuth()

  if (loading) {
    return <div className="p-8 text-center text-gray-500">Loading...</div>
  }

  return <Navigate to={token ? '/dashboard' : '/login'} replace />
}
