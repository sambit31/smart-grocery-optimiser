# Smart AI-Based Grocery List Optimiser for Indian Households

**GrocerySmart** is a full-stack web application that helps an Indian household plan its grocery shopping. It predicts what the household will need from its own consumption history, subtracts what is already in stock, checks the cost against the monthly budget, and produces an interactive shopping checklist.

```
Household details → Purchases & inventory → Consumption prediction → Stock adjustment → Budget optimisation → Final grocery list
```

> **About the “AI”.** The prediction is a transparent **simple moving average** of the household's real consumption, not a trained ML model. This is deliberate: it is explainable, it works with small amounts of data, and every number can be traced back to records in the database. See [Known limitations](#known-limitations) and [Future enhancements](#future-enhancements).

---

## Contents

1. [Key features](#key-features)
2. [Technology stack](#technology-stack)
3. [Architecture](#architecture)
4. [Folder structure](#folder-structure)
5. [Database schema](#database-schema)
6. [How the core logic works](#how-the-core-logic-works)
7. [Setup on Windows (step by step)](#setup-on-windows-step-by-step)
8. [Running the app](#running-the-app)
9. [Sample demonstration workflow](#sample-demonstration-workflow)
10. [API endpoint summary](#api-endpoint-summary)
11. [Tests](#tests)
12. [Security](#security)
13. [Troubleshooting](#troubleshooting)
14. [Known limitations](#known-limitations)
15. [Future enhancements](#future-enhancements)

---

## Key features

| Module | What it does |
|---|---|
| **Authentication** | Register, log in, log out. Passwords are hashed. JWT is kept in an HttpOnly cookie with CSRF protection. |
| **Household** | Family size, shopping frequency, monthly budget and planning period. One household per user. |
| **Grocery catalogue** | Add, edit, delete, search, filter, sort and paginate items with ₹ prices and a priority (Essential / Important / Optional). Items with history are **archived**, not deleted. |
| **Inventory** | Current stock per item, low-stock alerts, expiry dates, and increase/decrease controls. Stock can never go negative, and every change is logged. |
| **Purchase history** | Record, edit and delete purchases, with date and item filters and total expenditure. Purchases add to stock in the same database transaction. Duplicate submissions are blocked. |
| **Consumption** | Record what the household uses. This is the main input for prediction. Records reduce stock, and edits or deletes reverse exactly what was applied. |
| **Prediction** | Averages recent 30-day consumption totals, then calculates `buy = max(0, predicted − stock)`. Items without history fall back to the user's own *labelled* estimate, or are marked “Needs data”. |
| **Budget optimisation** | A deterministic, rule-based pass: Optional items are cut first, then Important. Essential items are never cut silently. Every adjustment is explained. |
| **Shopping list** | A mobile-friendly checklist grouped by category. You can edit quantities (totals recalculate), see why each quantity was recommended, and keep a history of saved plans. Ticking a box **does not** record a purchase; a separate, confirmed “Bought” action does. |
| **Dashboard & reports** | Live statistics, spending vs budget, spending by category, consumption trends, predicted vs purchased, and plan history. Every figure comes from the database. |
| **Feedback** | 1–5 star rating with an optional comment, validated on the server. |

---

## Technology stack

| Layer | Technology |
|---|---|
| Frontend | React 19 + Vite, JavaScript, Tailwind CSS v4, React Router, Axios, Lucide icons, Recharts, React Hot Toast |
| Backend | Python 3.11+ and Flask 3 with Flask-SQLAlchemy, Flask-Migrate, Flask-JWT-Extended, Flask-CORS and Flask-Limiter; Werkzeug password hashing; Pandas/NumPy |
| Database | MySQL 8 (via PyMySQL) |
| Tests | pytest. The suite runs on an isolated in-memory database by default and can also run against a MySQL test database. |

Scikit-learn is **not** included because no ML model is used (see [Future enhancements](#future-enhancements)).

---

## Architecture

```mermaid
flowchart LR
    subgraph Browser
        UI[React pages<br/>+ components] --> AX[Axios client<br/>cookie + CSRF header]
    end
    AX -- "/api/* (Vite proxy in dev)" --> R

    subgraph Flask backend
        R[Routes / Blueprints<br/>validation + ownership checks] --> S[Services<br/>prediction · budget · inventory<br/>purchase · recommendation · report]
        S --> M[SQLAlchemy models]
    end
    M --> DB[(MySQL)]
```

Each layer has one job:

- **Routes** (`app/routes/`) read and validate the request, check the user owns the record, call a service, commit, and return JSON.
- **Services** (`app/services/`) hold all business rules: the prediction maths, budget rules and stock changes. Every calculation lives in exactly one place.
- **Models** (`app/models/`) define the tables.

Every response has the same shape:

```json
{ "success": true,  "message": "Item added.", "data": { ... } }
{ "success": false, "message": "Quantity must be zero or greater." }
```

---

## Folder structure

```
smart-grocery-optimiser/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # app factory, error handlers, CLI commands
│   │   ├── config.py            # settings from .env
│   │   ├── constants.py         # categories, units, priorities (single source)
│   │   ├── extensions.py        # db, jwt, cors, limiter, migrate
│   │   ├── demo_data.py         # DEMONSTRATION data for `flask seed-demo`
│   │   ├── models/              # user, household, grocery_item, inventory (+ stock_movements),
│   │   │                        # purchase, consumption, recommendation (+ items), feedback
│   │   ├── routes/              # auth, household, grocery, inventory, purchase, consumption,
│   │   │                        # prediction, budget, dashboard (+ reports), feedback
│   │   ├── services/            # prediction, budget, inventory, purchase, recommendation, report
│   │   └── utils/               # validators, decorators (auth/ownership), responses, numbers
│   ├── migrations/              # Flask-Migrate (Alembic) schema migrations
│   ├── scripts/export_seed_sql.py
│   ├── tests/                   # conftest.py, test_calculations.py, test_api.py
│   ├── run.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/                 # one file per backend area; axios.js adds CSRF header
│   │   ├── components/          # layout/, common/, grocery/, inventory/, shopping/, charts/
│   │   ├── context/AuthContext.jsx
│   │   ├── hooks/               # useApi (loading/error state), useOptions
│   │   ├── layouts/             # DashboardLayout, AuthLayout
│   │   ├── pages/               # one file per screen
│   │   ├── utils/               # formatCurrency (₹, Indian grouping), formatQuantity
│   │   ├── App.jsx  main.jsx  index.css
│   ├── vite.config.js           # /api proxy → Flask :5000
│   └── .env.example
├── database/
│   ├── schema.sql               # full MySQL schema (alternative to migrations)
│   └── seed_data.sql            # DEMONSTRATION data with dates relative to today
└── README.md
```

---

## Database schema

```mermaid
erDiagram
    users ||--|| households : owns
    households ||--o{ grocery_items : has
    households ||--o{ feedback : gives
    grocery_items ||--o| inventory : "stock of"
    grocery_items ||--o{ stock_movements : "audit log"
    grocery_items ||--o{ purchases : bought
    grocery_items ||--o{ consumption : used
    households ||--o{ recommendations : plans
    recommendations ||--o{ recommendation_items : contains
    recommendation_items |o--o| purchases : "mark purchased"
```

| Table | Purpose / notable columns |
|---|---|
| `users` | `email` is unique. Only `password_hash` is stored. |
| `households` | `user_id` is unique (one per user). `monthly_budget DECIMAL(12,2)`, `planning_period_days`. |
| `grocery_items` | Unique `(household_id, name)`. `unit_price DECIMAL(10,2)`, `priority`, optional `initial_monthly_estimate`, `is_archived`. |
| `inventory` | One row per item (unique `item_id`). `quantity DECIMAL(12,3)` with a `CHECK (quantity >= 0)`. Also `low_stock_threshold` and `expiry_date`. |
| `stock_movements` | Every stock change with its reason, e.g. `purchase`, `consumption`, `purchase_reversal`, `manual_set`. |
| `purchases` | `quantity`, `unit_price`, `total_price`, `purchase_date`, `applied_to_inventory`. Unique `client_reference` stops double submits. A unique `recommendation_item_id` stops a plan line being bought twice. |
| `consumption` | `quantity`, `consumed_at`, `deducted_from_stock` (so reversals are exact). |
| `recommendations` | Saved plan: period, budget, predicted and final cost, method, `status` (generated / optimised / completed), `budget_status`, and the explanation. |
| `recommendation_items` | Per-item `predicted`, `stock`, `recommended`, `final` quantity, cost, source, data sufficiency, reason, adjustment note, `is_checked`, `is_purchased`. |
| `feedback` | `rating` 1–5, enforced with a `CHECK` constraint and backend validation. |

All money uses `DECIMAL` and all quantities use `DECIMAL(12,3)`. Python handles them as `Decimal`, never float, until they are sent to the browser as JSON.

---

## How the core logic works

### 1. Prediction (`services/prediction_service.py`)

1. Consumption records are summed into **rolling 30-day periods**: period 1 is the last 30 days, period 2 is 31–60 days ago, and so on. The service always averages *period totals*; it never mixes daily values with monthly totals.
2. It looks back over the history window, which is 3 periods by default. This is configurable in `.env` (`PREDICTION_HISTORY_PERIODS`) and on the Predictions page.
3. Periods older than the item's first-ever record are ignored, because the household wasn't tracking the item then. Gaps *after* the first record count as zero use.
4. `predicted = average × planning_days ÷ 30`

**Worked example (the synopsis case):** monthly totals of 7, 8 and 9 kg give (7 + 8 + 9) ÷ 3 = **8 kg**.

**When there is no history:** the user's *Initial monthly estimate* is used and shown as **“Your estimate”**. If there is no estimate either, the item shows **“Needs data”** and nothing is recommended for it. No history is ever invented.

**Data sufficiency** is shown as a label, not a fake percentage: *Good* (full window), *Limited* (fewer periods), *Estimate*, or *No data*.

### 2. Stock adjustment

```
recommended_quantity = max(0, predicted_requirement − current_stock)
```

Example: rice predicted at 8 kg with 3 kg in stock gives **5 kg** to buy. A negative result is clamped to 0.

Items sold by `piece`, `packet`, `g` or `ml` are rounded **up** to whole units. Items in `kg` or `litre` are rounded up to 0.1.

### 3. Budget optimisation (`services/budget_service.py`)

The plan budget is the monthly budget × planning days ÷ 30.

1. If the total fits within the budget, nothing changes and the plan shows **“Within Budget”**.
2. If the total is over budget, **Optional** items are reduced first, then **Important** items.
3. Within each priority group, the most expensive line is reduced first, and only by as much as needed (in buying steps). The total is recalculated after every change.
4. **Essential items are protected.** If they alone exceed the budget, they are kept and the plan is marked **“Over Budget”**. The shortfall is reported, and the essentials that don't fit are flagged so the user can decide what to do.

Every change is written to the plan's explanation, for example: *“Namkeen: Removed (Optional): 4 packet dropped to save ₹220.00. New total ₹4,293.80.”*

The reduction order and the protected priorities are defined as two constants at the top of `budget_service.py`. This is a **rule-based** method, not mathematical optimisation, and the UI says so.

### 4. Keeping stock correct

- Purchases add stock and consumption removes it, both through `inventory_service.change_stock()`, which refuses to let stock go negative.
- Editing or deleting a purchase or consumption record **reverses** what it originally applied, then applies the new values.
- Each request commits **once**. Any error rolls back the whole transaction, so a purchase is never saved without its stock change.
- **Ticking** a shopping-list item changes nothing else. **“Bought”** records the purchase and updates stock. The database won't allow the same list line to be bought twice.

---

## Setup on Windows (step by step)

### Prerequisites

| Software | Version | Download |
|---|---|---|
| Python | 3.11 or newer (3.12 recommended) | <https://www.python.org/downloads/> (tick **“Add python.exe to PATH”**) |
| Node.js | 20 LTS or newer | <https://nodejs.org/> |
| MySQL Server | 8.x (Community, free) | <https://dev.mysql.com/downloads/installer/> |
| VS Code | any | <https://code.visualstudio.com/> |

Check them in **PowerShell**:

```powershell
python --version
node --version
npm --version
mysql --version     # if not found, see Troubleshooting
```

### 1. Create the MySQL database and user

Open **MySQL Command Line Client** or PowerShell (`mysql -u root -p`) and run the following. Choose your own password.

```sql
CREATE DATABASE smart_grocery CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE smart_grocery_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;  -- optional, for MySQL tests
CREATE USER 'grocery_user'@'localhost' IDENTIFIED BY 'YourStrongPassword1';
GRANT ALL PRIVILEGES ON smart_grocery.* TO 'grocery_user'@'localhost';
GRANT ALL PRIVILEGES ON smart_grocery_test.* TO 'grocery_user'@'localhost';
FLUSH PRIVILEGES;
```

### 2. Backend setup

```powershell
cd smart-grocery-optimiser\backend

# Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1
#   If PowerShell blocks this script, run once:
#   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

pip install -r requirements.txt

# Create your .env from the template, then edit it
Copy-Item .env.example .env
notepad .env
```

In `.env`, set `MYSQL_PASSWORD` to the password from step 1, and replace both secret keys with long random strings. You can generate one with:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Create the tables. Pick **one** of these options:

```powershell
# Option A (recommended): run the migrations
flask --app run.py db upgrade

# Option B: load the SQL file
Get-Content ..\database\schema.sql | mysql -u grocery_user -p smart_grocery
```

Load the **demonstration** data (optional, but recommended for a viva):

```powershell
flask --app run.py seed-demo
# -> Demo data loaded. Log in with demo@grocery.local / Demo@1234
```

`seed-demo` can be run again at any time to reset the demo account. Alternatively, load the SQL version into an **empty** database:

```powershell
Get-Content ..\database\seed_data.sql | mysql -u grocery_user -p smart_grocery
```

### 3. Frontend setup

Open a **second** PowerShell window:

```powershell
cd smart-grocery-optimiser\frontend
npm install
Copy-Item .env.example .env
```

---

## Running the app

You need two terminals.

**Terminal 1: backend**

```powershell
cd smart-grocery-optimiser\backend
.\.venv\Scripts\Activate.ps1
python run.py
# Running on http://127.0.0.1:5000
```

**Terminal 2: frontend**

```powershell
cd smart-grocery-optimiser\frontend
npm run dev
# Local: http://localhost:5173/
```

Open **http://localhost:5173**. During development, Vite forwards every `/api` request to Flask, so the browser sees a single origin and the auth cookies work without extra setup.

To build an optimised frontend: `npm run build` (the output goes to `frontend/dist/`).

---

## Sample demonstration workflow

A viva walkthrough that takes about 10 minutes.

1. **Landing page**: show the features and the formula, then click **Get Started**.
2. **Log in** with `demo@grocery.local` / `Demo@1234`. This is demo data, clearly labelled `[DEMO DATA]`.
3. **Dashboard**: every figure is live (budget, spent this month, low-stock count, spending chart, consumption).
4. **Grocery catalogue**: search “dal”, filter by *Essential*, and edit a price. Try deleting *Basmati Rice*; the dialog explains it will be **archived** because it has history.
5. **Inventory**: show the low-stock badges, then use **+** to add 1 kg of rice.
6. **Consumption**: record 2 kg of Wheat Atta used today and watch its stock drop. Show the monthly trend chart.
7. **Predictions → Generate new plan**. Click **Why?** on *Basmati Rice* to show the period totals, the average and the stock subtraction. Point out *Desi Ghee* (**Your estimate**) and *Jaggery* (**Needs data**).
8. **Budget optimisation → Run optimisation**. The demo plan is about ₹500 over its ₹4,000 budget, so Namkeen, Biscuits and Garam Masala (Optional) are removed first, then Desi Ghee (Important) is trimmed. Essentials are untouched, and each step is explained.
9. **Shopping list**: tick a few items (no purchase is recorded), then edit a quantity and watch the total recalculate. Click **Bought** on one item and confirm. Check **Purchase History** (new entry, tagged “From plan”) and **Inventory** (stock increased).
10. **Reports**: spending vs budget, by category, predicted vs purchased, and plan history.
11. **Feedback**: submit a rating.

To show a brand-new user, register a fresh account. The guided empty states take you through household → items → stock → plan.

---

## API endpoint summary

All endpoints are under `/api`. Every route except register, login, logout, health and meta requires login. Household-scoped routes also require a household and only ever touch **your own** records; other households' records return `404`.

| Area | Method & path | Description |
|---|---|---|
| Auth | `POST /auth/register` | `name, email, password, confirm_password` → logs in |
| | `POST /auth/login` | `email, password` (rate-limited) |
| | `POST /auth/logout` | clears cookies |
| | `GET /auth/me` | current user |
| Household | `GET /household` | `household` or `null` |
| | `POST /household` · `PUT /household` | `household_name, family_size, shopping_frequency, monthly_budget, planning_period_days?` |
| Meta | `GET /meta/options` | categories, units, priorities, frequencies |
| Catalogue | `GET /groceries` | `?search&category&priority&sort&page&per_page&include_archived` |
| | `POST /groceries` | create (re-adding an archived name restores it) |
| | `GET /groceries/<id>` | item + `related_counts` |
| | `PUT /groceries/<id>` | update (`is_archived:false` restores) |
| | `DELETE /groceries/<id>` | deletes, or **archives** if the item has history |
| Inventory | `GET /inventory` | `?search&category&low_stock` + `untracked_items` |
| | `POST /inventory` | `item_id, quantity, low_stock_threshold?, expiry_date?` |
| | `PUT /inventory/<id>` | set absolute quantity / threshold / expiry |
| | `PATCH /inventory/<id>/quantity` | `change` (+/−), `reason?` |
| Purchases | `GET /purchases` | `?start_date&end_date&item_id&page` + `total_expenditure` |
| | `POST /purchases` | `item_id, quantity, unit_price?, purchase_date, store_name?, notes?, update_inventory?, client_reference?` |
| | `GET · PUT · DELETE /purchases/<id>` | edit/delete reconcile stock |
| Consumption | `GET /consumption` | `?start_date&end_date&item_id&page` |
| | `POST /consumption` | `item_id, quantity, consumed_at, notes?, deduct_from_stock?` |
| | `PUT · DELETE /consumption/<id>` | edit/delete reconcile stock |
| Plans | `POST /predictions/generate` | `history_periods?, optimise?` → saved plan |
| | `GET /predictions/latest` | latest plan or `null` |
| | `GET /recommendations` · `GET /recommendations/<id>` | plan history / one plan |
| | `POST /recommendations/<id>/optimise-budget` | apply budget rules → plan + summary |
| | `PATCH /recommendations/<id>/items/<line_id>` | `final_quantity?`, `is_checked?` (tick only) |
| | `POST /recommendations/<id>/items/<line_id>/mark-purchased` | `quantity?, unit_price?, purchase_date?, store_name?` → records purchase + stock |
| Dashboard | `GET /dashboard/summary` | all dashboard figures |
| Reports | `GET /reports/spending?months=` | by month (with budget usage), by category |
| | `GET /reports/consumption?item_id=&months=` | last 30 days + item trend |
| | `GET /reports/recommendations` | plan history + predicted vs purchased |
| Feedback | `GET /feedback` · `POST /feedback` | `rating (1–5), comment?` |
| Health | `GET /health` | API status |

In the item routes, `<line_id>` is the **plan line** id (`recommendation_items.id`), not the catalogue item id.

---

## Tests

```powershell
cd smart-grocery-optimiser\backend
.\.venv\Scripts\Activate.ps1
python -m pytest -v
```

The tests use a **separate in-memory database**, so your MySQL data is never touched. To run the same suite against MySQL, use the test database from setup step 1:

```powershell
$env:TEST_DATABASE_URL="mysql+pymysql://grocery_user:YourStrongPassword1@localhost:3306/smart_grocery_test?charset=utf8mb4"
python -m pytest -q
Remove-Item Env:TEST_DATABASE_URL
```

**45 tests** cover:

- registration and login, including invalid login, duplicate email and requests without a CSRF token
- household creation and retrieval
- grocery CRUD, archive-on-delete, and rejection of negative prices and quantities and invalid units
- inventory updates, including never going negative
- purchase recording and stock reconciliation on edit and delete, and blocking duplicate submits
- consumption aggregation, with no double counting
- average-based prediction, stock adjustment, labelled fallbacks and rounding of whole units
- **Examples A, B and C**: 8 − 3 = 5, 4 − 6 → 0, 5 − 0 = 5
- **Example D**: over budget → Optional reduced first, total recalculated, and the shortfall reported
- essentials alone exceeding the budget, and deterministic optimiser output
- household ownership: another user gets 404 on every record type
- plan persistence, the difference between ticking and buying, and preventing double purchase
- a database failure returning a clean 500 with a full rollback
- the demo seeder running twice

---

## Security

- Passwords are hashed with Werkzeug's scrypt. The hash is never returned by the API.
- The JWT is stored in an **HttpOnly** cookie that JavaScript cannot read. The access token expires after 8 hours by default.
- CSRF protection uses a double-submit token: the readable `csrf_access_token` cookie is sent back in the `X-CSRF-TOKEN` header by `api/axios.js`.
- **Local development:** `JWT_COOKIE_SECURE=False` and `SameSite=Lax`, over `http://localhost`.
- **Production:** serve over HTTPS and set `JWT_COOKIE_SECURE=True`. Keep `SameSite=Lax`, or use `Strict` if the frontend and API share a domain. Use long random secrets and set `FLASK_DEBUG=False`.
- Every household-scoped query filters by the logged-in user's household, so ownership is checked on each record.
- Every route reads an explicit list of allowed fields, so a request can't set fields it shouldn't (mass-assignment protection).
- All database access goes through the SQLAlchemy ORM, so queries are parameterised.
- CORS is limited to `FRONTEND_ORIGIN`.
- Login and registration are rate-limited (10 per minute per IP by default).
- Errors are returned as clean JSON. Stack traces are only logged on the server, and secrets never appear in logs or in Git (`.env` is git-ignored).

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Activate.ps1 cannot be loaded because running scripts is disabled` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then try again. |
| `mysql` is not recognised | Add `C:\Program Files\MySQL\MySQL Server 8.0\bin` to PATH, or use *MySQL Command Line Client* from the Start menu. |
| `Access denied for user 'grocery_user'` | The password in `backend\.env` must match the one in `CREATE USER`. |
| `Can't connect to MySQL server on 'localhost'` | Start the service: `Start-Service MySQL80` (as Administrator) or use *Services* → MySQL80. |
| `Unknown database 'smart_grocery'` | Run the `CREATE DATABASE` step. |
| `RuntimeError: 'cryptography' package is required` | Run `pip install -r requirements.txt` inside the activated venv. |
| Frontend shows “Cannot reach the server” | The backend isn't running on port 5000. Start `python run.py`. |
| Logged out immediately / “Missing security token” | Keep `VITE_API_BASE_URL=/api` in `frontend\.env` so requests go through the Vite proxy (same origin), then log in again. |
| “Too many attempts” on login | Rate limit reached. Wait a minute. |
| Port 5000 already in use | Set `PORT=5001` in `.env` and change the proxy target in `vite.config.js`. |
| Prediction shows “Needs data” for everything | Record consumption, or add an *Initial monthly estimate* to items in the catalogue. |

---

## Known limitations

- **The prediction is statistical, not machine learning.** A moving average does not model seasonality, festivals or guests. It reacts to these only after they appear in the history.
- Quantities are tracked in each item's own unit. There is no automatic conversion between units, so the unit of an item with history cannot be changed.
- Prices are user-entered estimates. There is no live price data.
- There is one household per user, and no shared household accounts.
- Budget optimisation is a transparent greedy rule set. It does not find a mathematically optimal basket, and it does not reason about nutrition.
- Login rate limiting uses in-memory storage, which resets when the server restarts. This is fine for a single local server.

---

## Future enhancements

- **Linear regression extension** (scikit-learn): once an item has, for example, 6 or more periods of history, fit a trend on period number versus total. Validate it on held-out periods with MAE, and use it only where it beats the moving-average baseline. Report both side by side.
- Festival and seasonal adjustments (Diwali, summer and so on), plus a guest/occasion multiplier.
- Shared households with several members.
- Automatic unit conversion (g ↔ kg, ml ↔ litre).
- Export the shopping list to PDF or WhatsApp. Add expiry reminders.
- A PWA for offline in-store use.

---

*Academic project (BCA). Demo data is synthetic and clearly labelled; it does not represent any real household.*
