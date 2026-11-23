import AIShoppingRecommendations from '../components/dashboard/AIShoppingRecommendations'

export default function AIShoppingRecommendationsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          AI Shopping Recommendations
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Smart grocery suggestions based on your inventory, consumption and shopping plan.
        </p>
      </div>

      <AIShoppingRecommendations />
    </div>
  )
}