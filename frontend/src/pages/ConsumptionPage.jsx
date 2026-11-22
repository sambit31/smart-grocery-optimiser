import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Pencil, Trash2, Utensils } from 'lucide-react'
import { getErrorMessage } from '../api/axios'
import { createConsumption, deleteConsumption, fetchConsumption, updateConsumption } from '../api/consumptionApi'
import { fetchAllGroceries } from '../api/groceryApi'
import { fetchConsumptionReport } from '../api/reportApi'
import Badge from '../components/common/Badge'
import ConfirmDialog from '../components/common/ConfirmDialog'
import EmptyState from '../components/common/EmptyState'
import ErrorState from '../components/common/ErrorState'
import LoadingSpinner from '../components/common/LoadingSpinner'
import PageHeader from '../components/common/PageHeader'
import Pagination from '../components/common/Pagination'
import ConsumptionChart from '../components/charts/ConsumptionChart'
import { useApi } from '../hooks/useApi'
import { formatDate, formatQuantity, todayISO, unitStep } from '../utils/formatQuantity'

const EMPTY_FORM = { item_id: '', quantity: '', consumed_at: todayISO(), notes: '', deduct_from_stock: true }

export default function ConsumptionPage() {
  const { data: items } = useApi(fetchAllGroceries)
  const [filters, setFilters] = useState({ item_id: '', start_date: '', end_date: '', page: 1 })
  const { data, loading, error, reload } = useApi(() => fetchConsumption({ ...filters, per_page: 15 }), [filters])
  const [form, setForm] = useState(EMPTY_FORM)
  const [editingId, setEditingId] = useState(null)
  const [formError, setFormError] = useState('')
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(null)
  const [trendItem, setTrendItem] = useState('')
  const { data: trend, reload: reloadTrend } = useApi(
    () => (trendItem ? fetchConsumptionReport({ item_id: trendItem, months: 6 }) : Promise.resolve(null)),
    [trendItem],
  )

  useEffect(() => {
    if (items?.length && !form.item_id) setForm((f) => ({ ...f, item_id: items[0].id }))
    if (items?.length && !trendItem) setTrendItem(String(items[0].id))
  }, [items]) // eslint-disable-line react-hooks/exhaustive-deps

  const selected = items?.find((i) => String(i.id) === String(form.item_id))
  const handleChange = (event) => {
    const { name, value, type, checked } = event.target
    setForm({ ...form, [name]: type === 'checkbox' ? checked : value })
  }

  const resetForm = () => {
    setEditingId(null)
    setForm({ ...EMPTY_FORM, item_id: items?.[0]?.id || '', consumed_at: todayISO() })
    setFormError('')
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setFormError('')
    if (!form.item_id) return setFormError('Please choose an item.')
    if (!(Number(form.quantity) > 0)) return setFormError('Quantity must be greater than zero.')
    if (!form.consumed_at || form.consumed_at > todayISO()) return setFormError('Choose a date that is not in the future.')
    const payload = {
      item_id: Number(form.item_id),
      quantity: Number(form.quantity),
      consumed_at: form.consumed_at,
      notes: form.notes.trim() || null,
    }
    setSaving(true)
    try {
      if (editingId) {
        await updateConsumption(editingId, payload)
        toast.success('Consumption updated.')
      } else {
        await createConsumption({ ...payload, deduct_from_stock: form.deduct_from_stock })
        toast.success(form.deduct_from_stock ? 'Consumption recorded and stock reduced.' : 'Consumption recorded.')
      }
      resetForm()
      reload()
      reloadTrend()
    } catch (err) {
      setFormError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const startEdit = (record) => {
    setEditingId(record.id)
    setForm({ item_id: record.item_id, quantity: record.quantity, consumed_at: record.consumed_at, notes: record.notes || '', deduct_from_stock: record.deducted_from_stock })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const confirmDelete = async () => {
    try {
      await deleteConsumption(deleting.id)
      toast.success('Record deleted.')
      setDeleting(null)
      reload()
      reloadTrend()
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  const trendData = trend?.trend
  const trendHasData = trendData?.months.some((m) => m.quantity > 0)

  return (
    <>
      <PageHeader title="Consumption tracking" description="How much your household actually uses. This is the main input for predictions." />

      <div className="grid gap-6 lg:grid-cols-5">
        <form onSubmit={handleSubmit} className="card space-y-4 p-5 lg:col-span-2" noValidate>
          <h2 className="font-semibold text-slate-900">{editingId ? 'Edit record' : 'Record consumption'}</h2>
          {formError && <div role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{formError}</div>}
          {!items?.length ? (
            <p className="text-sm text-slate-500">Add items to your catalogue first.</p>
          ) : (
            <>
              <div>
                <label htmlFor="c-item" className="label">Item</label>
                <select id="c-item" name="item_id" className="input" value={form.item_id} onChange={handleChange}>
                  {items.map((i) => <option key={i.id} value={i.id}>{i.name} ({i.unit}) — {formatQuantity(i.current_stock, i.unit)} in stock</option>)}
                </select>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label htmlFor="c-qty" className="label">Quantity used {selected && `(${selected.unit})`}</label>
                  <input id="c-qty" name="quantity" type="number" min="0" step={unitStep(selected?.unit) === '1' ? '1' : 'any'} className="input" value={form.quantity} onChange={handleChange} />
                </div>
                <div>
                  <label htmlFor="c-date" className="label">Date</label>
                  <input id="c-date" name="consumed_at" type="date" max={todayISO()} className="input" value={form.consumed_at} onChange={handleChange} />
                </div>
              </div>
              <div>
                <label htmlFor="c-notes" className="label">Notes — optional</label>
                <input id="c-notes" name="notes" className="input" value={form.notes} onChange={handleChange} maxLength={500} placeholder="e.g. guests over the weekend" />
              </div>
              {!editingId && (
                <label className="flex items-start gap-2 text-sm text-slate-700">
                  <input type="checkbox" name="deduct_from_stock" className="mt-0.5 h-4 w-4 accent-brand-700" checked={form.deduct_from_stock} onChange={handleChange} />
                  <span>Subtract from inventory <span className="block text-xs text-slate-500">Untick when entering past usage whose stock you have already counted.</span></span>
                </label>
              )}
              <div className="flex gap-2">
                <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Saving…' : editingId ? 'Update' : 'Add record'}</button>
                {editingId && <button type="button" className="btn btn-secondary" onClick={resetForm}>Cancel</button>}
              </div>
            </>
          )}
        </form>

        <section className="card p-5 lg:col-span-3">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="font-semibold text-slate-900">Monthly trend</h2>
            <select aria-label="Item for trend chart" className="input w-auto" value={trendItem} onChange={(e) => setTrendItem(e.target.value)}>
              {items?.map((i) => <option key={i.id} value={i.id}>{i.name}</option>)}
            </select>
          </div>
          <div className="mt-4">
            {trendHasData ? (
              <ConsumptionChart data={trendData.months} unit={trendData.unit} />
            ) : (
              <EmptyState compact icon={Utensils} title="No consumption for this item yet" message="Records you add will appear here by month." />
            )}
          </div>
        </section>
      </div>

      <section className="card mt-6">
        <div className="grid gap-3 border-b border-slate-100 p-4 sm:grid-cols-3">
          <select aria-label="Filter by item" className="input" value={filters.item_id} onChange={(e) => setFilters({ ...filters, item_id: e.target.value, page: 1 })}>
            <option value="">All items</option>
            {items?.map((i) => <option key={i.id} value={i.id}>{i.name}</option>)}
          </select>
          <input aria-label="From date" type="date" className="input" value={filters.start_date} onChange={(e) => setFilters({ ...filters, start_date: e.target.value, page: 1 })} />
          <input aria-label="To date" type="date" className="input" value={filters.end_date} onChange={(e) => setFilters({ ...filters, end_date: e.target.value, page: 1 })} />
        </div>
        {loading && !data ? (
          <LoadingSpinner />
        ) : error ? (
          <ErrorState message={error} onRetry={reload} />
        ) : data.consumption.length === 0 ? (
          <EmptyState icon={Utensils} title="No consumption records" message="Without history, predictions fall back to your own estimates (clearly labelled)." />
        ) : (
          <>
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th scope="col">Date</th>
                    <th scope="col">Item</th>
                    <th scope="col">Quantity</th>
                    <th scope="col">Notes</th>
                    <th scope="col" className="text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {data.consumption.map((c) => (
                    <tr key={c.id}>
                      <td className="whitespace-nowrap text-slate-600">{formatDate(c.consumed_at)}</td>
                      <td>
                        <span className="font-medium text-slate-900">{c.item_name}</span>
                        {!c.deducted_from_stock && <span className="ml-2"><Badge>History only</Badge></span>}
                      </td>
                      <td className="whitespace-nowrap">{formatQuantity(c.quantity, c.unit)}</td>
                      <td className="max-w-xs truncate text-slate-500">{c.notes || '—'}</td>
                      <td>
                        <div className="flex justify-end gap-1">
                          <button type="button" className="icon-btn" onClick={() => startEdit(c)} aria-label={`Edit record for ${c.item_name}`}><Pencil className="h-4 w-4" /></button>
                          <button type="button" className="icon-btn hover:text-red-600" onClick={() => setDeleting(c)} aria-label={`Delete record for ${c.item_name}`}><Trash2 className="h-4 w-4" /></button>
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
      </section>

      <ConfirmDialog
        open={!!deleting}
        title="Delete this record?"
        danger
        confirmLabel="Delete"
        onCancel={() => setDeleting(null)}
        onConfirm={confirmDelete}
        message={deleting && (
          <p>
            {formatQuantity(deleting.quantity, deleting.unit)} of <strong>{deleting.item_name}</strong> will be removed
            {deleting.deducted_from_stock ? ' and added back to your inventory.' : '.'}
          </p>
        )}
      />
    </>
  )
}
