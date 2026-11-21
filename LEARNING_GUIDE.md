# AI Data Intelligence Platform — Beginner-to-Advanced Learning Guide

Welcome to the **AI Data Intelligence Platform** architecture and developer handbook. This guide covers how every major module functions from conceptual foundations up to production-grade distributed execution.

---

## 1. Universal Data Ingestion & DuckDB Parquet Storage

### What does this module do?
It accepts any tabular dataset (CSV, Excel `.xlsx`/`.xls`, JSON, Parquet, Text) and automatically normalizes it into high-speed columnar Parquet storage.

### Why do we need it?
Loading giant CSV or Excel files repeatedly into server memory is slow and crashes backend workers. Storing data as columnar Parquet files allows sub-second analytical aggregations without loading the entire dataset into RAM.

### How does it work internally?
1. The user uploads a file through the UI via multipart form-data.
2. The backend (`profiler.py`) inspects the file extension, auto-detects character encoding, and constructs a Pandas/DuckDB representation.
3. DuckDB registers the dataframe as an in-memory view and exports it into a compressed `.parquet` analytical file.
4. Dataset metadata (row count, dimensions, byte size, quality score) is persistently committed into the SQLite/PostgreSQL database.

---

## 2. Autonomous Data Profiling & Quality Scoring

### How is the Data Quality Score calculated?
The platform calculates a transparent quality score (0.0% to 100.0%) using the following governed formula:
$$\text{Score} = 100 - \text{Missing Penalty} - \text{Duplicate Penalty} - \text{Outlier Penalty}$$

- **Missing Penalty:** Evaluates the ratio of null cells relative to total cells.
- **Duplicate Penalty:** Detects exact duplicate records across key dimensions.
- **Outlier Penalty:** Uses the Interquartile Range (IQR) technique ($Q_1 - 1.5 \times IQR$ and $Q_3 + 1.5 \times IQR$) to detect numerical outliers.

---

## 3. Governed Data Cleaning & Lineage Engine

### Why is non-destructive cleaning critical?
Real data analysts and enterprise compliance teams must never permanently destroy raw records. The platform creates versioned datasets (`_v2`, `_v3`) whenever an operation is applied.

### Supported Operations:
1. `drop_duplicates`: Removes duplicate rows while preserving the first chronological occurrence.
2. `impute_missing`: Fills null values using mean, median, mode, or constant strategies.
3. `type_cast`: Converts string representations into true numerical or ISO datetime formats.
4. `standardize_text`: Trims whitespace and standardizes casing (title, lower, upper).
5. `outlier_trim`: Clamps extreme outlier records to IQR boundaries.

---

## 4. Multi-Agent AI Analyst Architecture

```
User Query ("Which product has the highest revenue?")
       │
       ▼
[DataUnderstandingAgent] ──> Identifies target numerical ('revenue') & categorical ('product') columns
       │
       ▼
[SQLAnalyticalAgent]     ──> Generates safe DuckDB SQL:
                             "SELECT product, SUM(revenue) as total_revenue
                              FROM data GROUP BY product ORDER BY total_revenue DESC LIMIT 10"
       │
       ▼
[DuckDB Analytics Engine]──> Executes read-only query on compressed Parquet file (< 5ms)
       │
       ▼
[BusinessIntelligenceAgent]──> Generates natural business conclusion:
                               "The leading product is 'Hardware' with $107,000.00 in revenue."
       │
       ▼
[VisualizationAgent]     ──> Synthesizes Plotly JSON specification for interactive chart rendering
```

---

## 5. Automated Multi-Format Report Generation

### PowerPoint Presentation Deck (`python-pptx`)
- Creates 16:9 widescreen presentation slides.
- Dynamically formats Executive Summary, Data Health KPIs, and AI Findings.
- Outputs editable native Microsoft PowerPoint slides.

### Multi-Tab Excel Workbook (`openpyxl`)
- **Sheet 1 (Executive Summary):** Clean corporate layout detailing Data Quality Score, row counts, duplicate count, and audit grade.
- **Sheet 2 (Cleaned Data):** Formatted tabular worksheet with styled column headers for instant downstream modeling.

### Executive PDF Audit Report (`reportlab`)
- Compiles executive tables, methodology descriptions, and formal compliance statements.

---

## 6. Microsoft Power BI Integration Architecture

The platform supports 4 Power BI integration patterns:
1. **Direct Cleaned Excel/CSV Export:** 100% functional without external credentials.
2. **Power BI REST API Push Datasets:** Sends real-time row batches to Power BI service via Azure AD App Registration (`client_id`, `client_secret`, `tenant_id`).
3. **Power BI Embedded:** Embeds interactive reports directly in the workspace using embed tokens.
4. **Direct Database Connection:** Connects Power BI Desktop to PostgreSQL via native ODBC/PostgreSQL connectors.

---

## 7. How to Run Locally

### 1. Start the Backend API:
```powershell
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation and Swagger UI are accessible at: `http://127.0.0.1:8000/docs`

### 2. Start the Frontend Application:
```powershell
cd frontend
npm install
npm run dev
```
Open your browser at: `http://localhost:3000`

### 3. Log in with Default Administrative Credentials:
- **Email:** `admin@intel.ai`
- **Password:** `AdminPassword123!`
