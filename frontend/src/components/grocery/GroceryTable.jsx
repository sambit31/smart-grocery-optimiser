import { ArchiveRestore, Pencil, Trash2 } from 'lucide-react'
import Badge, { PriorityBadge } from '../common/Badge'
import { formatCurrency } from '../../utils/formatCurrency'
import { formatQuantity } from '../../utils/formatQuantity'

export default function GroceryTable({ items, onEdit, onDelete, onRestore }) {
  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th scope="col">Item</th>
            <th scope="col">Category</th>
            <th scope="col">Price</th>
            <th scope="col">Priority</th>
            <th scope="col">In stock</th>
            <th scope="col" className="text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id} className={item.is_archived ? 'opacity-60' : ''}>
              <td>
                <p className="font-medium text-slate-900">{item.name}</p>
                {item.description && <p className="max-w-xs truncate text-xs text-slate-500">{item.description}</p>}
              </td>
              <td className="text-slate-600">{item.category}</td>
              <td className="whitespace-nowrap">{formatCurrency(item.unit_price)} <span className="text-slate-400">/ {item.unit}</span></td>
              <td>{item.is_archived ? <Badge>Archived</Badge> : <PriorityBadge priority={item.priority} />}</td>
              <td className="whitespace-nowrap text-slate-600">{formatQuantity(item.current_stock, item.unit)}</td>
              <td>
                <div className="flex justify-end gap-1">
                  {item.is_archived ? (
                    <button type="button" className="btn btn-secondary btn-sm" onClick={() => onRestore(item)}>
                      <ArchiveRestore className="h-3.5 w-3.5" /> Restore
                    </button>
                  ) : (
                    <>
                      <button type="button" className="icon-btn" onClick={() => onEdit(item)} aria-label={`Edit ${item.name}`}>
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button type="button" className="icon-btn hover:text-red-600" onClick={() => onDelete(item)} aria-label={`Delete ${item.name}`}>
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
