# UnplugGo

A Streamlit web application for fire prevention and smart home monitoring in Cantilan, Surigao del Sur.

**Features:**
- User authentication (sign-in / sign-up)
- Smart appliance monitoring
- Fire prevention alerts
- Real-time monitoring dashboard

## Quick start

1. Create a Python virtual environment (recommended):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

3. Run the app:

```powershell
python -m streamlit run streamlit_app.py --server.port 8502
```

Or use the helper script (runs and opens Chrome automatically):

```powershell
.\run_streamlit.ps1
```

4. The app will open at `http://localhost:8502`

## Project structure

- `streamlit_app.py` — main entry point and landing page
- `pages/1_SignIn.py` — user sign-in page
- `pages/2_SignUp.py` — user sign-up / account creation page
- `pages/3_Home.py` — main dashboard with features (Smart Monitoring, Fire Prevention, Real-time Alerts)
- `requirements.txt` — Python dependencies
- `run_streamlit.ps1` — helper script to start Streamlit and open Chrome
- `images/` — image assets (optional)
- `src/unpluggo/` — reusable Python utilities
- `tests/` — unit tests (pytest)
- `docs/` — documentation

## Flow

1. User lands on the home page (`streamlit_app.py`)
2. User clicks "Sign In" or "Sign Up"
3. On sign-up, user enters full name, email, and password
4. On sign-in, user enters email and password
5. On successful login, user is redirected to the dashboard (`pages/3_Home.py`)
6. Dashboard shows three feature areas: Smart Monitoring, Fire Prevention, Real-time Alerts
7. User can sign out to return to the home page

## Testing

Run tests with:

```powershell
pytest -q
```

## Contributing

Open an issue or send a PR.
