import { ShoppingBasket } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function Brand({ to = '/', light = false }) {
  return (
    <Link to={to} className="flex items-center gap-2 font-semibold">
      <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-700 text-white">
        <ShoppingBasket className="h-4.5 w-4.5" aria-hidden="true" />
      </span>
      <span className={light ? 'text-white' : 'text-slate-900'}>
        Grocery<span className={light ? 'text-brand-200' : 'text-brand-700'}>Smart</span>
      </span>
    </Link>
  )
}
