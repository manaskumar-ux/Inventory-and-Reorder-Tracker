# Inventory & Reorder Tracker

A Python desktop application for a small electronics laboratory or shop. It is an original implementation of the **Inventory and Reorder Tracker** option in the supplied project list, with a focus on stock movement history and clear reorder alerts.

## Features
- Add, edit and delete inventory items
- Validate item IDs, quantities, prices and dates
- Search items and filter by stock status
- Stock-in and stock-out operations with movement history
- Automatic `IN STOCK`, `REORDER`, and `OUT OF STOCK` status
- CSV import/export and JSON export
- NumPy inventory totals and average stock calculation
- Pandas category and monthly movement summaries
- Matplotlib category chart
- Sample electronics-lab inventory included

## Requirements
- Python 3.10 or newer
- VS Code with the Python extension
- Packages in `requirements.txt`
- Tkinter (normally included with standard Windows Python)

## Run in VS Code (Windows)
1. Extract the ZIP folder.
2. Open VS Code → **File → Open Folder** → select `Inventory_Reorder_Tracker`.
3. Open **Terminal → New Terminal**.
4. Create a virtual environment:
   `py -m venv .venv`
5. Activate it:
   PowerShell: `.venv\Scripts\Activate.ps1`
   If PowerShell blocks activation, use Command Prompt and run `.venv\Scripts\activate.bat`.
6. Install packages:
   `py -m pip install -r requirements.txt`
7. Run:
   `py app.py`

If `py` is not recognised, try `python` instead. To check Tkinter, run `py -m tkinter`.

## CSV format
Required column names (exact spelling):
`item_id,name,category,quantity,reorder_level,unit_price,updated_on`

Example:
`EL101,Resistor 220 ohm,Passive,50,10,0.75,2026-11-13`

- Item IDs must be unique.
- Quantity and reorder level must be non-negative whole numbers.
- Unit price must be zero or greater.
- Date must use `YYYY-MM-DD`.

## Project files
- `app.py` — complete application
- `data/inventory.csv` — demonstration inventory
- `data/movements.csv` — demonstration stock movement history
- `requirements.txt` — Python packages
- `tests/test_logic.py` — automated logic tests
- `PROJECT_REPORT.docx` and `PROJECT_REPORT.pdf` — report copies

## GitHub upload
1. Sign in at https://github.com and click **New repository**.
2. Name it `Inventory-and-Reorder-Tracker` (or the exact project title).
3. Choose Public/Private as instructed by your teacher. Do not initialize with a README because this folder already contains one.
4. In VS Code open the project folder. Select **Source Control** on the left.
5. Click **Initialize Repository**, stage the files with `+`, enter a commit message such as `Initial project submission`, and click **Commit**.
6. Click **Publish Branch** / **Publish to GitHub**, sign in if prompted, and select the repository you created.
7. Alternatively use terminal:
   `git init`
   `git add .`
   `git commit -m "Initial project submission"`
   `git branch -M main`
   `git remote add origin https://github.com/YOUR-USERNAME/Inventory-and-Reorder-Tracker.git`
   `git push -u origin main`
   Replace `YOUR-USERNAME` with your own GitHub username. Do not paste passwords or tokens into source code.

## Before submission
- Run the app on your own computer and test each button.
- Add your actual name, roll number, enrollment number, section and institution to the report cover.
- Take genuine screenshots of the app running on your computer and add them to the report if required.
- Be prepared to explain the `Item` class, CSV validation, stock status rule, NumPy summary and Pandas report.
- Follow your teacher's rules about group contributions and the Google Sheet. Do not claim tests or screenshots you have not completed.
