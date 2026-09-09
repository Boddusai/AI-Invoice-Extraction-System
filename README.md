# AI-Powered Invoice Data Extraction and Validation System

An end-to-end full-stack application that automatically processes invoice PDFs and images, extracts structured invoice information using OCR and intelligent parsing, validates the extracted data, detects duplicate invoices, allows manual review and correction, and exports results to JSON, CSV, and Excel.

---

## Live Application

### Frontend

https://ai-invoice-extraction-system.vercel.app

### Backend API

https://ai-invoice-extraction-api.onrender.com

### Swagger API Documentation

https://ai-invoice-extraction-api.onrender.com/docs

### GitHub Repository

https://github.com/Boddusai/AI-Invoice-Extraction-System

---

## Project Objective

The objective of this project is to reduce manual invoice data entry by automatically extracting and validating important information from invoice PDFs and images.

The system supports digital PDFs, scanned PDFs, JPG, JPEG, and PNG invoice files.

It provides a complete workflow from invoice upload to structured data export.

---

## Key Features

- PDF invoice upload
- JPG/JPEG/PNG invoice upload
- Digital PDF text extraction
- OCR for scanned PDFs and invoice images
- Image preprocessing using OpenCV
- Vendor name extraction
- GSTIN extraction
- Invoice number extraction
- Invoice date extraction
- Due date extraction
- Subtotal extraction
- Tax amount extraction
- Grand total extraction
- Currency extraction
- Line-item extraction
- Field-level confidence scores
- Overall invoice confidence score
- Invoice validation engine
- GSTIN format validation
- Amount calculation validation
- Date validation
- Line-item validation
- Exact duplicate detection using SHA-256
- Advanced duplicate detection using invoice data
- OCR-tolerant fuzzy invoice number matching
- Manual invoice review and correction
- Editable line items
- Revalidation after manual correction
- Invoice history
- Search and filtering
- Pagination
- JSON export
- CSV export
- Excel export
- Responsive React dashboard
- Dockerized backend deployment
- Cloud PostgreSQL database

---

## Technology Stack

### Frontend

- React
- Vite
- JavaScript
- React Router
- Axios
- Lucide React
- CSS

### Backend

- Python 3.12
- FastAPI
- SQLAlchemy
- Pydantic
- Uvicorn

### OCR and Document Processing

- Tesseract OCR
- pytesseract
- OpenCV
- PyMuPDF
- NumPy
- Pillow

### Database

- PostgreSQL
- Neon PostgreSQL

### Export

- JSON
- CSV
- XlsxWriter

### Deployment

- Vercel — Frontend
- Render — Backend
- Docker
- Neon — PostgreSQL
- GitHub — Source control

---

# System Architecture

```text
                         USER
                           │
                           ▼
                 ┌─────────────────┐
                 │   React + Vite  │
                 │     Vercel      │
                 └────────┬────────┘
                          │
                       HTTPS API
                          │
                          ▼
                 ┌─────────────────┐
                 │     FastAPI     │
                 │ Render + Docker │
                 └────────┬────────┘
                          │
            ┌─────────────┼─────────────┐
            │             │             │
            ▼             ▼             ▼
         PyMuPDF      Tesseract      OpenCV
       PDF Parsing       OCR       Preprocessing
            │             │             │
            └─────────────┴─────────────┘
                          │
                          ▼
                  Field Extraction
                          │
                          ▼
                  Line Item Parsing
                          │
                          ▼
                 Confidence Scoring
                          │
                          ▼
                    Validation
                          │
                          ▼
                Duplicate Detection
                          │
                          ▼
                 ┌────────────────┐
                 │ Neon PostgreSQL│
                 └────────────────┘
                          │
                          ▼
                    Review / Edit
                          │
               ┌──────────┼──────────┐
               ▼          ▼          ▼
             JSON        CSV       Excel
```

---

# Application Workflow

