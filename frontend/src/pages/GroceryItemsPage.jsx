import { useState } from 'react'
import toast from 'react-hot-toast'
import { Plus, Search, Tags } from 'lucide-react'
import { getErrorMessage } from '../api/axios'
import { createGrocery, deleteGrocery, fetchGroceries, fetchGrocery, updateGrocery } from '../api/groceryApi'
import ConfirmDialog from '../components/common/ConfirmDialog'
import EmptyState from '../components/common/EmptyState'
import ErrorState from '../components/common/ErrorState'
import LoadingSpinner from '../components/common/LoadingSpinner'
import PageHeader from '../components/common/PageHeader'
import Pagination from '../components/common/Pagination'
import GroceryForm from '../components/grocery/GroceryForm'
import GroceryTable from '../components/grocery/GroceryTable'
import { useApi } from '../hooks/useApi'
import { useOptions } from '../hooks/useOptions'

export default function GroceryItemsPage() {
  const options = useOptions()
  const [filters, setFilters] = useState({ search: '', category: '', priority: '', sort: 'name', include_archived: false, page: 1 })
  const { data, loading, error, reload } = useApi(() => fetchGroceries({ ...filters, per_page: 15 }), [filters])
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [deleting, setDeleting] = useState(null) // { item, related }
  const [busy, setBusy] = useState(false)

  const setFilter = (name, value) => setFilters((f) => ({ ...f, [name]: value, page: 1 }))

  const openAdd = () => {
    setEditing(null)
    setFormOpen(true)
  }

  const handleSave = async (payload) => {
    try {
      if (editing) {
        await updateGrocery(editing.id, payload)
        toast.success('Item updated.')
      } else {
        const result = await createGrocery(payload)
        toast.success(result.message)
      }
      setFormOpen(false)
      reload()
    } catch (err) {
      throw getErrorMessage(err)
    }
  }

  const askDelete = async (item) => {
    try {
      const { item: detail } = await fetchGrocery(item.id)
      setDeleting({ item, related: detail.related_counts })
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  const confirmDelete = async () => {
    setBusy(true)
    try {
      const result = await deleteGrocery(deleting.item.id)
      toast.success(result.message)
      setDeleting(null)
      reload()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const handleRestore = async (item) => {
    try {
      await updateGrocery(item.id, { ...item, is_archived: false })
      toast.success(`${item.name} restored.`)
      reload()
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  const relatedTotal = deleting ? Object.values(deleting.related).reduce((a, b) => a + b, 0) : 0

  return (
    <>
      <PageHeader
        title="Grocery catalogue"
        description="Items your household buys, with current ₹ prices and priority."
        actions={<button type="button" className="btn btn-primary" onClick={openAdd} disabled={!options}><Plus className="h-4 w-4" /> Add item</button>}
      />

      <div className="card">
        <div className="grid gap-3 border-b border-slate-100 p-4 sm:grid-cols-2 lg:grid-cols-5">
          <div className="relative lg:col-span-2">
            <label htmlFor="search" className="sr-only">Search items</label>
            <Search className="pointer-events-none absolute top-2.5 left-3 h-4 w-4 text-slate-400" aria-hidden="true" />
            <input id="search" className="input pl-9" placeholder="Search by name…" value={filters.search} onChange={(e) => setFilter('search', e.target.value)} />
          </div>
          <select aria-label="Filter by category" className="input" value={filters.category} onChange={(e) => setFilter('category', e.target.value)}>
            <option value="">All categories</option>
            {options?.categories.map((c) => <option key={c}>{c}</option>)}
          </select>
          <select aria-label="Filter by priority" className="input" value={filters.priority} onChange={(e) => setFilter('priority', e.target.value)}>
            <option value="">All priorities</option>
            {options?.priorities.map((p) => <option key={p}>{p}</option>)}
          </select>
          <select aria-label="Sort" className="input" value={filters.sort} onChange={(e) => setFilter('sort', e.target.value)}>
            <option value="name">Sort: Name</option>
            <option value="category">Sort: Category</option>
            <option value="price_asc">Sort: Price (low–high)</option>
            <option value="price_desc">Sort: Price (high–low)</option>
            <option value="newest">Sort: Newest</option>
          </select>
          <label className="flex items-center gap-2 text-sm text-slate-600 lg:col-span-5">
            <input type="checkbox" className="h-4 w-4 accent-brand-700" checked={filters.include_archived} onChange={(e) => setFilter('include_archived', e.target.checked)} />
            Show archived items
          </label>
        </div>

        {loading && !data ? (
          <LoadingSpinner />
        ) : error ? (
          <ErrorState message={error} onRetry={reload} />
        ) : data.items.length === 0 ? (
          <EmptyState
            icon={Tags}
            title={filters.search || filters.category || filters.priority ? 'No matching items' : 'Your catalogue is empty'}
            message="Add the groceries your household regularly buys, like rice, dal, oil and vegetables."
            action={<button type="button" className="btn btn-primary" onClick={openAdd}><Plus className="h-4 w-4" /> Add your first item</button>}
          />
        ) : (
          <>
            <GroceryTable items={data.items} onEdit={(item) => { setEditing(item); setFormOpen(true) }} onDelete={askDelete} onRestore={handleRestore} />
            <Pagination pagination={data.pagination} onPageChange={(page) => setFilters((f) => ({ ...f, page }))} />
          </>
        )}
      </div>

      {options && <GroceryForm open={formOpen} item={editing} options={options} onClose={() => setFormOpen(false)} onSave={handleSave} />}

      <ConfirmDialog
        open={!!deleting}
        title={relatedTotal ? 'Archive this item?' : 'Delete this item?'}
        danger
        busy={busy}
        confirmLabel={relatedTotal ? 'Archive item' : 'Delete item'}
        onCancel={() => setDeleting(null)}
        onConfirm={confirmDelete}
        message={
          deleting &&
          (relatedTotal ? (
            <>
              <p><strong>{deleting.item.name}</strong> has {deleting.related.purchases} purchase(s), {deleting.related.consumption} consumption record(s) and appears in {deleting.related.plans} plan(s).</p>
              <p className="mt-2">To keep your history intact it will be <strong>archived</strong> (hidden from lists and new plans) rather than deleted. You can restore it later.</p>
            </>
          ) : (
            <p><strong>{deleting.item.name}</strong> has no history and will be permanently deleted.</p>
          ))
        }
      />
    </>
  )
}
