import { Route, Routes } from 'react-router-dom'
import ProtectedRoute from './components/layout/ProtectedRoute'
import AuthLayout from './layouts/AuthLayout'
import DashboardLayout from './layouts/DashboardLayout'
import BudgetOptimisationPage from './pages/BudgetOptimisationPage'
import ConsumptionPage from './pages/ConsumptionPage'
import DashboardPage from './pages/DashboardPage'
import FeedbackPage from './pages/FeedbackPage'
import GroceryItemsPage from './pages/GroceryItemsPage'
import HouseholdPage from './pages/HouseholdPage'
import InventoryPage from './pages/InventoryPage'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import NotFoundPage from './pages/NotFoundPage'
import PredictionPage from './pages/PredictionPage'
import PurchaseHistoryPage from './pages/PurchaseHistoryPage'
import RegisterPage from './pages/RegisterPage'
import ReportsPage from './pages/ReportsPage'
import ShoppingListPage from './pages/ShoppingListPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />

      <Route element={<AuthLayout />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route path="/app" element={<DashboardLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="household" element={<HouseholdPage />} />
          <Route path="groceries" element={<GroceryItemsPage />} />
          <Route path="inventory" element={<InventoryPage />} />
          <Route path="purchases" element={<PurchaseHistoryPage />} />
          <Route path="consumption" element={<ConsumptionPage />} />
          <Route path="predictions" element={<PredictionPage />} />
          <Route path="budget" element={<BudgetOptimisationPage />} />
          <Route path="shopping-list" element={<ShoppingListPage />} />
          <Route path="reports" element={<ReportsPage />} />
          <Route path="feedback" element={<FeedbackPage />} />
        </Route>
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
