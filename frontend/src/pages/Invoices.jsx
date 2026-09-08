import {
    Download,
    FileSearch,
    RefreshCw,
    Search,
  } from "lucide-react";
  
  import {
    useEffect,
    useMemo,
    useState,
  } from "react";
  
  import {
    Link,
  } from "react-router-dom";
  
  import api from "../services/api";
  
  
  function Invoices() {
    const [invoices, setInvoices] =
      useState([]);
  
    const [loading, setLoading] =
      useState(true);
  
    const [error, setError] =
      useState("");
  
    const [search, setSearch] =
      useState("");
  
    const [statusFilter, setStatusFilter] =
      useState("all");
  
    const [duplicateFilter, setDuplicateFilter] =
      useState("all");
  
    const [currentPage, setCurrentPage] =
      useState(1);
  
    const pageSize = 6;
  
  
    useEffect(() => {
      loadInvoices();
    }, []);
  
  
    useEffect(() => {
      setCurrentPage(1);
    }, [
      search,
      statusFilter,
      duplicateFilter,
    ]);
  
  
    const loadInvoices = async () => {
      try {
        setLoading(true);
  
        const response =
          await api.get(
            "/api/invoices"
          );
  
        setInvoices(
          response.data
        );
  
        setError("");
  
      } catch (err) {
        console.error(err);
  
        setError(
          "Unable to load invoice history."
        );
  
      } finally {
        setLoading(false);
      }
    };
  
  
    const filteredInvoices =
      useMemo(() => {
  
        let result = [
          ...invoices
        ];
  
  
        // -------------------------
        // Search
        // -------------------------
  
        const query =
          search
            .trim()
            .toLowerCase();
  
        if (query) {
          result = result.filter(
            (invoice) => {
  
              const values = [
                invoice.id,
                invoice.file_name,
                invoice.vendor_name,
                invoice.invoice_number,
                invoice.vendor_gstin,
              ];
  
              return values.some(
                (value) =>
                  String(
                    value || ""
                  )
                    .toLowerCase()
                    .includes(
                      query
                    )
              );
            }
          );
        }
  
  
        // -------------------------
        // Status filter
        // -------------------------
  
        if (
          statusFilter !== "all"
        ) {
          result = result.filter(
            (invoice) =>
              invoice.processing_status
              === statusFilter
          );
        }
  
  
        // -------------------------
        // Duplicate filter
        // -------------------------
  
        if (
          duplicateFilter === "duplicate"
        ) {
          result = result.filter(
            (invoice) =>
              invoice.is_duplicate
          );
        }
  
        if (
          duplicateFilter === "unique"
        ) {
          result = result.filter(
            (invoice) =>
              !invoice.is_duplicate
          );
        }
  
  
        // -------------------------
        // Newest invoice first
        // -------------------------
  
        result.sort(
          (a, b) =>
            b.id - a.id
        );
  
        return result;
  
      }, [
        invoices,
        search,
        statusFilter,
        duplicateFilter,
      ]);
  
  
    const totalPages =
      Math.max(
        1,
        Math.ceil(
          filteredInvoices.length
          / pageSize
        )
      );
  
  
    const paginatedInvoices =
      filteredInvoices.slice(
        (currentPage - 1)
          * pageSize,
  
        currentPage
          * pageSize
      );
  
  
    const formatCurrency = (
      value,
      currency = "INR"
    ) => {
  
      if (
        value === null
        || value === undefined
      ) {
        return "-";
      }
  
      try {
        return new Intl.NumberFormat(
          "en-IN",
          {
            style: "currency",
            currency:
              currency || "INR",
            maximumFractionDigits: 2,
          }
        ).format(
          Number(value)
        );
  
      } catch {
        return `${value}`;
      }
    };
  
  
    const formatDate = (
      value
    ) => {
  
      if (!value) {
        return "-";
      }
  
      return new Date(
        `${value}T00:00:00`
      ).toLocaleDateString(
        "en-IN"
      );
    };
  
  
    const getStatusText = (
      invoice
    ) => {
  
      if (
        invoice.is_duplicate
      ) {
        return "Duplicate";
      }
  
      const statuses = {
        uploaded:
          "Uploaded",
  
        text_extracted:
          "Text Extracted",
  
        ocr_required:
          "OCR Required",
  
        ocr_processing:
          "OCR Processing",
  
        ocr_completed:
          "OCR Complete",
  
        fields_extracted:
          "Fields Extracted",
  
        line_items_extracted:
          "Items Extracted",
  
        confidence_scored:
          "Scored",
  
        validated:
          "Validated",
  
        reviewed:
          "Reviewed",
  
        duplicate_checked:
          "Processed",
  
        duplicate_detected:
          "Duplicate",
      };
  
      return (
        statuses[
          invoice.processing_status
        ]
        || invoice.processing_status
        || "Unknown"
      );
    };
  
  
    const getStatusClass = (
      invoice
    ) => {
  
      if (
        invoice.is_duplicate
      ) {
        return "history-status duplicate";
      }
  
      if (
        invoice.processing_status
        === "validated"
      ) {
        return "history-status validated";
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
        return "history-status processed";
      }
  
      return "history-status pending";
    };
  
  
    const exportInvoice = (
      invoiceId,
      format
    ) => {
  
      const url =
        `${api.defaults.baseURL}`
        + `/api/invoices/`
        + `${invoiceId}`
        + `/export/${format}`;
  
      window.open(
        url,
        "_blank"
      );
    };
  
  
    const resetFilters = () => {
      setSearch("");
      setStatusFilter("all");
      setDuplicateFilter("all");
      setCurrentPage(1);
    };
  
  
    return (
      <div>
  
        <div className="page-header">
  
          <div>
            <h1>
              Invoice History
            </h1>
  
            <p>
              Search, review and export
              previously processed invoices.
            </p>
          </div>
  
  
          <button
            className="secondary-button history-refresh-button"
            onClick={
              loadInvoices
            }
          >
            <RefreshCw
              size={17}
            />
  
            Refresh
          </button>
  
        </div>
  
  
        <div className="content-card history-filter-card">
  
          <div className="history-filters">
  
            <div className="history-search-box">
  
              <Search
                size={18}
              />
  
              <input
                type="text"
                placeholder={
                  "Search vendor, invoice number, GSTIN or file..."
                }
                value={search}
                onChange={
                  (event) =>
                    setSearch(
                      event.target.value
                    )
                }
              />
  
            </div>
  
  
            <select
              value={
                statusFilter
              }
              onChange={
                (event) =>
                  setStatusFilter(
                    event.target.value
                  )
              }
            >
              <option value="all">
                All Statuses
              </option>
  
              <option value="uploaded">
                Uploaded
              </option>
  
              <option value="text_extracted">
                Text Extracted
              </option>
  
              <option value="ocr_completed">
                OCR Complete
              </option>
  
              <option value="fields_extracted">
                Fields Extracted
              </option>
  
              <option value="line_items_extracted">
                Items Extracted
              </option>
  
              <option value="confidence_scored">
                Confidence Scored
              </option>
  
              <option value="validated">
                Validated
              </option>
  
              <option value="reviewed">
                Reviewed
              </option>
  
              <option value="duplicate_checked">
                Processed
              </option>
  
              <option value="duplicate_detected">
                Duplicate Detected
              </option>
            </select>
  
  
            <select
              value={
                duplicateFilter
              }
              onChange={
                (event) =>
                  setDuplicateFilter(
                    event.target.value
                  )
              }
            >
              <option value="all">
                All Invoices
              </option>
  
              <option value="unique">
                Unique Only
              </option>
  
              <option value="duplicate">
                Duplicates Only
              </option>
            </select>
  
  
            <button
              className="history-reset-button"
              onClick={
                resetFilters
              }
            >
              Clear Filters
            </button>
  
          </div>
  
        </div>
  
  
        <div className="content-card history-table-card">
  
          <div className="card-header">
  
            <div>
              <h2>
                All Invoices
              </h2>
  
              <p>
                {
                  filteredInvoices.length
                }
                {" "}
                invoice(s) found
              </p>
            </div>
  
          </div>
  
  
          {loading && (
            <div className="table-message">
              Loading invoice history...
            </div>
          )}
  
  
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}
  
  
          {!loading
            && !error
            && filteredInvoices.length
            === 0
            && (
              <div className="history-empty">
  
                <FileSearch
                  size={38}
                />
  
                <h3>
                  No invoices found
                </h3>
  
                <p>
                  Try changing your search
                  or filter options.
                </p>
  
              </div>
            )}
  
  
          {!loading
            && !error
            && filteredInvoices.length
            > 0
            && (
            <>
  
              <div className="table-wrapper">
  
                <table className="history-table">
  
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Vendor</th>
                      <th>Invoice Number</th>
                      <th>Date</th>
                      <th>Total</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
  
  
                  <tbody>
  
                    {paginatedInvoices.map(
                      (invoice) => (
  
                      <tr
                        key={
                          invoice.id
                        }
                      >
  
                        <td>
                          <strong>
                            #{invoice.id}
                          </strong>
                        </td>
  
  
                        <td>
                          <div className="history-vendor">
  
                            <strong>
                              {
                                invoice.vendor_name
                                || "Not extracted"
                              }
                            </strong>
  
                            <span>
                              {
                                invoice.file_name
                              }
                            </span>
  
                          </div>
                        </td>
  
  
                        <td>
                          {
                            invoice.invoice_number
                            || "-"
                          }
                        </td>
  
  
                        <td>
                          {formatDate(
                            invoice.invoice_date
                          )}
                        </td>
  
  
                        <td>
                          <strong>
                            {formatCurrency(
                              invoice.grand_total,
                              invoice.currency
                            )}
                          </strong>
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
  
  
                        <td>
  
                          <div className="history-actions">
  
                            <Link
                              to={
                                `/review/${invoice.id}`
                              }
                              className="history-review-button"
                            >
                              Review
                            </Link>
  
  
                            <div className="history-export-menu">
  
                              <button
                                title="Export JSON"
                                onClick={() =>
                                  exportInvoice(
                                    invoice.id,
                                    "json"
                                  )
                                }
                              >
                                JSON
                              </button>
  
  
                              <button
                                title="Export CSV"
                                onClick={() =>
                                  exportInvoice(
                                    invoice.id,
                                    "csv"
                                  )
                                }
                              >
                                CSV
                              </button>
  
  
                              <button
                                title="Export Excel"
                                onClick={() =>
                                  exportInvoice(
                                    invoice.id,
                                    "xlsx"
                                  )
                                }
                              >
                                <Download
                                  size={14}
                                />
  
                                Excel
                              </button>
  
                            </div>
  
                          </div>
  
                        </td>
  
                      </tr>
  
                    ))}
  
                  </tbody>
  
                </table>
  
              </div>
  
  
              <div className="history-pagination">
  
                <div>
                  Page
                  {" "}
                  <strong>
                    {currentPage}
                  </strong>
                  {" "}
                  of
                  {" "}
                  <strong>
                    {totalPages}
                  </strong>
                </div>
  
  
                <div className="pagination-buttons">
  
                  <button
                    onClick={() =>
                      setCurrentPage(
                        (page) =>
                          Math.max(
                            1,
                            page - 1
                          )
                      )
                    }
                    disabled={
                      currentPage === 1
                    }
                  >
                    Previous
                  </button>
  
  
                  {Array.from(
                    {
                      length:
                        totalPages,
                    },
                    (_, index) =>
                      index + 1
                  )
                    .slice(
                      Math.max(
                        0,
                        currentPage - 3
                      ),
                      currentPage + 2
                    )
                    .map(
                      (page) => (
  
                      <button
                        key={page}
                        className={
                          page
                          === currentPage
                            ? "active"
                            : ""
                        }
                        onClick={() =>
                          setCurrentPage(
                            page
                          )
                        }
                      >
                        {page}
                      </button>
  
                    ))}
  
  
                  <button
                    onClick={() =>
                      setCurrentPage(
                        (page) =>
                          Math.min(
                            totalPages,
                            page + 1
                          )
                      )
                    }
                    disabled={
                      currentPage
                      === totalPages
                    }
                  >
                    Next
                  </button>
  
                </div>
  
              </div>
  
            </>
          )}
  
        </div>
  
      </div>
    );
  }
  
  
  export default Invoices;