import { useState } from 'react'
import toast from 'react-hot-toast'
import { MessageSquare, Star } from 'lucide-react'
import { getErrorMessage } from '../api/axios'
import { fetchFeedback, submitFeedback } from '../api/feedbackApi'
import EmptyState from '../components/common/EmptyState'
import ErrorState from '../components/common/ErrorState'
import LoadingSpinner from '../components/common/LoadingSpinner'
import PageHeader from '../components/common/PageHeader'
import { useApi } from '../hooks/useApi'
import { formatDate } from '../utils/formatQuantity'

const LABELS = ['', 'Poor', 'Fair', 'Good', 'Very good', 'Excellent']

function Stars({ value, size = 'h-4 w-4' }) {
  return (
    <span className="flex" aria-label={`${value} out of 5 stars`}>
      {[1, 2, 3, 4, 5].map((n) => (
        <Star key={n} className={`${size} ${n <= value ? 'fill-amber-400 text-amber-400' : 'text-slate-300'}`} aria-hidden="true" />
      ))}
    </span>
  )
}

export default function FeedbackPage() {
  const { data, loading, error, reload } = useApi(fetchFeedback)
  const [rating, setRating] = useState(0)
  const [hover, setHover] = useState(0)
  const [comment, setComment] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (rating < 1 || rating > 5) return toast.error('Please choose a rating from 1 to 5.')
    setSubmitting(true)
    try {
      const result = await submitFeedback({ rating, comment: comment.trim() || null })
      toast.success('Thank you for your feedback!')
      setRating(0)
      setComment('')
      reload()
      return result
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <PageHeader title="Feedback" description="Tell us how useful the recommendations are." />
      <div className="grid gap-6 lg:grid-cols-2">
        <form onSubmit={handleSubmit} className="card space-y-4 p-5">
          <fieldset>
            <legend className="label">Your rating</legend>
            <div className="flex items-center gap-1" onMouseLeave={() => setHover(0)}>
              {[1, 2, 3, 4, 5].map((n) => (
                <button
                  key={n}
                  type="button"
                  className="rounded p-1"
                  onClick={() => setRating(n)}
                  onMouseEnter={() => setHover(n)}
                  aria-label={`${n} star${n > 1 ? 's' : ''} — ${LABELS[n]}`}
                  aria-pressed={rating === n}
                >
                  <Star className={`h-7 w-7 transition-colors ${n <= (hover || rating) ? 'fill-amber-400 text-amber-400' : 'text-slate-300'}`} />
                </button>
              ))}
              <span className="ml-2 text-sm text-slate-500">{LABELS[hover || rating]}</span>
            </div>
          </fieldset>
          <div>
            <label htmlFor="comment" className="label">Comment — optional</label>
            <textarea id="comment" rows={4} className="input" value={comment} onChange={(e) => setComment(e.target.value)} maxLength={1000} placeholder="What worked well? What could be better?" />
            <p className="help-text">{comment.length}/1000</p>
          </div>
          <button type="submit" className="btn btn-primary" disabled={submitting}>{submitting ? 'Submitting…' : 'Submit feedback'}</button>
        </form>

        <section className="card">
          <h2 className="border-b border-slate-100 px-5 py-3.5 text-sm font-semibold text-slate-900">Your previous feedback</h2>
          {loading ? (
            <LoadingSpinner />
          ) : error ? (
            <ErrorState message={error} onRetry={reload} />
          ) : data.feedback.length === 0 ? (
            <EmptyState compact icon={MessageSquare} title="No feedback yet" />
          ) : (
            <ul className="divide-y divide-slate-100">
              {data.feedback.map((f) => (
                <li key={f.id} className="px-5 py-3.5">
                  <div className="flex items-center justify-between">
                    <Stars value={f.rating} />
                    <span className="text-xs text-slate-400">{formatDate(f.created_at)}</span>
                  </div>
                  {f.comment && <p className="mt-1.5 text-sm text-slate-600">{f.comment}</p>}
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </>
  )
}
