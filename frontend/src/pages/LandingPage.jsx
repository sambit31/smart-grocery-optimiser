import { ArrowRight, Boxes, ListChecks, Sparkles, Wallet } from 'lucide-react'
import { Link } from 'react-router-dom'
import Brand from '../components/common/Brand'
import Footer from '../components/layout/Footer'
import { useAuth } from '../context/AuthContext'

const FEATURES = [
  {
    icon: Sparkles,
    title: 'Smart prediction',
    text: 'Averages your household’s recent consumption to estimate what you will need for the next shopping period.',
  },
  {
    icon: Boxes,
    title: 'Inventory tracking',
    text: 'Keeps a running count of what is already in your kitchen, updated by every purchase and every use.',
  },
  {
    icon: Wallet,
    title: 'Budget optimisation',
    text: 'Over budget? Optional items are trimmed first, essentials are protected, and every change is explained.',
  },
  {
    icon: ListChecks,
    title: 'Shopping lists',
    text: 'A clean, mobile-friendly checklist with quantities, prices and the reason behind each recommendation.',
  },
]

const STEPS = [
  ['Set up your household', 'Family size, how often you shop, and your monthly grocery budget.'],
  ['Add items and stock', 'Build your catalogue with ₹ prices and record what is already at home.'],
  ['Log purchases and usage', 'Every entry improves the prediction — no guesswork, no invented data.'],
  ['Generate your plan', 'Predicted need − current stock = what to buy, fitted to your budget.'],
]

// Purely illustrative preview for the landing page (the real dashboard
// shows live figures from the database).
const PREVIEW_ROWS = [
  ['Basmati Rice', '5 kg', '₹475', 'Essential'],
  ['Toor Dal', '2 kg', '₹320', 'Essential'],
  ['Mustard Oil', '2 litre', '₹350', 'Essential'],
  ['Biscuits', '4 packet', '₹120', 'Optional'],
]

export default function LandingPage() {
  const { user } = useAuth()
  const startLink = user ? '/app' : '/register'

  return (
    <div className="min-h-screen bg-white">
      <header className="sticky top-0 z-30 border-b border-slate-100 bg-white/90 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <Brand />
          <nav aria-label="Primary" className="flex items-center gap-1 sm:gap-2">
            <a href="#features" className="btn btn-ghost hidden sm:inline-flex">Features</a>
            <a href="#how-it-works" className="btn btn-ghost hidden sm:inline-flex">How it works</a>
            {user ? (
              <Link to="/app" className="btn btn-primary">Open dashboard</Link>
            ) : (
              <>
                <Link to="/login" className="btn btn-ghost">Log in</Link>
                <Link to="/register" className="btn btn-primary">Get Started</Link>
              </>
            )}
          </nav>
        </div>
      </header>

      <main>
        <section className="mx-auto grid max-w-6xl items-center gap-12 px-4 py-16 sm:px-6 lg:grid-cols-2 lg:py-24">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-800 ring-1 ring-brand-200">
              <Sparkles className="h-3.5 w-3.5" /> Data-driven grocery planning
            </span>
            <h1 className="mt-5 text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
              Plan Smarter. Shop Better. Save More.
            </h1>
            <p className="mt-5 max-w-xl text-lg text-slate-600">
              GrocerySmart learns how much your household actually uses, subtracts what you already have, and
              builds a shopping list that fits your monthly budget — with essentials always first.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to={startLink} className="btn btn-primary px-5 py-2.5 text-base">
                Get Started <ArrowRight className="h-4 w-4" />
              </Link>
              <a href="#features" className="btn btn-secondary px-5 py-2.5 text-base">Explore Features</a>
            </div>
          </div>

          {/* Dashboard preview */}
          <div className="card overflow-hidden shadow-lg" aria-label="Illustrative preview of the app">
            <div className="flex items-center gap-1.5 border-b border-slate-100 bg-slate-50 px-4 py-3">
              <span className="h-2.5 w-2.5 rounded-full bg-red-300" />
              <span className="h-2.5 w-2.5 rounded-full bg-amber-300" />
              <span className="h-2.5 w-2.5 rounded-full bg-brand-500" />
              <span className="ml-3 text-xs text-slate-400">Preview · sample values</span>
            </div>
            <div className="grid grid-cols-3 gap-3 p-4">
              {[['Budget', '₹6,000'], ['Plan cost', '₹5,240'], ['Remaining', '₹760']].map(([label, value]) => (
                <div key={label} className="rounded-lg border border-slate-100 p-3">
                  <p className="text-[11px] text-slate-500">{label}</p>
                  <p className="text-base font-semibold text-slate-900">{value}</p>
                </div>
              ))}
            </div>
            <div className="px-4 pb-2">
              <div className="flex h-24 items-end gap-2">
                {[45, 62, 55, 70, 58, 66].map((h, i) => (
                  <div key={i} className="flex-1 rounded-t bg-brand-600/80" style={{ height: `${h}%` }} />
                ))}
              </div>
            </div>
            <table className="table">
              <tbody>
                {PREVIEW_ROWS.map(([name, qty, cost, priority]) => (
                  <tr key={name}>
                    <td className="font-medium text-slate-800">{name}</td>
                    <td className="text-slate-500">{qty}</td>
                    <td>{cost}</td>
                    <td>
                      <span className={`rounded-full px-2 py-0.5 text-xs ${priority === 'Essential' ? 'bg-red-50 text-red-700' : 'bg-slate-100 text-slate-600'}`}>
                        {priority}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section id="features" className="scroll-mt-20 border-t border-slate-100 bg-slate-50 py-16 lg:py-20">
          <div className="mx-auto max-w-6xl px-4 sm:px-6">
            <h2 className="text-2xl font-semibold text-slate-900 sm:text-3xl">Everything a household needs to plan groceries</h2>
            <p className="mt-2 max-w-2xl text-slate-600">Four connected modules that work from your real data.</p>
            <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
              {FEATURES.map(({ icon: Icon, title, text }) => (
                <div key={title} className="card p-5">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-50 text-brand-700">
                    <Icon className="h-5 w-5" aria-hidden="true" />
                  </div>
                  <h3 className="mt-4 font-semibold text-slate-900">{title}</h3>
                  <p className="mt-2 text-sm text-slate-600">{text}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="how-it-works" className="scroll-mt-20 py-16 lg:py-20">
          <div className="mx-auto max-w-6xl px-4 sm:px-6">
            <h2 className="text-2xl font-semibold text-slate-900 sm:text-3xl">How it works</h2>
            <ol className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
              {STEPS.map(([title, text], index) => (
                <li key={title} className="relative rounded-xl border border-slate-200 p-5">
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-700 text-sm font-semibold text-white">
                    {index + 1}
                  </span>
                  <h3 className="mt-4 font-semibold text-slate-900">{title}</h3>
                  <p className="mt-2 text-sm text-slate-600">{text}</p>
                </li>
              ))}
            </ol>
            <div className="mt-10 rounded-xl bg-brand-900 p-6 text-white sm:flex sm:items-center sm:justify-between">
              <p className="font-mono text-sm sm:text-base">recommended quantity = max(0, predicted requirement − current stock)</p>
              <Link to={startLink} className="btn mt-4 bg-white text-brand-900 hover:bg-brand-50 sm:mt-0">
                Start planning <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  )
}
