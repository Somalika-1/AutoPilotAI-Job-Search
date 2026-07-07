import { createBrowserRouter } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import Root from './pages/Root'
import Signup from './pages/Signup'

export const router = createBrowserRouter([
  { path: '/', element: <Root /> },
  { path: '/login', element: <Login /> },
  { path: '/signup', element: <Signup /> },
  {
    element: <ProtectedRoute />,
    children: [{ path: '/dashboard', element: <Dashboard /> }],
  },
])
