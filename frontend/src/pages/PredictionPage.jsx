import { Fragment, useState } from 'react'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { ArrowRight, Info, Sparkles } from 'lucide-react'
import { getErrorMessage } from '../api/axios'
import { fetchLatestPlan, generatePlan } from '../api/predictionApi'
import { PriorityBadge, SourceBadge, SufficiencyBadge } from '../components/common/Badge'
import EmptyState from '../components/common/EmptyState'
import ErrorState from '../components/common/ErrorState'
import LoadingSpinner from '../components/common/LoadingSpinner'
import PageHeader from '../components/common/PageHeader'
import PlanSummary from '../components/shopping/PlanSummary'
import { useApi } from '../hooks/useApi'
import { formatCurrency } from '../utils/formatCurrency'
import { formatQuantity } from '../utils/formatQuantity'

export default function PredictionPage() {
  const { data, setData, loading, error, reload } = useApi(fetchLatestPlan)
  const [historyPeriods, setHistoryPeriods] = useState(3)
  const [generating, setGenerating] = useState(false)
  const [expanded, setExpanded] = useState(null)

  const handleGenerate = async () => {
    setGenerating(true)
    try {
      const result = await generatePlan({ history_periods: historyPeriods })
      setData(result)
      toast.success('New prediction generated and saved.')
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setGenerating(false)
    }
  }

  const plan = data?.recommendation
  const needsData = plan?.items.filter((i) => i.prediction_source === 'no_data').length || 0

  return (
    <>
      <PageHeader
        title="Prediction results"
        description="Predicted need for the planning period, minus your current stock, gives the quantity to buy."
        actions={
          <>
            <label className="flex items-center gap-2 text-sm text-slate-600">
              <span className="whitespace-nowrap">History window</span>
              <select className="input w-auto" value={historyPeriods} onChange={(e) => setHistoryPeriods(Number(e.target.value))}>
                {[1, 2, 3, 4, 6].map((n) => <option key={n} value={n}>{n} × 30 days</option>)}
              </select>
            </label>
            <button type="button" className="btn btn-primary" onClick={handleGenerate} disabled={generating}>
              <Sparkles className="h-4 w-4" /> {generating ? 'Generating…' : 'Generate new plan'}
            </button>
          </>
        }
      />

      <div className="mb-6 flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-600">
        <Info className="mt-0.5 h-5 w-5 shrink-0 text-brand-700" aria-hidden="true" />
        <p>
          <strong className="text-slate-800">Method:</strong> consumption is summed into 30-day periods; the prediction is the
          simple average of those period totals, scaled to your planning period. Then{' '}
          <code className="rounded bg-slate-100 px-1">buy = max(0, predicted − stock)</code>, rounded up to whole packets/pieces.
          Items without history use your own estimate (labelled) or are marked “Needs data”. No figures are invented.
        </p>
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : error ? (
        <ErrorState message={error} onRetry={reload} />
      ) : !plan ? (
        <div className="card">
          <EmptyState icon={Sparkles} title="No prediction yet" message="Generate a plan to see predicted requirements for each item." action={<button type="button" className="btn btn-primary" onClick={handleGenerate} disabled={generating}>Generate plan</button>} />
        </div>
      ) : (
        <div className="space-y-6">
          <PlanSummary plan={plan} />
          {needsData > 0 && (
            <p className="rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-800">
              {needsData} item(s) have no consumption history or estimate, so nothing is recommended for them.{' '}
              <Link to="/app/consumption" className="font-medium underline">Record consumption</Link> or add an initial estimate in the catalogue.
            </p>
          )}
          <div className="card">
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th scope="col">Item</th>
                    <th scope="col">Basis</th>
                    <th scope="col">Predicted</th>
                    <th scope="col">In stock</th>
                    <th scope="col">To buy</th>
                    <th scope="col">Unit price</th>
                    <th scope="col">Est. cost</th>
                    <th scope="col"><span className="sr-only">Details</span></th>
                  </tr>
                </thead>
                <tbody>
                  {plan.items.map((line) => (
                    <Fragment key={line.id}>
                      <tr>
                        <td>
                          <p className="font-medium text-slate-900">{line.item_name}</p>
                          <PriorityBadge priority={line.priority} />
                        </td>
                        <td>
                          <div className="flex flex-col items-start gap-1">
                            <SourceBadge source={line.prediction_source} />
                            {line.prediction_source === 'consumption_history' && <SufficiencyBadge value={line.data_sufficiency} />}
                          </div>
                        </td>
                        <td className="whitespace-nowrap">{formatQuantity(line.predicted_quantity, line.unit)}</td>
                        <td className="whitespace-nowrap text-slate-600">{formatQuantity(line.stock_quantity, line.unit)}</td>
                        <td className="whitespace-nowrap font-semibold text-slate-900">{formatQuantity(line.recommended_quantity, line.unit)}</td>
                        <td className="whitespace-nowrap">{formatCurrency(line.unit_price)}</td>
                        <td className="whitespace-nowrap font-medium">{formatCurrency(line.recommended_cost)}</td>
                        <td>
                          <button type="button" className="text-xs font-medium text-brand-700 hover:underline" onClick={() => setExpanded(expanded === line.id ? null : line.id)} aria-expanded={expanded === line.id}>
                            {expanded === line.id ? 'Hide' : 'Why?'}
                          </button>
                        </td>
                      </tr>
                      {expanded === line.id && (
                        <tr>
                          <td colSpan={8} className="bg-slate-50 text-sm text-slate-600">{line.reason}</td>
                        </tr>
                      )}
                    </Fragment>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <div className="flex justify-end">
            <Link to="/app/budget" className="btn btn-primary">Check against budget <ArrowRight className="h-4 w-4" /></Link>
          </div>
        </div>
      )}
    </>
  )
}
