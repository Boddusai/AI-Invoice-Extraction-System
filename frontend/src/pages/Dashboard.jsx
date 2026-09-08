import { useEffect, useMemo, useState } from "react";

import {
  AlertTriangle,
  CheckCircle2,
  FileText,
  IndianRupee,
  RefreshCw,
  Upload,
} from "lucide-react";

import {
    Link,
    useNavigate,
} from "react-router-dom";

import api from "../services/api";


function Dashboard() {
  const navigate = useNavigate();
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");


  useEffect(() => {
    loadInvoices();
  }, []);


  const loadInvoices = async () => {
    try {
      setLoading(true);

      const response = await api.get(
        "/api/invoices"
      );

      setInvoices(response.data);
      setError("");

    } catch (err) {
      console.error(err);

      setError(
        "Unable to load invoices from the backend."
      );

    } finally {
      setLoading(false);
    }
  };


  const stats = useMemo(() => {

    const total = invoices.length;

    const processed = invoices.filter(
      (invoice) =>
        [
          "fields_extracted",
          "line_items_extracted",
          "confidence_scored",
          "validated",
          "duplicate_checked",
          "duplicate_detected",
          "reviewed",
        ].includes(
          invoice.processing_status
        )
    ).length;

    const duplicates = invoices.filter(
      (invoice) => invoice.is_duplicate
    ).length;

    const totalValue = invoices.reduce(
      (sum, invoice) => {
    
        if (invoice.is_duplicate) {
          return sum;
        }
    
        return (
          sum
          + Number(
              invoice.grand_total || 0
            )
        );
    
      },
      0
    );

    return {
      total,
      processed,
      duplicates,
      totalValue,
    };

  }, [invoices]);


  const formatCurrency = (value) => {
    return new Intl.NumberFormat(
      "en-IN",
      {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 2,
      }
    ).format(
      Number(value || 0)
    );
  };


  const formatDate = (value) => {
    if (!value) {
      return "-";
    }

    return new Date(
      `${value}T00:00:00`
    ).toLocaleDateString(
      "en-IN"
    );
  };


  const getStatusClass = (invoice) => {

    if (invoice.is_duplicate) {
      return "status duplicate";
    }

    if (
      invoice.processing_status
      === "validated"
    ) {
      return "status validated";
    }

    if (
      [
        "duplicate_checked",
        "reviewed",
        "confidence_scored",
        "line_items_extracted",
        "fields_extracted",
      ].includes(
        invoice.processing_status
      )
    ) {
      return "status processed";
    }

    return "status pending";
  };


  const getStatusText = (invoice) => {

    if (invoice.is_duplicate) {
      return "Duplicate";
    }

    const map = {
      uploaded: "Uploaded",
      text_extracted: "Text Extracted",
      ocr_completed: "OCR Complete",
      fields_extracted: "Fields Extracted",
      line_items_extracted: "Items Extracted",
      confidence_scored: "Scored",
      validated: "Validated",
      duplicate_checked: "Processed",
      reviewed: "Reviewed",
    };

    return (
      map[invoice.processing_status]
      || invoice.processing_status
    );
  };


  return (
    <div>

      <div className="page-header">
        <div>
          <h1>Dashboard</h1>

          <p>
            Monitor invoice extraction,
            validation and processing.
          </p>
        </div>

        <div className="dashboard-header-actions">

            <button
                className="secondary-button history-refresh-button"
                onClick={loadInvoices}
            >
                <RefreshCw size={17} />

                Refresh
            </button>

            <Link
                to="/upload"
                className="primary-button"
            >
                <Upload size={18} />

                Upload Invoice
            </Link>

        </div>
      </div>


      <div className="stats-grid">

        <div className="stat-card">
          <div className="stat-icon">
            <FileText />
          </div>

          <div>
            <span>Total Invoices</span>
            <h2>{stats.total}</h2>
          </div>
        </div>


        <div className="stat-card">
          <div className="stat-icon">
            <CheckCircle2 />
          </div>

          <div>
            <span>Processed</span>
            <h2>{stats.processed}</h2>
          </div>
        </div>


        <div className="stat-card">
          <div className="stat-icon">
            <AlertTriangle />
          </div>

          <div>
            <span>Duplicates</span>
            <h2>{stats.duplicates}</h2>
          </div>
        </div>


        <div className="stat-card">
          <div className="stat-icon">
            <IndianRupee />
          </div>

          <div>
            <span>Total Value</span>

            <h2 className="currency-stat">
              {formatCurrency(
                stats.totalValue
              )}
            </h2>
          </div>
        </div>

      </div>


      <div className="content-card">

        <div className="card-header">

          <div>
            <h2>Recent Invoices</h2>
            <p>
              Latest invoices processed
              by the system.
            </p>
          </div>

          <Link
            to="/invoices"
            className="text-button"
          >
            View all
          </Link>

        </div>


        {loading && (
          <div className="table-message">
            Loading invoices...
          </div>
        )}


        {error && (
          <div className="error-message">
            {error}
          </div>
        )}


        {!loading && !error && (
          <div className="table-wrapper">

            <table className="invoice-table">

              <thead>
                <tr>
                  <th>ID</th>
                  <th>Vendor</th>
                  <th>Invoice Number</th>
                  <th>Date</th>
                  <th>Total</th>
                  <th>Status</th>
                </tr>
              </thead>

              <tbody>

                {invoices
                  .slice(0, 8)
                  .map((invoice) => (

                    <tr
                        key={invoice.id}
                        className="clickable-row"
                        onClick={() =>
                            navigate(
                                `/review/${invoice.id}`
                            )
                        }
                    >

                    <td>
                      #{invoice.id}
                    </td>

                    <td className="vendor-cell">
                      {invoice.vendor_name
                        || "Not extracted"}
                    </td>

                    <td>
                      {invoice.invoice_number
                        || "-"}
                    </td>

                    <td>
                      {formatDate(
                        invoice.invoice_date
                      )}
                    </td>

                    <td>
                      {invoice.grand_total
                        ? formatCurrency(
                            invoice.grand_total
                          )
                        : "-"}
                    </td>

                    <td>
                      <span
                        className={
                          getStatusClass(
                            invoice
                          )
                        }
                      >
                        {getStatusText(
                          invoice
                        )}
                      </span>
                    </td>

                  </tr>

                ))}

              </tbody>

            </table>


            {invoices.length === 0 && (
              <div className="empty-state">
                No invoices have been
                uploaded yet.
              </div>
            )}

          </div>
        )}

      </div>

    </div>
  );
}

export default Dashboard;