```text
Upload Invoice
      │
      ▼
File Validation
      │
      ▼
Exact Duplicate Check
      │
      ▼
PDF Text Extraction / OCR
      │
      ▼
Structured Field Extraction
      │
      ▼
Line Item Extraction
      │
      ▼
Confidence Scoring
      │
      ▼
Invoice Validation
      │
      ▼
Advanced Duplicate Detection
      │
      ▼
Manual Review / Edit
      │
      ▼
Revalidation
      │
      ▼
JSON / CSV / Excel Export
```

---

# Extracted Invoice Fields

The system extracts:

| Field | Description |
|---|---|
| Vendor Name | Supplier or company name |
| GSTIN | GST identification number |
| Invoice Number | Unique invoice identifier |
| Invoice Date | Date of invoice |
| Due Date | Payment due date |
| Subtotal | Amount before tax |
| Tax Amount | GST / tax amount |
| Grand Total | Final invoice amount |
| Currency | INR, USD, EUR, etc. |
| Line Items | Products or services in the invoice |

---

# Confidence Scoring

Each extracted field receives a confidence score.

Example:

```text
Vendor Name       96%
GSTIN             99%
Invoice Number    98%
Invoice Date      95%
Subtotal          98%
Tax Amount        98%
Grand Total       99%
Currency          97%
```

The application also calculates an overall invoice confidence score.

Low-confidence extraction can be manually corrected from the Review page.

---

# Validation Engine

The system performs multiple validation checks.

Examples:

```text
Required fields
GSTIN format
Subtotal + Tax = Grand Total
Non-negative amounts
Invoice date validity
Due date validity
Line-item calculations
Line-item totals vs invoice total
```

The final validation status is:

```text
VALID
WARNING
INVALID
```

---

# Duplicate Detection

The application uses two duplicate detection methods.

## 1. Exact File Duplicate Detection

A SHA-256 file hash is generated when an invoice is uploaded.

```text
Same File
   │
   ▼
SHA-256 Match
   │
   ▼
Exact Duplicate
```

## 2. Business-Level Duplicate Detection

The application compares:

- Invoice number
- GSTIN
- Vendor
- Invoice date
- Grand total

The duplicate scoring system supports OCR errors through fuzzy invoice-number matching.

Example:

```text
Original:
IIC429326F097917

OCR Result:
11C429326F09791
```

The system can still identify the invoices as likely duplicates.

---

# Review and Edit

Users can manually review and correct extracted invoice data.

Editable fields include:

- Vendor
- GSTIN
- Invoice number
- Invoice date
- Due date
- Subtotal
- Tax
- Grand total
- Currency
- Line items

After changes are saved, the invoice can be revalidated.

---

# Export Formats

The application supports:

## JSON

Contains:

- Invoice information
- Line items
- Confidence scores
- Validation results

## CSV

Contains:

```text
INVOICE DETAILS
LINE ITEMS
CONFIDENCE SCORES
VALIDATION RESULTS
```

## Excel

The Excel workbook contains four sheets:

```text
Invoice Details
Line Items
Confidence Scores
Validation Results
```

---

# Dashboard

The dashboard displays:

- Total invoices
- Processed invoices
- Duplicate invoices
- Total unique invoice value
- Recent invoices
- Processing status

Duplicate invoices are excluded from the total invoice value.

---

# Application Screenshots

## Dashboard

The dashboard provides a quick overview of uploaded invoices, processed invoices, duplicate invoices, total invoice value, and recent processing activity.

![Dashboard](docs/screenshots/dashboard.png)

---

## Invoice Upload

Users can drag and drop or browse PDF, JPG, JPEG, and PNG invoice files. The interface displays upload progress and tracks every processing stage.

![Invoice Upload](docs/screenshots/upload-invoice.png)

---

## Invoice Review and Edit

The review screen displays extracted fields with confidence scores. Users can manually correct invoice information, edit line items, revalidate data, and export the final result.

