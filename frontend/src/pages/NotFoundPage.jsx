import { Link } from 'react-router-dom'
import Brand from '../components/common/Brand'

export default function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 px-4 text-center">
      <Brand />
      <p className="mt-6 text-5xl font-bold text-brand-700">404</p>
      <h1 className="text-xl font-semibold text-slate-900">Page not found</h1>
      <p className="max-w-sm text-sm text-slate-500">The page you are looking for does not exist or has moved.</p>
      <div className="flex gap-2">
        <Link to="/" className="btn btn-secondary">Home</Link>
        <Link to="/app" className="btn btn-primary">Dashboard</Link>
      </div>
    </div>
  )
}
