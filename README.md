# AI Data Intelligence Platform — Production Project Documentation

## 1. Project Overview
The **AI Data Intelligence Platform** is a full-stack, enterprise-grade Data Analytics Automation SaaS. It automates raw file ingestion, statistical data profiling, data quality auditing, non-destructive cleaning, exploratory data analysis via DuckDB SQL, multi-agent AI inquiry, predictive machine learning, and multi-format reporting (PowerPoint decks, PDF audits, Excel workbooks, and Power BI connectivity).

---

## 2. Technology Stack
- **Backend API**: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy ORM, SQLite / PostgreSQL.
- **Data Engine**: DuckDB SQL Engine, Pandas, NumPy, Columnar Parquet.
- **Machine Learning**: Scikit-Learn (Linear Regression, Random Forest, K-Means Clustering).
- **Generative Reporting**: `python-pptx` (PowerPoint), `openpyxl` (Excel), `reportlab` (PDF).
- **Frontend Architecture**: Next.js 14, React 18, TypeScript, Tailwind CSS, Lucide Icons.
- **Security & RBAC**: PBKDF2-HMAC-SHA256 password hashing, signed JWT Bearer authentication, tenant-isolated relational access controls.
- **DevOps**: Docker, Docker Compose, `.env.example`.

---

## 3. Directory Layout
```
ai-data-intelligence/
├── backend/
│   ├── app/
│   │   ├── api/v1/         # REST API endpoints (auth, projects, datasets, cleaning, ai, reports, powerbi)
│   │   ├── core/           # Configuration, database engine, PBKDF2/JWT security, dependencies
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── schemas/        # Pydantic validation schemas
│   │   ├── data_engine/    # Multi-format ingestion, statistical profiler, governed cleaner
│   │   ├── analytics/      # DuckDB SQL analytical engine, Scikit-learn predictive ML
│   │   ├── ai_engine/      # Multi-agent analyst swarm (profiling, SQL, insights, visualization)
│   │   ├── reporting/      # python-pptx, openpyxl, reportlab builders
│   │   └── integrations/   # Microsoft Power BI integration gateway
│   ├── tests/              # Automated test suites
│   ├── main.py             # FastAPI entrypoint
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js app router & pages (Authentication & Analytics Studio)
│   │   ├── lib/            # Authenticated API client
│   │   └── types/          # TypeScript interfaces
│   ├── package.json
│   └── Dockerfile
├── storage/                # Persistent database, uploaded datasets, Parquet lake, reports
├── docker-compose.yml
├── LEARNING_GUIDE.md       # Comprehensive educational guide
├── DEVELOPMENT_PROGRESS.md # Development milestones tracker
└── README.md
```

---

## 4. Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+

### Setup & Run
```powershell
# 1. Backend
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# 2. Frontend
cd ../frontend
npm install
npm run dev
```

### Pre-configured Administrator Account
- **Email:** `admin@intel.ai`
- **Password:** `AdminPassword123!`
