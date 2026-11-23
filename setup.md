# Smart Grocery Optimiser — Complete Setup Guide

Welcome to **Smart Grocery Optimiser**! This guide explains how to install and run the project on your computer, even if you have no technical background.

Follow the steps in order. You do not need to understand programming to complete the setup.

---

## 1. What do you need before starting?

Install the following software on your computer.

### Required software

| Software | Purpose | Download |
|---|---|---|
| Python 3.12 | Runs the backend and ML code | https://www.python.org/downloads/ |
| Node.js (LTS) | Runs the frontend | https://nodejs.org/ |
| MySQL Server | Stores grocery and user information | https://dev.mysql.com/downloads/mysql/ |
| MySQL Workbench | Helps manage the database visually | https://dev.mysql.com/downloads/workbench/ |
| Git | Downloads the project | https://git-scm.com/downloads/ |
| VS Code | Opens and edits project files | https://code.visualstudio.com/ |

**Important:** During Python installation, select the checkbox:

`Add Python to PATH`

This makes Python available from PowerShell.

### Check your installations

Open PowerShell and run these commands one by one:

```powershell
python --version
node --version
npm --version
git --version
```

If each command displays a version number, the installation was successful.

---

## 2. Download the project

Open PowerShell.

Move to the folder where you want to keep the project.

Download it using Git:

```powershell
git clone https://github.com/sambit31/smart-grocery-optimiser.git
```

Open the project folder:

```powershell
cd smart-grocery-optimiser
```

Open the project in VS Code:

```powershell
code .
```

### Project structure

The project contains these main folders:

```text
smart-grocery-optimiser/
│
├── backend/          # Flask backend and APIs
│   ├── app/
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/         # User interface
│   └── .env.example
│
├── database/         # Database-related files
│
├── ml/               # Machine learning code
│   ├── datasets/
│   ├── experiments/
│   ├── models/
│   └── tests/
│
├── pyproject.toml    # ML package configuration
├── ml.env.example    # ML database configuration
└── README.md
```

---

## 3. Set up the MySQL database

The application uses MySQL to store its data.

### Step 3.1: Start MySQL

1. Open MySQL Workbench.
2. Connect to your local MySQL Server.
3. Enter your MySQL password.
4. Open a new SQL query tab.

### Step 3.2: Create the database

Run this SQL command:

```sql
CREATE DATABASE smart_grocery;
```

This creates an empty database named `smart_grocery`.

You can verify it by running:

```sql
SHOW DATABASES;
```

You should see `smart_grocery` in the result.

### Step 3.3: Remember your database details

You will need these details later:

- Database host: `localhost`
- Database port: `3306`
- Database name: `smart_grocery`
- MySQL username: Your MySQL username
- MySQL password: Your MySQL password

Keep your password private.

---

## 4. Configure environment files

Environment files store configuration information such as database passwords, API keys and application settings.

The project provides example files. You must create your own working environment files from them.

**Never upload your actual `.env` files to GitHub.**

### Step 4.1: Backend configuration

Open PowerShell from the project root:

```powershell
Copy-Item .\backend\.env.example .\backend\.env
```

Open the new file:

```powershell
code .\backend\.env
```

Update the database settings:

```env
MYSQL_USER=your_mysql_username
MYSQL_PASSWORD=your_mysql_password
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=smart_grocery
```

Also configure:

```env
SECRET_KEY=your_secret_key
JWT_SECRET_KEY=your_jwt_secret
JWT_EXPIRES_HOURS=24

JWT_COOKIE_SECURE=False
JWT_COOKIE_SAMESITE=Lax

FRONTEND_ORIGIN=http://localhost:5173
AUTH_RATE_LIMIT=5 per minute
PREDICTION_HISTORY_PERIODS=12
FLASK_DEBUG=True
CURRENCY=INR

GROQ_API_KEY=your_groq_api_key
```

Generate random secret keys using Python:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Run it twice and use the two generated values for `SECRET_KEY` and `JWT_SECRET_KEY`.

If you do not have a Groq API key, obtain one from:

https://console.groq.com/keys

The AI-related functionality requiring Groq will need a valid key.

### Step 4.2: Frontend configuration

Run:

```powershell
Copy-Item .\frontend\.env.example .\frontend\.env
```

Open:

```powershell
code .\frontend\.env
```

Configure:

```env
VITE_API_BASE_URL=http://localhost:5000
```

This tells the frontend where to find the backend API. If your backend uses another port, update this URL accordingly.

### Step 4.3: Machine Learning configuration

Run:

```powershell
Copy-Item .\ml.env.example .\ml.env
```

Open:

```powershell
code .\ml.env
```

