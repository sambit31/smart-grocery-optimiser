import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { BarChart3 } from 'lucide-react'
import { fetchAllGroceries } from '../api/groceryApi'
import { fetchConsumptionReport, fetchRecommendationReport, fetchSpendingReport } from '../api/reportApi'
import { BudgetStatusBadge } from '../components/common/Badge'
import EmptyState from '../components/common/EmptyState'
import ErrorState from '../components/common/ErrorState'
import LoadingSpinner from '../components/common/LoadingSpinner'
import PageHeader from '../components/common/PageHeader'
import StatCard from '../components/common/StatCard'
import ConsumptionChart from '../components/charts/ConsumptionChart'
import SpendingChart from '../components/charts/SpendingChart'
import { useApi } from '../hooks/useApi'
import { formatCurrency, formatCurrencyShort } from '../utils/formatCurrency'
import { formatDate, formatQuantity } from '../utils/formatQuantity'

function Section({ title, children, action }) {
  return (
    <section className="card">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 px-5 py-3.5">
        <h2 className="text-sm font-semibold text-slate-900">{title}</h2>
        {action}
      </div>
      <div className="p-4">{children}</div>
    </section>
  )
}

export default function ReportsPage() {
  const [months, setMonths] = useState(6)
  const spending = useApi(() => fetchSpendingReport(months), [months])
  const plans = useApi(fetchRecommendationReport)
  const { data: items } = useApi(fetchAllGroceries)
  const [itemId, setItemId] = useState('')
  const consumption = useApi(
    () => (itemId ? fetchConsumptionReport({ item_id: itemId, months }) : Promise.resolve(null)),
    [itemId, months],
  )

  useEffect(() => {
    if (items?.length && !itemId) setItemId(String(items[0].id))
  }, [items, itemId])

  if (spending.loading && !spending.data) return <LoadingSpinner />
  if (spending.error) return <ErrorState message={spending.error} onRetry={spending.reload} />

  const s = spending.data
  const hasSpending = s.by_month.some((m) => m.total > 0)
  const trend = consumption.data?.trend
  const trendHasData = trend?.months.some((m) => m.quantity > 0)
  const comparison = plans.data?.predicted_vs_purchased?.find((p) => p.has_purchase_data)

  return (
    <>
      <PageHeader
        title="Reports"
        description="Spending, consumption and plan history, all calculated from your records."
        actions={
          <select aria-label="Report period" className="input w-auto" value={months} onChange={(e) => setMonths(Number(e.target.value))}>
            {[3, 6, 12].map((m) => <option key={m} value={m}>Last {m} months</option>)}
          </select>
        }
      />

      <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-3">
        <StatCard label={`Total spent (${months} months)`} value={formatCurrency(s.total_spent)} />
        <StatCard label="Average per month" value={formatCurrency(s.average_monthly)} tone="slate" />
        <StatCard label="Categories bought" value={s.by_category.length} tone="slate" />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Section title="Monthly spending vs budget">
          {hasSpending ? <SpendingChart data={s.by_month} /> : <EmptyState compact icon={BarChart3} title="No spending in this period" />}
        </Section>

        <Section title="Spending by category">
          {s.by_category.length ? (
            <ResponsiveContainer width="100%" height={Math.max(200, s.by_category.length * 36)}>
              <BarChart data={s.by_category} layout="vertical" margin={{ left: 10, right: 16 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
                <XAxis type="number" tickFormatter={formatCurrencyShort} tick={{ fontSize: 12, fill: '#64748b' }} />
                <YAxis type="category" dataKey="category" width={140} tick={{ fontSize: 12, fill: '#475569' }} />
                <Tooltip formatter={(v) => [formatCurrency(v), 'Spent']} />
                <Bar dataKey="total" fill="#15803d" radius={[0, 4, 4, 0]} maxBarSize={22} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState compact title="No purchases in this period" />
          )}
        </Section>

        <Section title="Budget usage by month">
          <div className="table-wrap">
            <table className="table">
              <thead><tr><th>Month</th><th>Spent</th><th>Budget</th><th>Used</th></tr></thead>
              <tbody>
                {s.by_month.map((m) => (
                  <tr key={m.month}>
                    <td>{m.label}</td>
                    <td>{formatCurrency(m.total)}</td>
                    <td className="text-slate-500">{formatCurrency(m.budget)}</td>
                    <td>
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-20 overflow-hidden rounded-full bg-slate-200" aria-hidden="true">
                          <div className={`h-full ${m.budget_used_percent > 100 ? 'bg-red-500' : 'bg-brand-600'}`} style={{ width: `${Math.min(100, m.budget_used_percent)}%` }} />
                        </div>
                        <span className={m.budget_used_percent > 100 ? 'font-medium text-red-600' : ''}>{m.budget_used_percent}%</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>

        <Section
          title="Consumption trend"
          action={
            <select aria-label="Item" className="input w-auto py-1" value={itemId} onChange={(e) => setItemId(e.target.value)}>
              {items?.map((i) => <option key={i.id} value={i.id}>{i.name}</option>)}
            </select>
          }
        >
          {trendHasData ? <ConsumptionChart data={trend.months} unit={trend.unit} /> : <EmptyState compact title="No consumption recorded for this item" />}
        </Section>

        <Section title="Predicted vs purchased (latest plan with purchases)">
          {comparison ? (
            <>
              <p className="mb-2 text-xs text-slate-500">Plan #{comparison.recommendation_id} · {comparison.period}. “Purchased” counts all purchases in the plan period.</p>
              <div className="table-wrap">
                <table className="table">
                  <thead><tr><th>Item</th><th>Predicted need</th><th>Planned to buy</th><th>Purchased</th></tr></thead>
                  <tbody>
                    {comparison.items.map((row) => (
                      <tr key={row.item_name}>
                        <td className="font-medium">{row.item_name}</td>
                        <td>{formatQuantity(row.predicted, row.unit)}</td>
                        <td>{formatQuantity(row.planned, row.unit)}</td>
                        <td className={row.purchased > row.planned ? 'text-amber-700' : ''}>{formatQuantity(row.purchased, row.unit)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <EmptyState compact title="Not enough data to compare yet" message="Record purchases after generating a plan to compare predicted and actual quantities." />
          )}
        </Section>

        <Section title="Saved plan history" action={<Link to="/app/shopping-list" className="text-xs font-medium text-brand-700 hover:underline">Open shopping list</Link>}>
          {plans.data?.history.length ? (
            <div className="table-wrap">
              <table className="table">
                <thead><tr><th>Plan</th><th>Created</th><th>Cost</th><th>Budget</th><th>Status</th></tr></thead>
                <tbody>
                  {plans.data.history.map((p) => (
                    <tr key={p.id}>
                      <td>#{p.id}</td>
                      <td className="whitespace-nowrap">{formatDate(p.created_at)}</td>
                      <td>{formatCurrency(p.final_total_cost)}</td>
                      <td className="text-slate-500">{formatCurrency(p.budget)}</td>
                      <td><BudgetStatusBadge status={p.budget_status} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyState compact title="No saved plans yet" />
          )}
        </Section>
      </div>

      <p className="mt-6 text-sm text-slate-500">
        Full purchase history with filters is on the <Link to="/app/purchases" className="font-medium text-brand-700 hover:underline">Purchase History</Link> page.
      </p>
    </>
  )
}
