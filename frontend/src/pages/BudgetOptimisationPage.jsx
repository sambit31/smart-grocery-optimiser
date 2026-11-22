import { useState } from 'react'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { AlertTriangle, ArrowRight, Scale, Sparkles, Wallet } from 'lucide-react'
import { getErrorMessage } from '../api/axios'
import { optimisePlanBudget } from '../api/budgetApi'
import { fetchLatestPlan } from '../api/predictionApi'
import { PlanStatusBadge, PriorityBadge } from '../components/common/Badge'
import EmptyState from '../components/common/EmptyState'
import ErrorState from '../components/common/ErrorState'
import LoadingSpinner from '../components/common/LoadingSpinner'
import PageHeader from '../components/common/PageHeader'
import PlanSummary from '../components/shopping/PlanSummary'
import { useApi } from '../hooks/useApi'
import { formatCurrency } from '../utils/formatCurrency'
import { formatQuantity } from '../utils/formatQuantity'

const RULES = [
  'Within budget → nothing changes.',
  'Over budget → Optional items are reduced first, then Important items.',
  'Inside each group, the most expensive line is reduced first, and only by as much as needed.',
  'Essential items are never cut automatically. If they alone exceed the budget, they are flagged for you to decide.',
]

export default function BudgetOptimisationPage() {
  const { data, setData, loading, error, reload } = useApi(fetchLatestPlan)
  const [running, setRunning] = useState(false)

  const plan = data?.recommendation

  const handleOptimise = async () => {
    setRunning(true)
    try {
      const result = await optimisePlanBudget(plan.id)
      setData({ recommendation: result.recommendation })
      toast.success(result.summary.budget_status === 'over_budget' ? 'Optimised — essentials still exceed the budget.' : 'Budget optimisation applied.')
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setRunning(false)
    }
  }

  if (loading) return <LoadingSpinner />
  if (error) return <ErrorState message={error} onRetry={reload} />

  if (!plan) {
    return (
      <>
        <PageHeader title="Budget optimisation" />
        <div className="card">
          <EmptyState icon={Wallet} title="No plan to optimise" message="Generate a prediction first." action={<Link to="/app/predictions" className="btn btn-primary"><Sparkles className="h-4 w-4" /> Go to predictions</Link>} />
        </div>
      </>
    )
  }

  const lines = plan.items.filter((l) => l.recommended_quantity > 0 || l.final_quantity > 0)
  const anyPurchased = plan.items.some((l) => l.is_purchased)
  const unaffordable = plan.items.filter((l) => l.plan_status === 'unaffordable')

  return (
    <>
      <PageHeader
        title="Budget optimisation"
        description="Transparent, rule-based adjustments so the plan fits your budget."
        actions={
          <button type="button" className="btn btn-primary" onClick={handleOptimise} disabled={running || anyPurchased} title={anyPurchased ? 'Items already purchased from this plan' : ''}>
            <Scale className="h-4 w-4" /> {running ? 'Optimising…' : plan.status === 'generated' ? 'Run optimisation' : 'Re-run optimisation'}
          </button>
        }
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <PlanSummary plan={plan} />

          {unaffordable.length > 0 && (
            <div role="alert" className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
              <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />
              <div>
                <p className="font-semibold">Essential items exceed the budget</p>
                <p className="mt-1">
                  {unaffordable.map((l) => l.item_name).join(', ')} could not be covered. They were kept in the plan — consider
                  increasing the budget, using existing stock, or editing quantities on the shopping list.
                </p>
              </div>
            </div>
          )}

          <div className="card">
            {lines.length === 0 ? (
              <EmptyState compact title="Nothing to buy" message="Your stock covers the predicted needs for this period." />
            ) : (
              <div className="table-wrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th scope="col">Item</th>
                      <th scope="col">Recommended</th>
                      <th scope="col">Final</th>
                      <th scope="col">Cost</th>
                      <th scope="col">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {lines.map((l) => (
                      <tr key={l.id}>
                        <td>
                          <p className="font-medium text-slate-900">{l.item_name}</p>
                          <PriorityBadge priority={l.priority} />
                          {l.adjustment_note && <p className="mt-1 max-w-sm text-xs text-slate-500">{l.adjustment_note}</p>}
                        </td>
                        <td className="whitespace-nowrap text-slate-600">{formatQuantity(l.recommended_quantity, l.unit)}</td>
                        <td className={`whitespace-nowrap font-semibold ${l.final_quantity < l.recommended_quantity ? 'text-amber-700' : 'text-slate-900'}`}>
                          {formatQuantity(l.final_quantity, l.unit)}
                        </td>
                        <td className="whitespace-nowrap">{formatCurrency(l.estimated_cost)}</td>
                        <td><PlanStatusBadge status={l.plan_status} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        <aside className="space-y-6">
          <section className="card p-5">
            <h2 className="font-semibold text-slate-900">What happened</h2>
            <ol className="mt-3 space-y-2 text-sm text-slate-600">
              {plan.explanation.map((line, index) => (
                <li key={index} className="flex gap-2">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-600" aria-hidden="true" />
                  {line}
                </li>
              ))}
            </ol>
          </section>
          <section className="card p-5">
            <h2 className="font-semibold text-slate-900">The rules</h2>
            <ol className="mt-3 list-decimal space-y-2 pl-4 text-sm text-slate-600">
              {RULES.map((r) => <li key={r}>{r}</li>)}
            </ol>
            <p className="mt-3 text-xs text-slate-500">This is a deterministic rule-based method, not mathematical optimisation. It cannot guarantee every nutritional need is met.</p>
          </section>
          <Link to="/app/shopping-list" className="btn btn-primary w-full">Open shopping list <ArrowRight className="h-4 w-4" /></Link>
        </aside>
      </div>
    </>
  )
}