![Invoice Review](docs/screenshots/review-invoice.png)

---

## Invoice History

The invoice history page provides search, processing-status filters, duplicate filters, pagination, review actions, and export options.

![Invoice History](docs/screenshots/invoice-history.png)

---

## Swagger API Documentation

FastAPI automatically provides interactive Swagger documentation for testing all invoice-processing APIs.

![Swagger API](docs/screenshots/swagger-api.png)

---

# Invoice History

The Invoice History page supports:

- Search
- Vendor search
- Invoice-number search
- GSTIN search
- File-name search
- Processing-status filter
- Duplicate filter
- Pagination
- Review action
- JSON export
- CSV export
- Excel export

---

# Database Design

The application uses PostgreSQL.

Main tables:

```text
invoices
invoice_items
field_confidences
validation_results
```

## invoices

Stores:

- File information
- File hash
- Vendor information
- Invoice number
- Dates
- Monetary values
- Currency
- OCR text
- Processing status
- Duplicate information

## invoice_items

Stores invoice products/services.

## field_confidences

Stores confidence scores for extracted fields.

## validation_results

Stores individual invoice validation results.

---

# Important API Endpoints

## Invoice Upload

```http
POST /api/invoices/upload
```

## List Invoices

```http
GET /api/invoices
```

## Invoice Details

```http
GET /api/invoices/{invoice_id}
```

## PDF Text Extraction

```http
POST /api/invoices/{invoice_id}/extract-text
```

## OCR

```http
POST /api/invoices/{invoice_id}/ocr
```

## Field Extraction

```http
POST /api/invoices/{invoice_id}/extract-fields
```

## Line Item Extraction

```http
POST /api/invoices/{invoice_id}/extract-line-items
```

## Confidence Scores

```http
POST /api/invoices/{invoice_id}/confidence-scores
```

## Validation

```http
POST /api/invoices/{invoice_id}/validate
```

## Duplicate Detection

```http
POST /api/invoices/{invoice_id}/check-duplicate
```

## Review Invoice

```http
GET /api/invoices/{invoice_id}/review
```

## Update Invoice

```http
PATCH /api/invoices/{invoice_id}/review
```

## Update Line Item

```http
PATCH /api/invoices/{invoice_id}/line-items/{item_id}
```

## Export

```http
GET /api/invoices/{invoice_id}/export/json
GET /api/invoices/{invoice_id}/export/csv
GET /api/invoices/{invoice_id}/export/xlsx
```

---

# Project Structure

```text
AI-Invoice-Extraction-System/
│
├── Dockerfile
├── .dockerignore
├── .gitignore
├── README.md
│
├── backend/
│   │
│   ├── app/
│   │   ├── api/
│   │   │   └── invoices.py
│   │   │
│   │   ├── database/
│   │   │   └── database.py
│   │   │
│   │   ├── models/
│   │   │   └── invoice.py
│   │   │
│   │   ├── schemas/
│   │   │   └── invoice.py
│   │   │
│   │   ├── services/
│   │   │   ├── confidence_service.py
│   │   │   ├── duplicate_service.py
│   │   │   ├── export_service.py
│   │   │   ├── invoice_extractor.py
│   │   │   ├── line_item_extractor.py
│   │   │   ├── ocr_service.py
│   │   │   ├── pdf_extractor.py
│   │   │   └── validation_service.py
│   │   │
│   │   ├── config.py
│   │   └── main.py
│   │
│   ├── uploads/
│   ├── requirements.txt
│   ├── smoke_test.py
│   └── init_db.py
│
└── frontend/
    │
    ├── src/
    │   ├── components/
    │   │   └── Sidebar.jsx
    │   │
    │   ├── pages/
    │   │   ├── Dashboard.jsx
    │   │   ├── UploadInvoice.jsx
    │   │   ├── Invoices.jsx
    │   │   └── ReviewInvoice.jsx
    │   │
    │   ├── services/
    │   │   └── api.js
    │   │
    │   ├── App.jsx
    │   ├── main.jsx
    │   └── index.css
    │
    ├── package.json
    ├── vite.config.js
    └── vercel.json
```

