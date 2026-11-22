import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { AlertTriangle, ListChecks, Printer, Sparkles } from 'lucide-react'
import { getErrorMessage } from '../api/axios'
import { fetchPlan, fetchPlans, generatePlan, markPlanItemPurchased, updatePlanItem } from '../api/predictionApi'
import EmptyState from '../components/common/EmptyState'
import ErrorState from '../components/common/ErrorState'
import LoadingSpinner from '../components/common/LoadingSpinner'
import Modal from '../components/common/Modal'
import PageHeader from '../components/common/PageHeader'
import PlanSummary from '../components/shopping/PlanSummary'
import ShoppingList from '../components/shopping/ShoppingList'
import { useApi } from '../hooks/useApi'
import { formatCurrency } from '../utils/formatCurrency'
import { formatDate, formatQuantity, todayISO, unitStep } from '../utils/formatQuantity'

export default function ShoppingListPage() {
  const { data: plansData, loading: plansLoading, error: plansError, reload: reloadPlans } = useApi(fetchPlans)
  const [planId, setPlanId] = useState(null)
  const [plan, setPlan] = useState(null)
  const [loadingPlan, setLoadingPlan] = useState(false)
  const [busy, setBusy] = useState(false)
  const [onlyToBuy, setOnlyToBuy] = useState(true)
  const [buying, setBuying] = useState(null)
  const [buyForm, setBuyForm] = useState({})

  const plans = plansData?.recommendations || []

  useEffect(() => {
    if (!planId && plans.length) setPlanId(plans[0].id)
  }, [plans, planId])

  useEffect(() => {
    if (!planId) return
    setLoadingPlan(true)
    fetchPlan(planId)
      .then((d) => setPlan(d.recommendation))
      .catch((err) => toast.error(getErrorMessage(err)))
      .finally(() => setLoadingPlan(false))
  }, [planId])

  const handleGenerate = async () => {
    setBusy(true)
    try {
      const { recommendation } = await generatePlan({ optimise: true })
      toast.success('New plan generated and fitted to your budget.')
      await reloadPlans()
      setPlanId(recommendation.id)
      setPlan(recommendation)
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const handleToggle = async (line, checked) => {
    setBusy(true)
    try {
      const { recommendation } = await updatePlanItem(plan.id, line.id, { is_checked: checked })
      setPlan(recommendation)
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const handleEditQuantity = async (line, quantity) => {
    if (quantity === '' || Number(quantity) < 0) {
      toast.error('Quantity must be zero or greater.')
      return false
    }
    setBusy(true)
    try {
      const { recommendation } = await updatePlanItem(plan.id, line.id, { final_quantity: Number(quantity) })
      setPlan(recommendation)
      toast.success('Quantity updated and total recalculated.')
      return true
    } catch (err) {
      toast.error(getErrorMessage(err))
      return false
    } finally {
      setBusy(false)
    }
  }

  const openBuy = (line) => {
    setBuying(line)
    setBuyForm({ quantity: line.final_quantity, unit_price: line.unit_price, purchase_date: todayISO(), store_name: '' })
  }

  const confirmBuy = async (event) => {
    event.preventDefault()
    if (!(Number(buyForm.quantity) > 0)) return toast.error('Quantity must be greater than zero.')
    if (buyForm.unit_price === '' || Number(buyForm.unit_price) < 0) return toast.error('Price cannot be negative.')
    setBusy(true)
    try {
      const { recommendation } = await markPlanItemPurchased(plan.id, buying.id, {
        quantity: Number(buyForm.quantity),
        unit_price: Number(buyForm.unit_price),
        purchase_date: buyForm.purchase_date,
        store_name: buyForm.store_name.trim() || null,
      })
      setPlan(recommendation)
      setBuying(null)
      toast.success(`${buying.item_name}: purchase recorded and stock updated.`)
      reloadPlans()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  if (plansLoading) return <LoadingSpinner />
  if (plansError) return <ErrorState message={plansError} onRetry={reloadPlans} />

  const header = (
    <PageHeader
      title="Shopping list"
      description="Tick items as they go in your basket. Use “Bought” to record the purchase and update stock."
      actions={
        <>
          {plan && <button type="button" className="btn btn-secondary" onClick={() => window.print()}><Printer className="h-4 w-4" /> Print</button>}
          <button type="button" className="btn btn-primary" onClick={handleGenerate} disabled={busy}><Sparkles className="h-4 w-4" /> Generate new plan</button>
        </>
      }
    />
  )

  if (!plans.length) {
    return (
      <>
        {header}
        <div className="card">
          <EmptyState icon={ListChecks} title="No saved plans yet" message="Generate a plan to get a budget-checked shopping list." />
        </div>
      </>
    )
  }

  const lines = plan ? plan.items.filter((l) => !onlyToBuy || l.final_quantity > 0 || l.is_purchased) : []
  const unaffordable = plan?.items.filter((l) => l.plan_status === 'unaffordable') || []
  const toBuyCount = plan?.items.filter((l) => l.final_quantity > 0).length || 0
  const checkedCount = plan?.items.filter((l) => l.final_quantity > 0 && l.is_checked).length || 0

  return (
    <>
      {header}
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <label htmlFor="plan-select" className="text-sm font-medium text-slate-700">Saved plan</label>
        <select id="plan-select" className="input w-auto" value={planId || ''} onChange={(e) => setPlanId(Number(e.target.value))}>
          {plans.map((p) => (
            <option key={p.id} value={p.id}>
              #{p.id} · {formatDate(p.created_at)} · {formatCurrency(p.final_total_cost)} · {p.status}
            </option>
          ))}
        </select>
        <label className="ml-auto flex items-center gap-2 text-sm text-slate-600">
          <input type="checkbox" className="h-4 w-4 accent-brand-700" checked={onlyToBuy} onChange={(e) => setOnlyToBuy(e.target.checked)} />
          Only items to buy
        </label>
      </div>

      {loadingPlan || !plan ? (
        <LoadingSpinner />
      ) : (
        <div className="space-y-4">
          <PlanSummary plan={plan} />

          {plan.status === 'generated' && plan.budget_status === 'needs_optimisation' && (
            <p className="rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-800">
              This plan is over budget and hasn’t been optimised yet. <Link to="/app/budget" className="font-medium underline">Optimise it</Link> or edit quantities below.
            </p>
          )}
          {plan.budget_status === 'over_budget' && (
            <div role="alert" className="flex items-start gap-3 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-800">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>
                The plan is {formatCurrency(-plan.remaining_budget)} over budget.
                {unaffordable.length > 0 && ` Essential items not covered: ${unaffordable.map((l) => l.item_name).join(', ')}.`}
              </span>
            </div>
          )}

          <div className="flex items-center justify-between text-sm text-slate-600">
            <span>{checkedCount} of {toBuyCount} items ticked</span>
            <span>Total: <strong className="text-slate-900">{formatCurrency(plan.final_total_cost)}</strong></span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-slate-200" aria-hidden="true">
            <div className="h-full bg-brand-600 transition-all" style={{ width: `${toBuyCount ? (checkedCount / toBuyCount) * 100 : 0}%` }} />
          </div>

          {lines.length ? (
            <ShoppingList lines={lines} busy={busy} onToggle={handleToggle} onEditQuantity={handleEditQuantity} onMarkPurchased={openBuy} />
          ) : (
            <div className="card"><EmptyState compact title="Nothing to buy in this plan" message="Your current stock covers the predicted needs." /></div>
          )}
        </div>
      )}

      <Modal
        open={!!buying}
        size="sm"
        title={buying ? `Record purchase: ${buying.item_name}` : ''}
        onClose={() => setBuying(null)}
        footer={
          <>
            <button type="button" className="btn btn-secondary" onClick={() => setBuying(null)}>Cancel</button>
            <button type="submit" form="buy-form" className="btn btn-primary" disabled={busy}>{busy ? 'Saving…' : 'Confirm purchase'}</button>
          </>
        }
      >
        {buying && (
          <form id="buy-form" onSubmit={confirmBuy} className="space-y-4">
            <p className="text-sm text-slate-600">This records a purchase in your history and adds the quantity to your inventory.</p>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label htmlFor="buy-qty" className="label">Quantity ({buying.unit})</label>
                <input id="buy-qty" type="number" min="0" step={unitStep(buying.unit)} className="input" value={buyForm.quantity} onChange={(e) => setBuyForm({ ...buyForm, quantity: e.target.value })} />
              </div>
              <div>
                <label htmlFor="buy-price" className="label">Price / {buying.unit} (₹)</label>
                <input id="buy-price" type="number" min="0" step="0.01" className="input" value={buyForm.unit_price} onChange={(e) => setBuyForm({ ...buyForm, unit_price: e.target.value })} />
              </div>
              <div>
                <label htmlFor="buy-date" className="label">Date</label>
                <input id="buy-date" type="date" max={todayISO()} className="input" value={buyForm.purchase_date} onChange={(e) => setBuyForm({ ...buyForm, purchase_date: e.target.value })} />
              </div>
              <div>
                <label htmlFor="buy-store" className="label">Store</label>
                <input id="buy-store" className="input" value={buyForm.store_name} onChange={(e) => setBuyForm({ ...buyForm, store_name: e.target.value })} maxLength={120} />
              </div>
            </div>
            <p className="rounded-lg bg-slate-50 px-3 py-2 text-sm">
              {formatQuantity(Number(buyForm.quantity || 0), buying.unit)} × {formatCurrency(buyForm.unit_price)} ={' '}
              <strong>{formatCurrency(Number(buyForm.quantity || 0) * Number(buyForm.unit_price || 0))}</strong>
            </p>
          </form>
        )}
      </Modal>
    </>
  )
}
