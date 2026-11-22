import { BudgetStatusBadge } from '../common/Badge'
import { formatCurrency } from '../../utils/formatCurrency'
import { formatDate } from '../../utils/formatQuantity'

/** Budget / cost / remaining strip shown on every planning page. */
export default function PlanSummary({ plan }) {
  const remaining = plan.remaining_budget
  return (
    <div className="card p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-slate-900">Plan #{plan.id}</p>
          <p className="text-xs text-slate-500">
            {formatDate(plan.planning_period_start)} – {formatDate(plan.planning_period_end)} · {plan.prediction_method}
          </p>
        </div>
        <BudgetStatusBadge status={plan.budget_status} />
      </div>
      <dl className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div>
          <dt className="text-xs text-slate-500">Plan budget</dt>
          <dd className="text-lg font-semibold text-slate-900">{formatCurrency(plan.budget)}</dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500">Predicted cost</dt>
          <dd className="text-lg font-semibold text-slate-900">{formatCurrency(plan.predicted_total_cost)}</dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500">Final cost</dt>
          <dd className="text-lg font-semibold text-slate-900">{formatCurrency(plan.final_total_cost)}</dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500">Remaining</dt>
          <dd className={`text-lg font-semibold ${remaining < 0 ? 'text-red-600' : 'text-brand-700'}`}>{formatCurrency(remaining)}</dd>
        </div>
      </dl>
    </div>
  )
}