---

# Local Installation

## Prerequisites

Install:

```text
Python 3.12
Node.js
npm
Tesseract OCR
Git
```

---

## Clone Repository

```bash
git clone https://github.com/Boddusai/AI-Invoice-Extraction-System.git
```

```bash
cd AI-Invoice-Extraction-System
```

---

# Backend Setup

Go to:

```bash
cd backend
```

Create environment:

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create:

```text
backend/.env
```

Example:

```env
DATABASE_URL=postgresql+psycopg://USERNAME:PASSWORD@HOST/DATABASE
FRONTEND_URL=http://localhost:5173
```

Do not commit this file.

Start backend:

```bash
uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

---

# Frontend Setup

Open another terminal:

```bash
cd frontend
```

Install packages:

```bash
npm install
```

Create:

```text
frontend/.env
```

Add:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Start frontend:

```bash
npm run dev
```

Open:

```text
http://localhost:5173
```

---

# Backend Smoke Test

Start the FastAPI backend and run:

```bash
python smoke_test.py
```

Expected:

```text
[PASS] Root API
[PASS] Health
[PASS] Database
[PASS] API Info
[PASS] Invoice List

Passed: 5/5
Backend smoke test completed successfully!
```

---

# Docker

The backend is deployed using Docker.

The Docker image includes:

- Python 3.12
- FastAPI
- Tesseract OCR
- OpenCV
- PyMuPDF
- PostgreSQL client dependencies

Build locally:

```bash
docker build -t ai-invoice-api .
```

Run:

```bash
docker run -p 8000:8000 ai-invoice-api
```

---

# Production Deployment

## Frontend

Vercel

```text
https://ai-invoice-extraction-system.vercel.app
```

## Backend

Render

```text
https://ai-invoice-extraction-api.onrender.com
```

## Database

Neon PostgreSQL

Environment variables are used for database credentials and production URLs.

No credentials are stored in the GitHub repository.

---

# Production Architecture

```text
GitHub
   │
   ├──────────────┐
   │              │
   ▼              ▼
Vercel          Render
React           Docker
                 FastAPI
                   │
                   ▼
               Tesseract
                   │
                   ▼
             Neon PostgreSQL
```

---

# Security Considerations

- Database credentials stored in environment variables
- `.env` excluded from Git
- File-type validation
- File-size validation
- Duplicate file hashing
- CORS configuration
- No credentials committed to GitHub

---

# Current Limitations

- OCR accuracy depends on invoice image quality
- Invoice layouts differ between vendors
- Complex tables may require manual review
- Render free instances may have limited CPU/RAM
- Uploaded files on Render are temporary unless persistent storage is configured

---

# Future Improvements

Possible future enhancements:

- Transformer-based invoice extraction
- LayoutLM / Donut document models
- Vendor-specific extraction templates
- Cloud object storage
- User authentication
- Role-based access
- Batch invoice processing
- Email invoice ingestion
- Automatic accounting software integration
- GST API verification
- Invoice approval workflow
- Audit logs
- Dashboard analytics
- Multi-language OCR

---

# Example Successfully Processed Invoice

Example extracted values:

```text
Vendor:
India Central Billing

GSTIN:
06AACCV7324B1ZO

Invoice Number:
IIC429326F097917

Invoice Date:
31/07/2026

Subtotal:
₹422.88

Tax:
₹76.12

Grand Total:
₹499.00

Currency:
INR

Overall Confidence:
97.5%

Validation:
VALID
```

---

# Author

**Sai Pavan**

Python Developer / Full-Stack Developer

---

## License

This project is developed for educational, portfolio, and demonstration purposes.