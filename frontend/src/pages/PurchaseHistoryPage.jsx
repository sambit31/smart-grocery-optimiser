import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Pencil, Plus, Receipt, Trash2 } from 'lucide-react'
import { getErrorMessage } from '../api/axios'
import { fetchAllGroceries } from '../api/groceryApi'
import { createPurchase, deletePurchase, fetchPurchases, updatePurchase } from '../api/purchaseApi'
import Badge from '../components/common/Badge'
import ConfirmDialog from '../components/common/ConfirmDialog'
import EmptyState from '../components/common/EmptyState'
import ErrorState from '../components/common/ErrorState'
import LoadingSpinner from '../components/common/LoadingSpinner'
import Modal from '../components/common/Modal'
import PageHeader from '../components/common/PageHeader'
import Pagination from '../components/common/Pagination'
import { useApi } from '../hooks/useApi'
import { formatCurrency } from '../utils/formatCurrency'
import { formatDate, formatQuantity, newClientReference, todayISO, unitStep } from '../utils/formatQuantity'

function PurchaseForm({ open, purchase, items, onClose, onSaved }) {
  const [form, setForm] = useState({})
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!open) return
    setError('')
    setForm(
      purchase
        ? { ...purchase, store_name: purchase.store_name || '', notes: purchase.notes || '' }
        : {
            item_id: items[0]?.id || '',
            quantity: '',
            unit_price: items[0]?.unit_price ?? '',
            purchase_date: todayISO(),
            store_name: '',
            notes: '',
            update_inventory: true,
            // A fresh id per form: if this exact form is submitted twice,
            // the backend recognises the duplicate and ignores it.
            client_reference: newClientReference(),
          },
    )
  }, [open, purchase, items])

  const selected = items.find((i) => String(i.id) === String(form.item_id))

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target
    const next = { ...form, [name]: type === 'checkbox' ? checked : value }
    if (name === 'item_id' && !purchase) {
      next.unit_price = items.find((i) => String(i.id) === value)?.unit_price ?? ''
    }
    setForm(next)
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!form.item_id) return setError('Please choose an item.')
    if (!(Number(form.quantity) > 0)) return setError('Quantity must be greater than zero.')
    if (form.unit_price === '' || Number(form.unit_price) < 0) return setError('Unit price must be zero or greater.')
    if (!form.purchase_date) return setError('Purchase date is required.')
    if (form.purchase_date > todayISO()) return setError('Purchase date cannot be in the future.')
    const payload = {
      item_id: Number(form.item_id),
      quantity: Number(form.quantity),
      unit_price: Number(form.unit_price),
      purchase_date: form.purchase_date,
      store_name: form.store_name.trim() || null,
      notes: form.notes.trim() || null,
    }
    setSaving(true)
    setError('')
    try {
      if (purchase) {
        await updatePurchase(purchase.id, payload)
        toast.success('Purchase updated and stock reconciled.')
      } else {
        await createPurchase({ ...payload, update_inventory: form.update_inventory, client_reference: form.client_reference })
        toast.success(form.update_inventory ? 'Purchase recorded and added to inventory.' : 'Purchase recorded.')
      }
      onSaved()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const total = Number(form.quantity || 0) * Number(form.unit_price || 0)

  return (
    <Modal
      open={open}
      title={purchase ? 'Edit purchase' : 'Record a purchase'}
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button type="submit" form="purchase-form" className="btn btn-primary" disabled={saving}>{saving ? 'Saving…' : 'Save purchase'}</button>
        </>
      }
    >
      <form id="purchase-form" onSubmit={handleSubmit} className="space-y-4" noValidate>
        {error && <div role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
        <div>
          <label htmlFor="p-item" className="label">Item</label>
          <select id="p-item" name="item_id" className="input" value={form.item_id ?? ''} onChange={handleChange} disabled={!!purchase?.recommendation_item_id}>
            {items.map((i) => <option key={i.id} value={i.id}>{i.name} ({i.unit})</option>)}
          </select>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="p-qty" className="label">Quantity {selected && `(${selected.unit})`}</label>
            <input id="p-qty" name="quantity" type="number" min="0" step={unitStep(selected?.unit) === '1' ? '1' : 'any'} className="input" value={form.quantity ?? ''} onChange={handleChange} />
          </div>
          <div>
            <label htmlFor="p-price" className="label">Unit price (₹)</label>
            <input id="p-price" name="unit_price" type="number" min="0" step="0.01" className="input" value={form.unit_price ?? ''} onChange={handleChange} />
          </div>
          <div>
            <label htmlFor="p-date" className="label">Purchase date</label>
            <input id="p-date" name="purchase_date" type="date" max={todayISO()} className="input" value={form.purchase_date ?? ''} onChange={handleChange} />
          </div>
          <div>
            <label htmlFor="p-store" className="label">Store — optional</label>
            <input id="p-store" name="store_name" className="input" value={form.store_name ?? ''} onChange={handleChange} maxLength={120} />
          </div>
        </div>
        <div>
          <label htmlFor="p-notes" className="label">Notes — optional</label>
          <input id="p-notes" name="notes" className="input" value={form.notes ?? ''} onChange={handleChange} maxLength={500} />
        </div>
        {!purchase && (
          <label className="flex items-start gap-2 text-sm text-slate-700">
            <input type="checkbox" name="update_inventory" className="mt-0.5 h-4 w-4 accent-brand-700" checked={!!form.update_inventory} onChange={handleChange} />
            <span>Add this quantity to my inventory <span className="block text-xs text-slate-500">Untick only for old purchases whose stock you have already counted.</span></span>
          </label>
        )}
        <p className="rounded-lg bg-slate-50 px-3 py-2 text-sm">Total: <strong>{formatCurrency(total)}</strong></p>
      </form>
    </Modal>
  )
}

