import { useState } from 'react'
import toast from 'react-hot-toast'
import { Boxes, Plus, Search } from 'lucide-react'
import { getErrorMessage } from '../api/axios'
import { addInventory, adjustInventory, fetchInventory, updateInventory } from '../api/inventoryApi'
import EmptyState from '../components/common/EmptyState'
import ErrorState from '../components/common/ErrorState'
import LoadingSpinner from '../components/common/LoadingSpinner'
import Modal from '../components/common/Modal'
import PageHeader from '../components/common/PageHeader'
import InventoryForm from '../components/inventory/InventoryForm'
import InventoryTable from '../components/inventory/InventoryTable'
import { useApi } from '../hooks/useApi'
import { useOptions } from '../hooks/useOptions'
import { formatQuantity, unitStep } from '../utils/formatQuantity'

export default function InventoryPage() {
  const options = useOptions()
  const [filters, setFilters] = useState({ search: '', category: '', low_stock: false })
  const { data, loading, error, reload } = useApi(() => fetchInventory(filters), [filters])
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [adjusting, setAdjusting] = useState(null) // { record, direction }
  const [amount, setAmount] = useState('')
  const [saving, setSaving] = useState(false)

  const handleSave = async (payload) => {
    try {
      if (editing) {
        await updateInventory(editing.id, payload)
        toast.success('Inventory updated.')
      } else {
        await addInventory(payload)
        toast.success('Stock added.')
      }
      setFormOpen(false)
      reload()
    } catch (err) {
      throw getErrorMessage(err)
    }
  }

  const openAdjust = (record, direction) => {
    setAdjusting({ record, direction })
    setAmount('1')
  }

  const submitAdjust = async (event) => {
    event.preventDefault()
    if (!(Number(amount) > 0)) return toast.error('Enter an amount greater than zero.')
    setSaving(true)
    try {
      const change = Number(amount) * adjusting.direction
      await adjustInventory(adjusting.record.id, change, adjusting.direction > 0 ? 'manual_increase' : 'manual_decrease')
      toast.success('Stock adjusted.')
      setAdjusting(null)
      reload()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const untracked = data?.untracked_items || []

  return (
    <>
      <PageHeader
        title="Inventory"
        description="What you currently have at home. Purchases add stock and consumption removes it automatically."
        actions={
          <button type="button" className="btn btn-primary" disabled={!untracked.length} onClick={() => { setEditing(null); setFormOpen(true) }} title={untracked.length ? '' : 'All catalogue items are already tracked'}>
            <Plus className="h-4 w-4" /> Add stock
          </button>
        }
      />

      <div className="card">
        <div className="grid gap-3 border-b border-slate-100 p-4 sm:grid-cols-3">
          <div className="relative">
            <Search className="pointer-events-none absolute top-2.5 left-3 h-4 w-4 text-slate-400" aria-hidden="true" />
            <input aria-label="Search inventory" className="input pl-9" placeholder="Search by name…" value={filters.search} onChange={(e) => setFilters({ ...filters, search: e.target.value })} />
          </div>
          <select aria-label="Filter by category" className="input" value={filters.category} onChange={(e) => setFilters({ ...filters, category: e.target.value })}>
            <option value="">All categories</option>
            {options?.categories.map((c) => <option key={c}>{c}</option>)}
          </select>
          <label className="flex items-center gap-2 text-sm text-slate-600">
            <input type="checkbox" className="h-4 w-4 accent-brand-700" checked={filters.low_stock} onChange={(e) => setFilters({ ...filters, low_stock: e.target.checked })} />
            Show low-stock items only {data && `(${data.low_stock_count})`}
          </label>
        </div>

        {loading && !data ? (
          <LoadingSpinner />
        ) : error ? (
          <ErrorState message={error} onRetry={reload} />
        ) : data.inventory.length === 0 ? (
          <EmptyState
            icon={Boxes}
            title={filters.search || filters.category || filters.low_stock ? 'No matching stock' : 'No stock recorded yet'}
            message={untracked.length ? 'Record how much of each item you have at home right now.' : 'Add items to your grocery catalogue first.'}
          />
        ) : (
          <InventoryTable records={data.inventory} onAdjust={openAdjust} onEdit={(r) => { setEditing(r); setFormOpen(true) }} />
        )}
      </div>

      <InventoryForm open={formOpen} record={editing} untrackedItems={untracked} onClose={() => setFormOpen(false)} onSave={handleSave} />

      <Modal
        open={!!adjusting}
        size="sm"
        title={adjusting ? `${adjusting.direction > 0 ? 'Increase' : 'Decrease'} ${adjusting.record.item_name}` : ''}
        onClose={() => setAdjusting(null)}
        footer={
          <>
            <button type="button" className="btn btn-secondary" onClick={() => setAdjusting(null)}>Cancel</button>
            <button type="submit" form="adjust-form" className="btn btn-primary" disabled={saving}>{saving ? 'Saving…' : 'Apply'}</button>
          </>
        }
      >
        {adjusting && (
          <form id="adjust-form" onSubmit={submitAdjust} className="space-y-3">
            <p className="text-sm text-slate-600">Current stock: <strong>{formatQuantity(adjusting.record.quantity, adjusting.record.unit)}</strong></p>
            <div>
              <label htmlFor="adjust-amount" className="label">Amount to {adjusting.direction > 0 ? 'add' : 'remove'} ({adjusting.record.unit})</label>
              <input id="adjust-amount" type="number" min="0" step={unitStep(adjusting.record.unit) === '1' ? '1' : 'any'} className="input" value={amount} onChange={(e) => setAmount(e.target.value)} />
            </div>
            <p className="text-xs text-slate-500">For bought or used groceries, prefer recording a purchase or consumption so your history stays accurate.</p>
          </form>
        )}
      </Modal>
    </>
  )
}
