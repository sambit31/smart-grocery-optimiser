
import { useState } from 'react'
import { Sparkles, RefreshCw } from 'lucide-react'
import { getAIInsights } from '../../api/aiApi'
import { getErrorMessage } from '../../api/axios'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export default function AIInsights() {
  const [insights, setInsights] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleGenerate = async () => {
    setLoading(true)
    setError('')

    try {
      const result = await getAIInsights()
      setInsights(result.insights)
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to generate AI insights.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="card overflow-hidden">
      <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
        <div className="flex items-center gap-2">
          <div className="rounded-lg bg-violet-100 p-2 text-violet-700">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <h2 className="font-semibold text-slate-900">AI Grocery Insights</h2>
            <p className="text-xs text-slate-500">Smart analysis of your grocery data</p>
          </div>
        </div>

        <button
          type="button"
          onClick={handleGenerate}
          disabled={loading}
          className="btn btn-primary"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          {loading ? 'Analyzing...' : insights ? 'Refresh Insights' : 'Generate Insights'}
        </button>
      </div>

      <div className="p-5">
        {loading && (
          <p className="text-sm text-slate-500">
            AI is analyzing your grocery data...
          </p>
        )}

        {error && (
          <p className="text-sm text-red-600">{error}</p>
        )}

        {!loading && !error && !insights && (
          <p className="text-sm text-slate-500">
            Generate personalized spending insights, inventory suggestions
            and grocery recommendations.
          </p>
        )}

        {insights && !loading && (
         <ReactMarkdown remarkPlugins={[remarkGfm]}>
  {insights}
</ReactMarkdown>
        )}
      </div>
    </section>
  )
}
