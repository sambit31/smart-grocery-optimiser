import { Loader2 } from 'lucide-react'

export default function LoadingSpinner({ label = 'Loading…', fullPage = false }) {
  return (
    <div
      role="status"
      className={`flex items-center justify-center gap-2 text-sm text-slate-500 ${fullPage ? 'min-h-screen' : 'py-16'}`}
    >
      <Loader2 className="h-5 w-5 animate-spin text-brand-700" aria-hidden="true" />
      <span>{label}</span>
    </div>
  )
}
