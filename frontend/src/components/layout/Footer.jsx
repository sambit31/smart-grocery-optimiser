import { Link } from 'react-router-dom'
import Brand from '../common/Brand'

export default function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-white">
      <div className="mx-auto flex max-w-6xl flex-col items-start gap-4 px-4 py-8 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <div>
          <Brand />
          <p className="mt-2 text-sm text-slate-500">Smart grocery planning for Indian households.</p>
        </div>
        <nav aria-label="Footer" className="flex flex-wrap gap-5 text-sm text-slate-600">
          <a href="#features" className="hover:text-brand-700">Features</a>
          <a href="#how-it-works" className="hover:text-brand-700">How it works</a>
          <Link to="/login" className="hover:text-brand-700">Log in</Link>
          <Link to="/register" className="hover:text-brand-700">Get started</Link>
        </nav>
        <p className="text-xs text-slate-400">© {new Date().getFullYear()} GrocerySmart · SAMBIT GHOSH</p>
      </div>
    </footer>
  )
}
