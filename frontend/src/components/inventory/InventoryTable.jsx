import { Minus, Pencil, Plus } from 'lucide-react'
import Badge from '../common/Badge'
import { formatDate, formatQuantity } from '../../utils/formatQuantity'

export default function InventoryTable({ records, onAdjust, onEdit }) {
  const today = new Date().toISOString().slice(0, 10)
  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th scope="col">Item</th>
            <th scope="col">Quantity</th>
            <th scope="col">Status</th>
            <th scope="col">Expiry</th>
            <th scope="col">Last updated</th>
            <th scope="col" className="text-right">Adjust</th>
          </tr>
        </thead>
        <tbody>
          {records.map((r) => {
            const expired = r.expiry_date && r.expiry_date < today
            return (
              <tr key={r.id}>
                <td>
                  <p className="font-medium text-slate-900">{r.item_name}</p>
                  <p className="text-xs text-slate-500">{r.category}</p>
                </td>
                <td className="whitespace-nowrap text-base font-semibold text-slate-900">{formatQuantity(r.quantity, r.unit)}</td>
                <td>
                  {r.is_low_stock ? <Badge tone="amber">Low stock</Badge> : <Badge tone="green">OK</Badge>}
                  <p className="mt-1 text-xs text-slate-400">Low at ≤ {formatQuantity(r.low_stock_threshold, r.unit)}</p>
                </td>
                <td className={expired ? 'font-medium text-red-600' : 'text-slate-600'}>
                  {r.expiry_date ? `${formatDate(r.expiry_date)}${expired ? ' (expired)' : ''}` : '—'}
                </td>
                <td className="text-slate-500">{formatDate(r.updated_at)}</td>
                <td>
                  <div className="flex justify-end gap-1">
                    <button type="button" className="icon-btn" onClick={() => onAdjust(r, -1)} aria-label={`Decrease ${r.item_name}`}>
                      <Minus className="h-4 w-4" />
                    </button>
                    <button type="button" className="icon-btn" onClick={() => onAdjust(r, 1)} aria-label={`Increase ${r.item_name}`}>
                      <Plus className="h-4 w-4" />
                    </button>
                    <button type="button" className="icon-btn" onClick={() => onEdit(r)} aria-label={`Edit ${r.item_name}`}>
                      <Pencil className="h-4 w-4" />
                    </button>
                  </div>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