Configure:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_NAME=smart_grocery
```

Use the same MySQL credentials as the backend.

**Important:** The ML environment file is located in the project root, not inside the `ml` folder.

---

## 5. Set up the Python backend

The backend is built using Flask and communicates with the MySQL database.

### Step 5.1: Open the backend folder

```powershell
cd backend
```

### Step 5.2: Create a virtual environment

A virtual environment keeps the project's Python packages separate from other Python projects.

```powershell
python -m venv .venv
```

### Step 5.3: Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

You should see `(.venv)` at the beginning of your PowerShell prompt.

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

This changes the execution policy only for the current PowerShell session.

### Step 5.4: Upgrade pip

```powershell
python -m pip install --upgrade pip
```

### Step 5.5: Install backend dependencies

```powershell
pip install -r requirements.txt
```

Wait until all packages finish installing.

### Step 5.6: Install the ML package

Return to the project root:

```powershell
cd ..
```

Make sure the backend virtual environment is still activated.

Install the project's ML package:

```powershell
python -m pip install -e .
```

This makes the project's ML modules importable by the backend.

---

## 6. Set up the database tables

The project uses Flask-Migrate to manage database tables.

From the project root, activate the backend environment if it is not already active:

```powershell
.\backend\.venv\Scripts\Activate.ps1
```

Move into the backend:

```powershell
cd backend
```

Run the database migration:

```powershell
flask --app run.py db upgrade
```

This applies the available database migrations and creates or updates the required tables.

**Important:** If you get an error saying that `run.py` cannot be found, check the backend's actual Flask entry-point file and use that entry point instead.

---

## 7. Start the backend server

Stay inside the `backend` folder.

Run:

```powershell
flask --app run.py run --debug
```

If everything is configured correctly, Flask will start its development server.

The expected local address is:

```text
http://127.0.0.1:5000
```

Keep this PowerShell window open.

**Do not close it while using the application.**

---

## 8. Start the frontend

Open a second PowerShell window.

Move into the frontend folder:

```powershell
cd smart-grocery-optimiser
cd frontend
```

Install frontend dependencies:

```powershell
npm install
```

Start the development server:

```powershell
npm run dev
```

The frontend should be available at:

```text
http://localhost:5173
```

Open this address in Chrome or another browser.

You should now be able to access the application's interface.

Keep the frontend PowerShell window open too.

---

## 9. Understanding how to run the project next time

Once everything has been installed, you do not need to repeat all installation steps.

Whenever you want to use the project, follow this routine.

### Terminal 1 — Backend

```powershell
cd smart-grocery-optimiser
.\backend\.venv\Scripts\Activate.ps1
cd backend
flask --app run.py run --debug
```

### Terminal 2 — Frontend

```powershell
cd smart-grocery-optimiser\frontend
npm run dev
```

### MySQL

Make sure your MySQL Server is running.

Then open:

```text
http://localhost:5173
```

---

## 10. Run the project tests

Tests help check whether the application is working correctly.

Open PowerShell from the project root.

Activate the backend environment:

```powershell
.\backend\.venv\Scripts\Activate.ps1
```

### Run backend tests

```powershell
python -m pytest .\backend\tests -v
```

### Run machine learning tests

```powershell
python -m pytest .\ml\tests -v
```

If the tests pass, you should see a successful test summary.

---

## 11. Common problems and solutions

### Problem 1: Python is not recognized

**Reason:** Python is not added to PATH.

**Solution:** Reinstall Python and select `Add Python to PATH`, or use the Python launcher if available.

### Problem 2: MySQL connection failed

Check:

1. Is MySQL Server running?
2. Is the database name correct?
3. Is the username correct?
4. Is the password correct?
5. Is the port set to `3306`?

Also confirm that the database `smart_grocery` exists.

### Problem 3: ModuleNotFoundError

Example:

```text
ModuleNotFoundError: No module named 'flask'
```

**Solution:**

Activate the backend virtual environment and install the requirements again:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

For ML imports, also install the root package:

```powershell
cd ..
python -m pip install -e .
```

### Problem 4: Frontend cannot connect to backend

Check the frontend `.env`:

```env
VITE_API_BASE_URL=http://localhost:5000
```

Make sure the backend server is running.

If you change a Vite environment variable, restart the frontend development server.

### Problem 5: Database tables are missing

Run:

```powershell
cd backend
flask --app run.py db upgrade
```

### Problem 6: npm is not recognized

Install Node.js LTS and restart PowerShell.

Check:

```powershell
node --version
npm --version
```

### Problem 7: Port is already in use

Another application may already be using the required port.

Close the other application or configure the project to use an available port, updating the frontend API URL if necessary.

---

## 12. Important security instructions

Please follow these rules:

1. Never upload `.env` files or `ml.env` to GitHub.
2. Never share your MySQL password.
3. Never share your Flask secret keys or JWT secret.
4. Never publish your Groq API key.
5. Only commit `.env.example` files containing placeholder values.
6. Do not use Flask debug mode in production.
7. Use HTTPS and secure cookie settings when deploying the application.

---

## 13. Final setup checklist

Before using the application, check the following:

- [ ] Python installed
- [ ] Node.js installed
- [ ] MySQL Server installed and running
- [ ] MySQL database `smart_grocery` created
- [ ] Backend `.env` configured
- [ ] Frontend `.env` configured
- [ ] Root `ml.env` configured
- [ ] Backend virtual environment created
- [ ] Backend dependencies installed
- [ ] ML package installed
- [ ] Database migrations applied
- [ ] Backend server running
- [ ] Frontend dependencies installed
- [ ] Frontend server running
- [ ] Application opens in the browser

---

## 14. Application address

Once both servers are running:

**Frontend:**

http://localhost:5173

**Backend:**

http://127.0.0.1:5000

---

**Congratulations!** Your Smart Grocery Optimiser project should now be ready to run locally.

If you encounter any problem during installation, read the error message carefully and check the troubleshooting section above. Make sure MySQL, the backend and the frontend are all running before testing the application.

