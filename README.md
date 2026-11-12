# Intelligent Invoice Processing System

An AI-powered, end-to-end Accounts Payable automation platform. Upload any vendor invoice PDF and receive a fully-reasoned approval decision in seconds — with a complete audit trail.

> **Live Demo**
> - Frontend: https://frontendupdated-two.vercel.app
> - Backend API: https://invoice-ai-backend-b2bd.onrender.com
> - API Docs (Swagger): https://invoice-ai-backend-b2bd.onrender.com/docs

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Processing Pipeline](#processing-pipeline)
- [Business Rules Engine](#business-rules-engine)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Local Setup](#local-setup)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Configuration](#configuration)
- [Running Locally](#running-locally)
- [Deployment](#deployment)
  - [Backend → Render](#backend--render)
  - [Frontend → Vercel](#frontend--vercel)
- [API Reference](#api-reference)
- [Seed Data](#seed-data)
- [Database Schema](#database-schema)
- [Testing](#testing)

---

## Overview

This system automates the entire invoice review workflow for an Accounts Payable team. It accepts PDF invoices (both digital and scanned), extracts all fields using AI, validates them against vendor master data and purchase orders, runs a deterministic rules engine, and produces one of three final decisions:

| Decision | Meaning |
|---|---|
| **Approved** | All checks passed — safe to process for payment |
| **Needs Review** | One or more soft-warning rules triggered — AP team must verify |
| **Rejected** | A blocking rule fired (duplicate, unknown vendor, PO mismatch, etc.) |

Every decision is backed by a step-by-step audit trail visible in the UI.

---

## Features

- **PDF Classification** — Automatically detects digital vs. scanned PDFs
- **OCR Support** — Tesseract OCR for scanned / image-based invoices
- **AI Field Extraction** — Google Gemini or OpenAI extracts structured JSON from raw invoice text
- **Data Normalization** — Cleans dates, amounts, currency codes and flags missing fields
- **Arithmetic Validation** — Checks subtotal + tax = total and line item sums
- **Vendor Verification** — Fuzzy name matching + GSTIN/Tax ID lookup against vendor master
- **PO Matching** — Links invoice to the correct Purchase Order with ownership and balance check
- **Duplicate Detection** — Two-tier system: exact match (blocking) and fuzzy/circumstantial (review)
- **11 Business Rules** — Deterministic rule evaluation covering all AP scenarios
- **Real-time Progress** — Live pipeline stage updates streamed to the UI
- **Full Audit Trail** — Every stage, validation check, and rule outcome is persisted
- **Dashboard** — Live stats, recent invoices table, and feature overview
- **View Original PDF** — Every processed invoice links back to the original uploaded file

---

## Tech Stack

### Backend

| Component | Technology |
|---|---|
| Framework | FastAPI 0.115 |
| Database ORM | SQLAlchemy 2.0 |
| Database | SQLite (file-based) |
| PDF parsing | PyMuPDF (fitz) |
| OCR | Tesseract via pytesseract |
| AI extraction | Google Gemini (`gemini-1.5-flash`) / OpenAI (`gpt-4o-mini`) |
| Fuzzy matching | thefuzz |
| Async file I/O | aiofiles |
| Data validation | Pydantic v2 + pydantic-settings |
| Date parsing | python-dateutil |
| Server | Uvicorn (ASGI) |

### Frontend

| Component | Technology |
|---|---|
| Framework | Next.js 15 (App Router) |
| UI library | React 19 |
| Language | TypeScript 5.6 |
| Styling | Tailwind CSS 3.4 |
| Icons | Lucide React |
| HTTP client | Axios |

---

## Architecture

```
┌─────────────────────────────────┐       ┌──────────────────────────────────┐
│         Next.js Frontend        │       │          FastAPI Backend          │
│  (localhost:3000 / Vercel)      │◄─────►│  (localhost:8000 / Render)       │
│                                 │  API  │                                  │
│  /           Dashboard          │       │  POST /api/invoices/upload        │
│  /upload     Upload page        │       │  GET  /api/invoices/              │
│  /invoices   Invoice list       │       │  GET  /api/invoices/{id}          │
│  /invoices/[id]  Detail view    │       │  GET  /api/invoices/runs/{id}     │
│  /runs/[id]  Run detail         │       │  GET  /api/dashboard/             │
└─────────────────────────────────┘       └──────────────┬───────────────────┘
                                                         │
                                          ┌──────────────▼───────────────────┐
                                          │      Processing Pipeline          │
                                          │  upload → classify → extract_text │
                                          │  → ai_extract → normalize         │
                                          │  → validate → vendor_po           │
                                          │  → duplicate → rules → decision   │
                                          └──────────────────────────────────┘
```

---

## Processing Pipeline

Each uploaded invoice passes through 10 sequential stages:

| Stage | Name | Description |
|---|---|---|
| 1 | **upload** | File saved to disk, Invoice record created |
| 2 | **classify** | PDF classified as `digital` or `scanned` based on embedded-text ratio |
| 3 | **extract_text** | Text extracted via PyMuPDF (digital) or Tesseract OCR (scanned) |
| 4 | **ai_extract** | Raw text sent to Gemini / OpenAI; structured JSON returned |
| 5 | **normalize** | Dates, amounts, currencies cleaned; missing fields identified |
| 6 | **validate** | Arithmetic checks (subtotal + tax = total, line item sums) |
| 7 | **vendor_po** | Vendor looked up by GSTIN then fuzzy name; PO matched and balance updated |
| 8 | **duplicate** | Two-tier duplicate detection (exact + fuzzy/circumstantial) |
| 9 | **rules** | All 11 business rules evaluated |
| 10 | **decision** | Final status set with explanation and recommended action |

> If an early stage fails, all remaining stages are stubbed as "Skipped" and the run is marked `failed`.

---

## Business Rules Engine

Eleven deterministic rules fire against all evidence collected from prior stages:

| Rule | Severity | Trigger Condition |
|---|---|---|
| R01 — Duplicate invoice | BLOCKING | Exact invoice number + same vendor already approved/in-review |
| R01 — Resubmission | REVIEW | Exact match against a previously *rejected* invoice |
| R01 — Possible duplicate | REVIEW | Same vendor + same amount + same date (fuzzy number match) |
| R02 — Vendor not found | BLOCKING | Vendor name/GSTIN not in vendor master |
| R03 — Vendor inactive | BLOCKING | Vendor found but status is not `approved` |
| R04 — Missing invoice number | REVIEW | Invoice number could not be extracted |
| R05 — Mandatory fields | REVIEW | Required fields (vendor, total, date) are absent |
| R06 — Arithmetic failure | REVIEW | subtotal + tax ≠ total, or line items don't sum correctly |
| R07 — Low confidence | REVIEW | Extraction confidence < 60% (always triggered for scanned PDFs) |
| R08 — No PO match | BLOCKING / REVIEW | PO vendor mismatch (blocking) or PO not found (review) |
| R09 — PO not approved | BLOCKING | Matched PO status is `inactive` or `closed` |
| R10 — Currency mismatch | BLOCKING | Invoice currency differs from PO currency |
| R11 — Amount tolerance | REVIEW | Invoice amount differs from PO by more than 2% |

**Decision logic:**
- Any BLOCKING rule triggered → `rejected`
- One or more REVIEW rules triggered, no BLOCKING → `needs_review`
- All rules passed → `approved`

---

## Project Structure

```
Invoice_system/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app, CORS middleware, router registration
│   │   ├── config.py               # Settings (env-driven via pydantic-settings)
│   │   ├── database.py             # SQLAlchemy engine and session factory
│   │   ├── models/
│   │   │   └── models.py           # ORM models: Vendor, PurchaseOrder, Invoice, ProcessingRun...
│   │   ├── schemas/
│   │   │   └── schemas.py          # Pydantic request/response schemas
│   │   ├── routers/
│   │   │   ├── invoices.py         # Upload, list, detail, run status endpoints
│   │   │   ├── vendors.py          # Vendor list and detail
│   │   │   ├── purchase_orders.py  # PO list and detail
│   │   │   └── dashboard.py        # Aggregate stats for dashboard
│   │   └── services/
│   │       ├── pipeline.py         # 10-stage orchestrator
│   │       ├── pdf_extractor.py    # PyMuPDF + Tesseract OCR
│   │       ├── ai_extractor.py     # Gemini / OpenAI extraction
│   │       ├── normalizer.py       # Field cleaning and arithmetic validation
│   │       ├── vendor_verifier.py  # Fuzzy vendor lookup
│   │       ├── po_matcher.py       # PO matching and balance tracking
│   │       ├── duplicate_detector.py  # Two-tier duplicate detection
│   │       ├── rules_engine.py     # 11 business rules
│   │       ├── decision_engine.py  # Final status from rule results
│   │       └── run_manager.py      # Stage/run lifecycle helpers
│   ├── seed_data.py                # Seed vendors and purchase orders
│   ├── reset_demo.py               # Reset DB to clean state
│   ├── requirements.txt
│   ├── render.yaml                 # Render deployment config
│   └── uploads/                   # Uploaded PDF files (created at runtime)
│
└── frontend_updated/               # Final production frontend
    ├── app/
    │   ├── page.tsx                # Dashboard (stats, recent invoices, feature cards)
    │   ├── upload/page.tsx         # Invoice upload page
    │   ├── invoices/               # Invoice list and detail pages
    │   ├── runs/                   # Processing run live-progress page
    │   ├── dashboard/              # Dashboard route
    │   ├── icon.svg                # Custom blue favicon
    │   └── layout.tsx              # Root layout with Navbar and Footer
    ├── components/                 # Reusable UI components (Navbar, Footer, StatusBadge)
    ├── lib/
    │   ├── api.ts                  # All API client functions (axios)
    │   └── types.ts                # TypeScript type definitions
    ├── .env.local                  # Frontend env vars (not committed)
    └── package.json
```

---

## Prerequisites

- **Python 3.10+**
- **Node.js 18+** and **npm**
- **Tesseract OCR** (required only for scanned / image-based PDFs)
  - Windows: Download from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki), install to `C:\Program Files\Tesseract-OCR\`
  - macOS: `brew install tesseract`
  - Ubuntu/Debian: `sudo apt install tesseract-ocr`
- A **Google Gemini API key** (default) **or** an **OpenAI API key**

---

## Local Setup

### Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Seed vendors and purchase orders
python seed_data.py
```

### Frontend Setup

```bash
cd frontend_updated

npm install
```

---

## Configuration

### Backend — `backend/.env`

```env
# AI Provider: "gemini" (default) or "openai"
AI_PROVIDER=gemini

# Google Gemini API key (required if AI_PROVIDER=gemini)
GEMINI_API_KEY=your_gemini_api_key_here

# OpenAI API key (required if AI_PROVIDER=openai)
OPENAI_API_KEY=sk-your_openai_key_here

# SQLite database path (relative to backend/)
DATABASE_URL=sqlite:///./invoice_system.db

# Directory to store uploaded PDF files
UPLOAD_DIR=uploads

# Amount variance tolerance for PO matching (0.02 = 2%)
TOLERANCE_THRESHOLD=0.02

# Allowed CORS origins (comma-separated, used in production)
ALLOWED_ORIGINS=http://localhost:3000
```

### Frontend — `frontend_updated/.env.local`

```env
# URL of the running backend API
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Running Locally

### Start the Backend

```bash
cd backend
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Start the Frontend

```bash
cd frontend_updated
npm run dev
```

| Service | URL |
|---|---|
| Frontend (UI) | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger API Docs | http://localhost:8000/docs |
| ReDoc API Docs | http://localhost:8000/redoc |

---

## Deployment

### Backend → Render

1. Connect this GitHub repository to [Render](https://render.com)
2. Create a new **Web Service**, set **Root Directory** to `backend`
3. Render will auto-detect `render.yaml` — it sets the build and start commands automatically
4. Add these **Environment Variables** in the Render dashboard:

| Variable | Value |
|---|---|
| `AI_PROVIDER` | `gemini` |
| `GEMINI_API_KEY` | your Gemini API key |
| `ALLOWED_ORIGINS` | your Vercel frontend URL (e.g. `https://your-app.vercel.app`) |
| `UPLOAD_DIR` | `uploads` |
| `TOLERANCE_THRESHOLD` | `0.02` |

> **Note:** Render's free tier uses an ephemeral filesystem — the SQLite database and uploaded PDFs reset on each redeploy. The app automatically re-seeds vendor/PO data on startup.

---

### Frontend → Vercel

1. Connect this GitHub repository to [Vercel](https://vercel.com)
2. Set **Root Directory** to `frontend_updated`
3. Framework will be auto-detected as **Next.js**
4. Add this **Environment Variable** in the Vercel dashboard:

| Variable | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | your Render backend URL (e.g. `https://your-backend.onrender.com`) |

5. Deploy — Vercel handles the build automatically.

---

## API Reference

### Health

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check — returns `{"status": "ok"}` |

### Dashboard

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/dashboard/` | Aggregate stats + 10 recent invoices |

### Invoices

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/invoices/upload` | Upload a PDF invoice (multipart/form-data). Max 20 MB. |
| `GET` | `/api/invoices/` | List all invoices (newest first) |
| `GET` | `/api/invoices/{invoice_id}` | Full invoice detail including extracted fields and status |
| `GET` | `/api/invoices/{invoice_id}/runs` | All processing runs for an invoice |
| `GET` | `/api/invoices/runs/{run_id}` | Full run detail: stages, validation results, audit events |
| `GET` | `/api/invoices/runs/{run_id}/stream` | **SSE** — live stage-by-stage progress stream |

### Vendors

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/vendors/` | List all vendors in vendor master |
| `GET` | `/api/vendors/{vendor_id}` | Single vendor detail |

### Purchase Orders

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/purchase-orders/` | List all purchase orders |

### Uploaded Files

```
GET /uploads/{stored_filename}
```

---

## Seed Data

The `seed_data.py` script populates the database with 6 vendors and 7 purchase orders.

```bash
cd backend
python seed_data.py
```

**Vendors:**

| ID | Legal Name | Currency | Tax ID | Status |
|---|---|---|---|---|
| V001 | ABC Technologies Pvt Ltd | INR | TEST-TAX-001 | approved |
| V002 | XYZ Solutions Pvt Ltd | INR | TEST-TAX-002 | approved |
| V003 | Global Services Inc | INR | TEST-TAX-003 | inactive |
| V004 | Northstar Systems Ltd | INR | TEST-TAX-004 | approved |
| V005 | Pinnacle Consulting Group | INR | TEST-TAX-005 | approved |
| V006 | Northwind Office Supplies Pvt. Ltd. | USD | 05AABCN1234F1Z5 | approved |

**Purchase Orders:**

| PO Number | Vendor | Total Amount | Currency | Status |
|---|---|---|---|---|
| PO-10045 | ABC Technologies (V001) | 53,100.00 | INR | approved |
| PO-10048 | ABC Technologies (V001) | 1,20,000.00 | INR | approved |
| PO-10046 | XYZ Solutions (V002) | 25,000.00 | INR | approved |
| PO-10047 | Global Services (V003) | 75,000.00 | INR | inactive |
| PO-10049 | Northstar Systems (V004) | 26,500.00 | INR | approved |
| PO-10050 | Pinnacle Consulting (V005) | 1,80,000.00 | INR | approved |
| PO-2026-1093 | Northwind Office Supplies (V006) | 4,900.00 | USD | approved |

To reset to a clean demo state:

```bash
cd backend
python reset_demo.py
```

---

## Database Schema

| Table | Description |
|---|---|
| `vendors` | Vendor master — legal name, aliases, tax ID, status |
| `purchase_orders` | PO header — vendor, amounts, currency, status, running balance |
| `po_line_items` | PO line items — description, qty, unit price, amount |
| `invoices` | Uploaded invoices — extracted fields, matched PO/vendor, final status |
| `processing_runs` | One run per invoice upload — status, current stage, timestamps |
| `processing_stages` | One row per pipeline stage per run — status, output summary |
| `validation_results` | Arithmetic checks + business rule outcomes per run |
| `audit_events` | Structured event log entries per run |

---

## Testing

```bash
cd backend
venv\Scripts\activate

python test_e2e.py           # End-to-end pipeline test
python test_pipeline.py      # Happy path invoice
python test_duplicate.py     # Duplicate detection
python test_all_scenarios.py # Edge case invoices
python test_phase4.py        # Phase 4 feature tests
```

Test invoice PDFs are in `backend/test_invoices/` and the project root.