export default function PurchaseHistoryPage() {
  const [filters, setFilters] = useState({ start_date: '', end_date: '', item_id: '', page: 1 })
  const { data, loading, error, reload } = useApi(() => fetchPurchases({ ...filters, per_page: 15 }), [filters])
  const { data: items } = useApi(fetchAllGroceries)
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [deleting, setDeleting] = useState(null)
  const [busy, setBusy] = useState(false)

  const setFilter = (name, value) => setFilters((f) => ({ ...f, [name]: value, page: 1 }))

  const confirmDelete = async () => {
    setBusy(true)
    try {
      await deletePurchase(deleting.id)
      toast.success('Purchase deleted and stock reversed.')
      setDeleting(null)
      reload()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <PageHeader
        title="Purchase history"
        description="What you bought, when, and for how much. Buying is not the same as using — record consumption separately."
        actions={<button type="button" className="btn btn-primary" disabled={!items?.length} onClick={() => { setEditing(null); setFormOpen(true) }}><Plus className="h-4 w-4" /> Record purchase</button>}
      />

      <div className="card">
        <div className="grid gap-3 border-b border-slate-100 p-4 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <label htmlFor="f-start" className="label">From</label>
            <input id="f-start" type="date" className="input" value={filters.start_date} onChange={(e) => setFilter('start_date', e.target.value)} />
          </div>
          <div>
            <label htmlFor="f-end" className="label">To</label>
            <input id="f-end" type="date" className="input" value={filters.end_date} onChange={(e) => setFilter('end_date', e.target.value)} />
          </div>
          <div>
            <label htmlFor="f-item" className="label">Item</label>
            <select id="f-item" className="input" value={filters.item_id} onChange={(e) => setFilter('item_id', e.target.value)}>
              <option value="">All items</option>
              {items?.map((i) => <option key={i.id} value={i.id}>{i.name}</option>)}
            </select>
          </div>
          <div className="flex flex-col justify-end rounded-lg bg-brand-50 px-4 py-2">
            <p className="text-xs text-brand-800">Total expenditure (filtered)</p>
            <p className="text-lg font-semibold text-brand-900">{data ? formatCurrency(data.total_expenditure) : '—'}</p>
          </div>
        </div>

        {loading && !data ? (
          <LoadingSpinner />
        ) : error ? (
          <ErrorState message={error} onRetry={reload} />
        ) : data.purchases.length === 0 ? (
          <EmptyState icon={Receipt} title="No purchases found" message={items?.length ? 'Record a purchase to start building your spending history.' : 'Add items to your catalogue first.'} />
        ) : (
          <>
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th scope="col">Date</th>
                    <th scope="col">Item</th>
                    <th scope="col">Quantity</th>
                    <th scope="col">Unit price</th>
                    <th scope="col">Total</th>
                    <th scope="col">Store</th>
                    <th scope="col" className="text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {data.purchases.map((p) => (
                    <tr key={p.id}>
                      <td className="whitespace-nowrap text-slate-600">{formatDate(p.purchase_date)}</td>
                      <td>
                        <p className="font-medium text-slate-900">{p.item_name}</p>
                        <div className="mt-0.5 flex gap-1">
                          {p.recommendation_item_id && <Badge tone="green">From plan</Badge>}
                          {!p.applied_to_inventory && <Badge>History only</Badge>}
                        </div>
                      </td>
                      <td className="whitespace-nowrap">{formatQuantity(p.quantity, p.unit)}</td>
                      <td className="whitespace-nowrap">{formatCurrency(p.unit_price)}</td>
                      <td className="whitespace-nowrap font-medium">{formatCurrency(p.total_price)}</td>
                      <td className="text-slate-600">{p.store_name || '—'}</td>
                      <td>
                        <div className="flex justify-end gap-1">
                          <button type="button" className="icon-btn" onClick={() => { setEditing(p); setFormOpen(true) }} aria-label={`Edit purchase of ${p.item_name}`}><Pencil className="h-4 w-4" /></button>
                          <button type="button" className="icon-btn hover:text-red-600" onClick={() => setDeleting(p)} aria-label={`Delete purchase of ${p.item_name}`}><Trash2 className="h-4 w-4" /></button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination pagination={data.pagination} onPageChange={(page) => setFilters((f) => ({ ...f, page }))} />
          </>
        )}
      </div>

      <PurchaseForm open={formOpen} purchase={editing} items={items || []} onClose={() => setFormOpen(false)} onSaved={() => { setFormOpen(false); reload() }} />

      <ConfirmDialog
        open={!!deleting}
        title="Delete this purchase?"
        danger
        busy={busy}
        confirmLabel="Delete"
        onCancel={() => setDeleting(null)}
        onConfirm={confirmDelete}
        message={deleting && (
          <p>
            {formatQuantity(deleting.quantity, deleting.unit)} of <strong>{deleting.item_name}</strong> will be removed from history
            {deleting.applied_to_inventory ? ' and subtracted from your inventory.' : '.'}
            {deleting.recommendation_item_id && ' The matching shopping-list item will be marked as not purchased.'}
          </p>
        )}
      />
    </>
  )
}
