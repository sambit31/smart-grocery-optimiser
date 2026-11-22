import {
  BarChart3,
  Boxes,
  Home,
  LayoutDashboard,
  ListChecks,
  MessageSquare,
  Receipt,
  Sparkles,
  Tags,
  Utensils,
  Wallet,
} from 'lucide-react'

// Grouped in the order of the app's workflow.
export const NAV_GROUPS = [
  {
    label: 'Overview',
    items: [{ to: '/app', label: 'Dashboard', icon: LayoutDashboard, end: true }],
  },
  {
    label: 'Your data',
    items: [
      { to: '/app/household', label: 'Household', icon: Home },
      { to: '/app/groceries', label: 'Grocery Catalogue', icon: Tags },
      { to: '/app/inventory', label: 'Inventory', icon: Boxes },
      { to: '/app/purchases', label: 'Purchase History', icon: Receipt },
      { to: '/app/consumption', label: 'Consumption', icon: Utensils },
    ],
  },
  {
    label: 'Planning',
    items: [
      { to: '/app/predictions', label: 'Predictions', icon: Sparkles },
      { to: '/app/budget', label: 'Budget Optimisation', icon: Wallet },
      { to: '/app/shopping-list', label: 'Shopping List', icon: ListChecks },
    ],
  },
  {
    label: 'Insights',
    items: [
      { to: '/app/reports', label: 'Reports', icon: BarChart3 },
      { to: '/app/feedback', label: 'Feedback', icon: MessageSquare },
    ],
  },
]
