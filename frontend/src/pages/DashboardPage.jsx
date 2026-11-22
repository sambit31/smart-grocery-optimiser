import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import {
  AlertTriangle,
  ArrowRight,
  Boxes,
  CircleDollarSign,
  ClipboardList,
  PiggyBank,
  Sparkles,
  Tags,
  Users,
  Wallet,
} from 'lucide-react'
import { getErrorMessage } from '../api/axios'
import { generatePlan } from '../api/predictionApi'
import { fetchDashboardSummary } from '../api/reportApi'
import { PriorityBadge } from '../components/common/Badge'
import EmptyState from '../components/common/EmptyState'
import ErrorState from '../components/common/ErrorState'
import LoadingSpinner from '../components/common/LoadingSpinner'
import PageHeader from '../components/common/PageHeader'
import StatCard from '../components/common/StatCard'
import AIShoppingAssistant from '../components/dashboard/AIShoppingAssistant'
import SpendingChart from '../components/charts/SpendingChart'
import AIInsights from '../components/dashboard/AIInsights'
import { useApi } from '../hooks/useApi'
import { formatCurrency } from '../utils/formatCurrency'
import { formatDate, formatQuantity } from '../utils/formatQuantity'


function Panel({ title, action, children }) {
  return (
    <section className="card">
      <div className="flex items-center justify-between border-b border-slate-100 px-5 py-3.5">
        <h2 className="text-sm font-semibold text-slate-900">{title}</h2>
        {action}
      </div>
      {children}
    </section>
  )
}

const SETUP_STEPS = [
  ['Add grocery items with prices', '/app/groceries'],
  ['Enter what you currently have in stock', '/app/inventory'],
  ['Record purchases and consumption', '/app/consumption'],
  ['Generate your first grocery plan', '/app/predictions'],
]

