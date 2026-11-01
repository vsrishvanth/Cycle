# Campus Cycle

A student prototype for buying used cycles, arranging physical inspections and reselling owner-held stock. Prices use an explicit judgement formula, not a verified market appraisal. Sarvam provides an optional explanation.

## Run on this computer

Install Python, then run `python -m pip install -r requirements.txt`.
Keep `SARVAM_API_KEY` in `.env`, then run `python cycle_server.py`.
Open http://127.0.0.1:8001. Create your owner password at `/admin`.

## Put a demonstration online

1. Sign in at https://github.com and create a **private** repository named `campus-cycle`.
2. Use **uploading an existing file** / **Add file → Upload files** to upload ONLY:
   - `cycle_server.py`, `valuation.py`, `cycles.html`, `owner.html`, `requirements.txt`, `README.md`, `.gitignore`.
3. Commit the uploaded files. Never upload `.env`, `cycles.db`, or your API key. The database contains private contact details and owner credentials.
4. Sign in at https://dashboard.render.com and choose **New → Web Service**. Connect the GitHub repository. Select **Python 3**.
5. Build command: `pip install -r requirements.txt`.
6. Start command: `python cycle_server.py`.
7. In environment settings add `SARVAM_API_KEY` with your actual key and `CYCLE_OWNER_PASSWORD` with a new private password of at least 10 characters. Enter them only in Render's secret settings.
8. For saved contacts and stock, choose a paid service with a persistent disk mounted at `/var/data`, and set `DATA_DIR=/var/data`. Check Render's displayed cost before purchasing. A free disposable demo loses its database when the filesystem resets; do not collect real seller contacts on that configuration.
9. Deploy. Render supplies an HTTPS `onrender.com` address. Share that address, not the localhost address. Sign in at `/admin` with the owner password set above.

The online database starts empty. Your local contacts and stock are not uploaded. On a persistent database, changing the initial password environment variable does not replace an already-created owner password.

This is a demonstration using Python's basic HTTP server behind the hosting proxy. Before a real campus launch, use a production application server, durable backups and proper account/rate-limit handling. Do not run multiple instances: login sessions are currently stored in one server process.

## Checks

`python -m unittest test_valuation test_cycle_server`

The tests use temporary databases and never call Sarvam.
