
import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { getAIShoppingRecommendations } from '../../api/aiApi'
import { getErrorMessage } from '../../api/axios'

export default function AIShoppingRecommendations() {
    const [recommendations, setRecommendations] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const handleGenerate = async () => {
        try {
            setLoading(true)
            setError('')

            const data = await getAIShoppingRecommendations()
            setRecommendations(data.recommendations)
        } catch (err) {
            setError(getErrorMessage(err))
        } finally {
            setLoading(false)
        }
    }

    return (
        <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-md transition-shadow hover:shadow-lg">

            {/* Header */}
            <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
                <div>
                    <h2 className="flex items-center gap-2 text-xl font-bold text-gray-900">
                        <span className="rounded-lg bg-indigo-100 p-2 text-indigo-600">
                            ✨
                        </span>
                        AI Shopping Assistant
                    </h2>

                    <p className="mt-1 text-sm text-gray-500">
                        Personalised shopping priorities based on your ML plan and inventory.
                    </p>
                </div>

                <button
                    onClick={handleGenerate}
                    disabled={loading}
                    className="flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-800 disabled:cursor-not-allowed disabled:opacity-60"
                >
                    {loading ? (
                        <>
                            <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                            Analysing...
                        </>
                    ) : (
                        'Generate Recommendations'
                    )}
                </button>
            </div>

            {/* Error */}
            {error && (
                <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
                    {error}
                </div>
            )}

            {/* Recommendations */}
            {recommendations ? (
                <div className="prose prose-sm max-w-none
    prose-headings:text-gray-900
    prose-p:leading-7 prose-p:text-gray-600
    prose-li:text-gray-600
    prose-strong:text-gray-900
    prose-table:w-full prose-table:border-collapse
    prose-th:border prose-th:border-gray-200 prose-th:bg-gray-50 prose-th:p-3
    prose-td:border prose-td:border-gray-200 prose-td:p-3">

                    <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                            br: () => <br />,
                        }}
                    >
                        {recommendations}
                    </ReactMarkdown>
                </div>
            ) : (
                !loading && !error && (
                    <div className="rounded-xl border border-dashed border-indigo-200 bg-indigo-50/50 p-8 text-center">
                        <div className="mb-3 text-4xl">🛒</div>

                        <p className="font-semibold text-gray-800">
                            Your AI shopping assistant is ready!
                        </p>

                        <p className="mx-auto mt-2 max-w-md text-sm text-gray-500">
                            Generate personalised shopping priorities, budget advice and inventory insights using your latest saved grocery plan.
                        </p>
                    </div>
                )
            )}

        </section>
    )
}