export default function DashboardPage() {
  const navigate = useNavigate()
  const { data, loading, error, reload } = useApi(fetchDashboardSummary)
  const [generating, setGenerating] = useState(false)

  const handleGenerate = async () => {
    setGenerating(true)
    try {
      await generatePlan()
      toast.success('New grocery plan generated.')
      navigate('/app/predictions')
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setGenerating(false)
    }
  }

  if (loading) return <LoadingSpinner />
  if (error) return <ErrorState message={error} onRetry={reload} />

  const hasSpending = data.monthly_spending.some((m) => m.total > 0)
  const isNewUser = data.item_count === 0

  return (
    <>
      <PageHeader
        title="Dashboard"
        description={`Overview for ${data.household.household_name}`}
        actions={
          <button type="button" className="btn btn-primary" onClick={handleGenerate} disabled={generating || isNewUser}>
            <Sparkles className="h-4 w-4" /> {generating ? 'Generating…' : 'Generate Grocery Plan'}
          </button>
        }
      />
      <div className="mb-6">
  <AIInsights />
</div>

<div className="mb-6">
  <AIShoppingAssistant />
</div>

      {isNewUser && (
        <section className="card mb-6 p-5">
          <h2 className="font-semibold text-slate-900">Get started in four steps</h2>
          <ol className="mt-3 grid gap-2 sm:grid-cols-2">
            {SETUP_STEPS.map(([label, to], index) => (
              <li key={to}>
                <Link to={to} className="flex items-center gap-3 rounded-lg border border-slate-200 px-3 py-2.5 text-sm hover:border-brand-300 hover:bg-brand-50">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-brand-100 text-xs font-semibold text-brand-800">{index + 1}</span>
                  {label}
                  <ArrowRight className="ml-auto h-4 w-4 text-slate-400" />
                </Link>
              </li>
            ))}
          </ol>
        </section>
      )}

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard icon={Users} label="Household size" value={`${data.household.family_size} members`} hint={`Shops ${data.household.shopping_frequency.toLowerCase()}`} tone="slate" />
        <StatCard icon={Wallet} label="Monthly budget" value={formatCurrency(data.monthly_budget)} />
        <StatCard icon={CircleDollarSign} label="Spent this month" value={formatCurrency(data.spent_this_month)} tone="blue" />
        <StatCard
          icon={PiggyBank}
          label="Remaining budget"
          value={formatCurrency(data.remaining_budget)}
          tone={data.remaining_budget < 0 ? 'red' : 'brand'}
          hint={data.remaining_budget < 0 ? 'Over budget this month' : 'Budget − spent this month'}
        />
        <StatCard icon={ClipboardList} label="Estimated plan cost" value={data.estimated_plan_cost === null ? '—' : formatCurrency(data.estimated_plan_cost)} hint={data.latest_plan ? 'Latest saved plan' : 'No plan yet'} tone="slate" />
        <StatCard icon={Tags} label="Grocery items" value={data.item_count} tone="slate" />
        <StatCard icon={AlertTriangle} label="Low-stock items" value={data.low_stock_count} tone={data.low_stock_count ? 'amber' : 'slate'} />
        <StatCard icon={Boxes} label="Plan status" value={data.latest_plan ? data.latest_plan.status : '—'} hint={data.latest_plan ? `${data.latest_plan.purchased_count}/${data.latest_plan.item_count} lines bought` : ''} tone="slate" />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Panel title="Monthly spending (last 6 months)" action={<Link to="/app/reports" className="text-xs font-medium text-brand-700 hover:underline">Reports</Link>}>
            <div className="p-4">
              {hasSpending ? (
                <SpendingChart data={data.monthly_spending} />
              ) : (
                <EmptyState compact title="No purchases yet" message="Record purchases to see monthly spending against your budget." />
              )}
            </div>
          </Panel>
        </div>

        <Panel title="Upcoming recommended purchases" action={<Link to="/app/shopping-list" className="text-xs font-medium text-brand-700 hover:underline">Shopping list</Link>}>
          {data.upcoming_purchases.length ? (
            <ul className="divide-y divide-slate-100">
              {data.upcoming_purchases.map((item) => (
                <li key={item.item_name} className="flex items-center justify-between gap-3 px-5 py-3 text-sm">
                  <div>
                    <p className="font-medium text-slate-800">{item.item_name}</p>
                    <p className="text-xs text-slate-500">{formatQuantity(item.quantity, item.unit)}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-medium">{formatCurrency(item.estimated_cost)}</p>
                    <PriorityBadge priority={item.priority} />
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState compact icon={Sparkles} title="Nothing pending" message="Generate a grocery plan to see what to buy next." />
          )}
        </Panel>

        <Panel title="Recent purchases" action={<Link to="/app/purchases" className="text-xs font-medium text-brand-700 hover:underline">View all</Link>}>
          {data.recent_purchases.length ? (
            <ul className="divide-y divide-slate-100">
              {data.recent_purchases.map((p) => (
                <li key={p.id} className="flex items-center justify-between px-5 py-3 text-sm">
                  <div>
                    <p className="font-medium text-slate-800">{p.item_name}</p>
                    <p className="text-xs text-slate-500">{formatQuantity(p.quantity, p.unit)} · {formatDate(p.purchase_date)}</p>
                  </div>
                  <span className="font-medium">{formatCurrency(p.total_price)}</span>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState compact title="No purchases recorded" />
          )}
        </Panel>

        <Panel title="Consumption overview (last 30 days)" action={<Link to="/app/consumption" className="text-xs font-medium text-brand-700 hover:underline">Details</Link>}>
          {data.consumption_overview.length ? (
            <ul className="divide-y divide-slate-100">
              {data.consumption_overview.map((c) => (
                <li key={c.item_id} className="flex items-center justify-between px-5 py-2.5 text-sm">
                  <span className="text-slate-700">{c.item_name}</span>
                  <span className="font-medium text-slate-900">{formatQuantity(c.quantity, c.unit)}</span>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState compact title="No consumption recorded" message="Consumption history powers the prediction." />
          )}
        </Panel>

        <Panel title="Low-stock items" action={<Link to="/app/inventory" className="text-xs font-medium text-brand-700 hover:underline">Inventory</Link>}>
          {data.low_stock_items.length ? (
            <ul className="divide-y divide-slate-100">
              {data.low_stock_items.map((r) => (
                <li key={r.id} className="flex items-center justify-between px-5 py-2.5 text-sm">
                  <span className="text-slate-700">{r.item_name}</span>
                  <span className="font-medium text-amber-700">{formatQuantity(r.quantity, r.unit)}</span>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState compact icon={Boxes} title="Stock levels look fine" />
          )}
        </Panel>
      </div>
    </>
  )
}
