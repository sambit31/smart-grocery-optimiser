import { useState } from 'react'
import { Check, PackageCheck, Pencil, X } from 'lucide-react'
import { PlanStatusBadge, PriorityBadge } from '../common/Badge'
import { formatCurrency } from '../../utils/formatCurrency'
import { formatQuantity, unitStep } from '../../utils/formatQuantity'

/**
 * One shopping-list line.
 *  - Checkbox  = "in my basket" tick only. It never records a purchase.
 *  - "Bought"  = separate, confirmed action that records the purchase and stock.
 */
export default function ShoppingListItem({ line, onToggle, onEditQuantity, onMarkPurchased, busy }) {
  const [editing, setEditing] = useState(false)
  const [quantity, setQuantity] = useState(line.final_quantity)
  const [showWhy, setShowWhy] = useState(false)

  const saveQuantity = async () => {
    const ok = await onEditQuantity(line, quantity)
    if (ok) setEditing(false)
  }

  return (
    <li className={`px-4 py-4 sm:px-5 ${line.is_purchased ? 'bg-brand-50/40' : ''}`}>
      <div className="flex items-start gap-3">
        <input
          type="checkbox"
          className="mt-1 h-5 w-5 shrink-0 cursor-pointer rounded accent-brand-700"
          checked={line.is_checked}
          disabled={busy || line.is_purchased}
          onChange={(e) => onToggle(line, e.target.checked)}
          aria-label={`Tick ${line.item_name}`}
        />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className={`font-medium ${line.is_checked ? 'text-slate-400 line-through' : 'text-slate-900'}`}>{line.item_name}</p>
            <PriorityBadge priority={line.priority} />
            <PlanStatusBadge status={line.plan_status} />
            {line.is_purchased && <span className="inline-flex items-center gap-1 text-xs font-medium text-brand-700"><PackageCheck className="h-3.5 w-3.5" /> Purchased</span>}
          </div>

          <dl className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-slate-500 sm:grid-cols-4">
            <div><dt className="inline">Predicted: </dt><dd className="inline text-slate-700">{formatQuantity(line.predicted_quantity, line.unit)}</dd></div>
            <div><dt className="inline">In stock: </dt><dd className="inline text-slate-700">{formatQuantity(line.stock_quantity, line.unit)}</dd></div>
            <div><dt className="inline">Recommended: </dt><dd className="inline text-slate-700">{formatQuantity(line.recommended_quantity, line.unit)}</dd></div>
            <div><dt className="inline">Price: </dt><dd className="inline text-slate-700">{formatCurrency(line.unit_price)}/{line.unit}</dd></div>
          </dl>

          <button type="button" className="mt-2 text-xs font-medium text-brand-700 hover:underline" onClick={() => setShowWhy(!showWhy)} aria-expanded={showWhy}>
            {showWhy ? 'Hide reason' : 'Why this quantity?'}
          </button>
          {showWhy && (
            <div className="mt-2 rounded-lg bg-slate-50 p-3 text-xs text-slate-600">
              <p>{line.reason}</p>
              {line.adjustment_note && <p className="mt-1 font-medium text-amber-800">{line.adjustment_note}</p>}
            </div>
          )}
        </div>

        <div className="flex shrink-0 flex-col items-end gap-2 text-right">
          {editing ? (
            <div className="flex items-center gap-1">
              <label htmlFor={`qty-${line.id}`} className="sr-only">Quantity for {line.item_name}</label>
              <input
                id={`qty-${line.id}`}
                type="number"
                min="0"
                step={unitStep(line.unit)}
                className="input w-20 px-2 py-1"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
              />
              <button type="button" className="icon-btn text-brand-700" onClick={saveQuantity} disabled={busy} aria-label="Save quantity"><Check className="h-4 w-4" /></button>
              <button type="button" className="icon-btn" onClick={() => { setEditing(false); setQuantity(line.final_quantity) }} aria-label="Cancel"><X className="h-4 w-4" /></button>
            </div>
          ) : (
            <div className="flex items-center gap-1">
              <span className="text-base font-semibold text-slate-900">{formatQuantity(line.final_quantity, line.unit)}</span>
              {!line.is_purchased && (
                <button type="button" className="icon-btn h-7 w-7" onClick={() => setEditing(true)} aria-label={`Edit quantity of ${line.item_name}`}>
                  <Pencil className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
          )}
          <span className="text-sm text-slate-600">{formatCurrency(line.estimated_cost)}</span>
          {!line.is_purchased && line.final_quantity > 0 && (
            <button type="button" className="btn btn-secondary btn-sm" onClick={() => onMarkPurchased(line)} disabled={busy}>
              <PackageCheck className="h-3.5 w-3.5" /> Bought
            </button>
          )}
        </div>
      </div>
    </li>
  )
}
