import {
    AlertCircle,
    CheckCircle2,
    Download,
    FileSearch,
    Loader2,
    RefreshCw,
    Save,
  } from "lucide-react";
  
  import {
    useEffect,
    useMemo,
    useState,
  } from "react";
  
  import {
    useNavigate,
    useParams,
  } from "react-router-dom";
  
  import api from "../services/api";
  
  
  function ReviewInvoice() {
    const params = useParams();
    const navigate = useNavigate();
  
    const [searchId, setSearchId] = useState(
      params.invoiceId || ""
    );
  
    const [invoice, setInvoice] = useState(null);
  
    const [form, setForm] = useState({});
  
    const [items, setItems] = useState([]);
  
    const [confidence, setConfidence] =
      useState(null);
  
    const [validation, setValidation] =
      useState(null);
  
    const [loading, setLoading] =
      useState(false);
  
    const [saving, setSaving] =
      useState(false);
  
    const [revalidating, setRevalidating] =
      useState(false);
  
    const [error, setError] =
      useState("");
  
    const [message, setMessage] =
      useState("");
  
  
    useEffect(() => {
      if (params.invoiceId) {
        loadInvoice(
          params.invoiceId
        );
      }
    }, [params.invoiceId]);
  
  
    const confidenceMap = useMemo(() => {
      const map = {};
  
      confidence?.fields?.forEach(
        (field) => {
          map[field.field_name] =
            field.confidence;
        }
      );
  
      return map;
    }, [confidence]);
  
  
    const loadInvoice = async (id) => {
      if (!id) {
        return;
      }
  
      try {
        setLoading(true);
  
        setError("");
        setMessage("");
  
        const reviewResponse =
          await api.get(
            `/api/invoices/${id}/review`
          );
  
        const reviewData =
          reviewResponse.data;
  
        setInvoice(reviewData);
  
        setForm({
          vendor_name:
            reviewData.vendor_name || "",
  
          vendor_gstin:
            reviewData.vendor_gstin || "",
  
          invoice_number:
            reviewData.invoice_number || "",
  
          invoice_date:
            reviewData.invoice_date || "",
  
          due_date:
            reviewData.due_date || "",
  
          subtotal:
            reviewData.subtotal ?? "",
  
          tax_amount:
            reviewData.tax_amount ?? "",
  
          grand_total:
            reviewData.grand_total ?? "",
  
          currency:
            reviewData.currency || "INR",
        });
  
        setItems(
          reviewData.items || []
        );
  
        /*
         * Try to calculate/display the latest
         * confidence and validation results.
         * If extraction is incomplete, the review
         * page should still remain usable.
         */
        try {
          const confidenceResponse =
            await api.post(
              `/api/invoices/${id}/confidence-scores`
            );
  
          setConfidence(
            confidenceResponse.data
          );
  
        } catch (err) {
          console.warn(
            "Confidence unavailable",
            err
          );
  
          setConfidence(null);
        }
  
  
        try {
          const validationResponse =
            await api.post(
              `/api/invoices/${id}/validate`
            );
  
          setValidation(
            validationResponse.data
          );
  
        } catch (err) {
          console.warn(
            "Validation unavailable",
            err
          );
  
          setValidation(null);
        }
  
      } catch (err) {
        console.error(err);
  
        setInvoice(null);
  
        setError(
          err.response?.data?.detail
          || "Unable to load invoice."
        );
  
      } finally {
        setLoading(false);
      }
    };
  
  
    const handleSearch = () => {
      if (!searchId) {
        setError(
          "Enter an invoice ID."
        );
  
        return;
      }
  
      navigate(
        `/review/${searchId}`
      );
    };
  
  
    const updateField = (
      field,
      value
    ) => {
      setForm(
        (current) => ({
          ...current,
          [field]: value,
        })
      );
    };
  
  
    const saveInvoice = async () => {
      if (!invoice) {
        return;
      }
  
      try {
        setSaving(true);
  
        setError("");
        setMessage("");
  
        const payload = {
          vendor_name:
            form.vendor_name || null,
  
          vendor_gstin:
            form.vendor_gstin || null,
  
          invoice_number:
            form.invoice_number || null,
  
          invoice_date:
            form.invoice_date || null,
  
          due_date:
            form.due_date || null,
  
          subtotal:
            form.subtotal === ""
              ? null
              : Number(
                  form.subtotal
                ),
  
          tax_amount:
            form.tax_amount === ""
              ? null
              : Number(
                  form.tax_amount
                ),
  
          grand_total:
            form.grand_total === ""
              ? null
              : Number(
                  form.grand_total
                ),
  
          currency:
            form.currency || "INR",
        };
  
        const response =
          await api.patch(
            `/api/invoices/${invoice.invoice_id}/review`,
            payload
          );
  
        setInvoice(
          response.data
        );
  
        setMessage(
          "Invoice changes saved successfully."
        );
  
        setConfidence(null);
        setValidation(null);
  
      } catch (err) {
        console.error(err);
  
        setError(
          err.response?.data?.detail
          || "Unable to save invoice."
        );
  
      } finally {
        setSaving(false);
      }
    };
  
  
    const updateItemValue = (
      index,
      field,
      value
    ) => {
      setItems(
        (currentItems) =>
          currentItems.map(
            (item, itemIndex) => {
  
              if (
                itemIndex !== index
              ) {
                return item;
              }
  
              return {
                ...item,
                [field]: value,
              };
            }
          )
      );
    };
  
  
    const saveLineItem = async (
      item,
      index
    ) => {
      try {
        setError("");
        setMessage("");
  
        const payload = {
          description:
            item.description || null,
  
          quantity:
            item.quantity === ""
              ? null
              : Number(
                  item.quantity
                ),
  
          unit_price:
            item.unit_price === ""
              ? null
              : Number(
                  item.unit_price
                ),
  
          tax_rate:
            item.tax_rate === ""
              ? null
              : Number(
                  item.tax_rate
                ),
  
          tax_amount:
            item.tax_amount === ""
              ? null
              : Number(
                  item.tax_amount
                ),
  
          line_total:
            item.line_total === ""
              ? null
              : Number(
                  item.line_total
                ),
        };
  
        const response =
          await api.patch(
            `/api/invoices/${invoice.invoice_id}/line-items/${item.id}`,
            payload
          );
  
        setItems(
          (currentItems) =>
            currentItems.map(
              (
                currentItem,
                itemIndex
              ) =>
                itemIndex === index
                  ? response.data.item
                  : currentItem
            )
        );
  
        setMessage(
          `Line item #${item.id} updated.`
        );
  
        setValidation(null);
  
      } catch (err) {
        console.error(err);
  
        setError(
          err.response?.data?.detail
          || "Unable to update line item."
        );
      }
    };
  
  
    const revalidateInvoice =
      async () => {
  
      if (!invoice) {
        return;
      }
  
      try {
        setRevalidating(true);
  
        setError("");
        setMessage("");
  
        const id =
          invoice.invoice_id;
  
        const confidenceResponse =
          await api.post(
            `/api/invoices/${id}/confidence-scores`
          );
  
        const validationResponse =
          await api.post(
            `/api/invoices/${id}/validate`
          );
  
        const duplicateResponse =
          await api.post(
            `/api/invoices/${id}/check-duplicate`
          );
  
        setConfidence(
          confidenceResponse.data
        );
  
        setValidation(
          validationResponse.data
        );
  
        setInvoice(
          (current) => ({
            ...current,
  
            is_duplicate:
              duplicateResponse.data
                .is_duplicate,
  
            duplicate_of:
              duplicateResponse.data
                .duplicate_of,
  
            processing_status:
              duplicateResponse.data
                .processing_status,
          })
        );
  
        setMessage(
          "Invoice recalculated and revalidated."
        );
  
      } catch (err) {
        console.error(err);
  
        setError(
          err.response?.data?.detail
          || "Revalidation failed."
        );
  
      } finally {
        setRevalidating(false);
      }
    };
  
  
    const exportInvoice = (
      format
    ) => {
      if (!invoice) {
        return;
      }
  
      const url =
        `${api.defaults.baseURL}`
        + `/api/invoices/`
        + `${invoice.invoice_id}`
        + `/export/${format}`;
  
      window.open(
        url,
        "_blank"
      );
    };
  
  
    const getConfidenceClass = (
      fieldName
    ) => {
  
      const value =
        confidenceMap[fieldName];
  
      if (
        value === undefined
        || value === null
      ) {
        return "confidence-badge neutral";
      }
  
      if (value >= 0.9) {
        return "confidence-badge high";
      }
  
      if (value >= 0.7) {
        return "confidence-badge medium";
      }
  
      return "confidence-badge low";
    };
  
  
    const confidenceLabel = (
      fieldName
    ) => {
  
      const value =
        confidenceMap[fieldName];
  
      if (
        value === undefined
        || value === null
      ) {
        return "N/A";
      }
  
      return `${Math.round(
        value * 100
      )}%`;
    };
  
  
    return (
      <div>
  
        <div className="page-header">
  
          <div>
            <h1>
              Review Invoice
            </h1>
  
            <p>
              Review, correct and validate
              extracted invoice data.
            </p>
          </div>
  
        </div>
  
  
        <div className="review-search-card">
  
          <div className="review-search">
  
            <input
              type="number"
              placeholder="Enter Invoice ID"
              value={searchId}
              onChange={(event) =>
                setSearchId(
                  event.target.value
                )
              }
              onKeyDown={(event) => {
                if (
                  event.key
                  === "Enter"
                ) {
                  handleSearch();
                }
              }}
            />
  
            <button
              className="primary-action-button"
              onClick={
                handleSearch
              }
            >
              <FileSearch size={18} />
              Load Invoice
            </button>
  
          </div>
  
        </div>
  
  
        {loading && (
          <div className="content-card review-loading">
  
            <Loader2
              className="spin"
            />
  
            Loading invoice...
  
          </div>
        )}
  
  
        {error && (
          <div className="upload-error">
            <AlertCircle size={18} />
            {error}
          </div>
        )}
  
  
        {message && (
          <div className="success-alert">
            <CheckCircle2 size={18} />
            {message}
          </div>
        )}
  
  
        {!loading && invoice && (
          <>
  
            {invoice.is_duplicate && (
              <div className="duplicate-alert review-duplicate">
  
                <AlertCircle
                  size={21}
                />
  
                <div>
                  <strong>
                    Duplicate invoice
                  </strong>
  
                  <p>
                    This invoice matches
                    Invoice #
                    {invoice.duplicate_of}.
                  </p>
                </div>
  
              </div>
            )}
  
  
            <div className="review-top-grid">
  
              <div className="content-card">
  
                <div className="card-header">
                  <div>
                    <h2>
                      Invoice Details
                    </h2>
  
                    <p>
                      Invoice #
                      {invoice.invoice_id}
                      {" · "}
                      {invoice.file_name}
                    </p>
                  </div>
                </div>
  
  
                <div className="review-form-grid">
  
                  <ReviewField
                    label="Vendor Name"
                    value={
                      form.vendor_name
                    }
                    onChange={(value) =>
                      updateField(
                        "vendor_name",
                        value
                      )
                    }
                    confidence={
                      confidenceLabel(
                        "vendor_name"
                      )
                    }
                    confidenceClass={
                      getConfidenceClass(
                        "vendor_name"
                      )
                    }
                  />
  
  
                  <ReviewField
                    label="GSTIN"
                    value={
                      form.vendor_gstin
                    }
                    onChange={(value) =>
                      updateField(
                        "vendor_gstin",
                        value
                      )
                    }
                    confidence={
                      confidenceLabel(
                        "vendor_gstin"
                      )
                    }
                    confidenceClass={
                      getConfidenceClass(
                        "vendor_gstin"
                      )
                    }
                  />
  
  
                  <ReviewField
                    label="Invoice Number"
                    value={
                      form.invoice_number
                    }
                    onChange={(value) =>
                      updateField(
                        "invoice_number",
                        value
                      )
                    }
                    confidence={
                      confidenceLabel(
                        "invoice_number"
                      )
                    }
                    confidenceClass={
                      getConfidenceClass(
                        "invoice_number"
                      )
                    }
                  />
  
  
                  <ReviewField
                    label="Invoice Date"
                    type="date"
                    value={
                      form.invoice_date
                    }
                    onChange={(value) =>
                      updateField(
                        "invoice_date",
                        value
                      )
                    }
                    confidence={
                      confidenceLabel(
                        "invoice_date"
                      )
                    }
                    confidenceClass={
                      getConfidenceClass(
                        "invoice_date"
                      )
                    }
                  />
  
  
                  <ReviewField
                    label="Due Date"
                    type="date"
                    value={
                      form.due_date
                    }
                    onChange={(value) =>
                      updateField(
                        "due_date",
                        value
                      )
                    }
                    confidence={
                      confidenceLabel(
                        "due_date"
                      )
                    }
                    confidenceClass={
                      getConfidenceClass(
                        "due_date"
                      )
                    }
                  />
  
  
                  <ReviewField
                    label="Subtotal"
                    type="number"
                    step="0.01"
                    value={
                      form.subtotal
                    }
                    onChange={(value) =>
                      updateField(
                        "subtotal",
                        value
                      )
                    }
                    confidence={
                      confidenceLabel(
                        "subtotal"
                      )
                    }
                    confidenceClass={
                      getConfidenceClass(
                        "subtotal"
                      )
                    }
                  />
  
  
                  <ReviewField
                    label="Tax Amount"
                    type="number"
                    step="0.01"
                    value={
                      form.tax_amount
                    }
                    onChange={(value) =>
                      updateField(
                        "tax_amount",
                        value
                      )
                    }
                    confidence={
                      confidenceLabel(
                        "tax_amount"
                      )
                    }
                    confidenceClass={
                      getConfidenceClass(
                        "tax_amount"
                      )
                    }
                  />
  
  
                  <ReviewField
                    label="Grand Total"
                    type="number"
                    step="0.01"
                    value={
                      form.grand_total
                    }
                    onChange={(value) =>
                      updateField(
                        "grand_total",
                        value
                      )
                    }
                    confidence={
                      confidenceLabel(
                        "grand_total"
                      )
                    }
                    confidenceClass={
                      getConfidenceClass(
                        "grand_total"
                      )
                    }
                  />
  
  
                  <div className="review-field">
  
                    <div className="review-field-label">
                      <label>
                        Currency
                      </label>
  
                      <span
                        className={
                          getConfidenceClass(
                            "currency"
                          )
                        }
                      >
                        {confidenceLabel(
                          "currency"
                        )}
                      </span>
                    </div>
  
                    <select
                      value={
                        form.currency
                      }
                      onChange={(event) =>
                        updateField(
                          "currency",
                          event.target.value
                        )
                      }
                    >
                      <option value="INR">
                        INR
                      </option>
  
                      <option value="USD">
                        USD
                      </option>
  
                      <option value="EUR">
                        EUR
                      </option>
  
                      <option value="GBP">
                        GBP
                      </option>
                    </select>
  
                  </div>
  
                </div>
  
  
                <div className="review-actions">
  
                  <button
                    className="primary-action-button"
                    onClick={
                      saveInvoice
                    }
                    disabled={
                      saving
                    }
                  >
  
                    {saving
                      ? (
                        <Loader2
                          className="spin"
                          size={18}
                        />
                      )
                      : (
                        <Save
                          size={18}
                        />
                      )
                    }
  
                    Save Changes
  
                  </button>
  
  
                  <button
                    className="secondary-button review-revalidate-button"
                    onClick={
                      revalidateInvoice
                    }
                    disabled={
                      revalidating
                    }
                  >
  
                    {revalidating
                      ? (
                        <Loader2
                          className="spin"
                          size={17}
                        />
                      )
                      : (
                        <RefreshCw
                          size={17}
                        />
                      )
                    }
  
                    Revalidate
  
                  </button>
  
                </div>
  
              </div>
  
  
              <div className="review-side-column">
  
                <div className="content-card">
  
                  <h2 className="review-card-title">
                    Quality Summary
                  </h2>
  
  
                  <div className="quality-item">
  
                    <span>
                      Overall Confidence
                    </span>
  
                    <strong>
                      {confidence
                        ? `${confidence.overall_confidence_percentage}%`
                        : "N/A"
                      }
                    </strong>
  
                  </div>
  
  
                  <div className="quality-item">
  
                    <span>
                      Validation
                    </span>
  
                    <strong
                      className={
                        validation
                          ?.overall_status
                        === "VALID"
                          ? "quality-valid"
                          : "quality-invalid"
                      }
                    >
                      {validation
                        ?.overall_status
                        || "Not validated"
                      }
                    </strong>
  
                  </div>
  
  
                  <div className="quality-item">
  
                    <span>
                      Duplicate
                    </span>
  
                    <strong>
                      {invoice.is_duplicate
                        ? "Yes"
                        : "No"
                      }
                    </strong>
  
                  </div>
  
                </div>
  
  
                <div className="content-card">
  
                  <h2 className="review-card-title">
                    Export
                  </h2>
  
  
                  <div className="export-buttons">
  
                    <button
                      onClick={() =>
                        exportInvoice(
                          "json"
                        )
                      }
                    >
                      <Download
                        size={16}
                      />
                      JSON
                    </button>
  
  
                    <button
                      onClick={() =>
                        exportInvoice(
                          "csv"
                        )
                      }
                    >
                      <Download
                        size={16}
                      />
                      CSV
                    </button>
  
  
                    <button
                      onClick={() =>
                        exportInvoice(
                          "xlsx"
                        )
                      }
                    >
                      <Download
                        size={16}
                      />
                      Excel
                    </button>
  
                  </div>
  
                </div>
  
              </div>
  
            </div>
  
  
            <div className="content-card review-section">
  
              <div className="card-header">
  
                <div>
                  <h2>
                    Line Items
                  </h2>
  
                  <p>
                    Review and correct
                    extracted products
                    or services.
                  </p>
                </div>
  
              </div>
  
  
              {items.length === 0 ? (
  
                <div className="empty-state">
                  No line items were extracted.
                </div>
  
              ) : (
  
                <div className="table-wrapper">
  
                  <table className="edit-items-table">
  
                    <thead>
                      <tr>
                        <th>
                          Description
                        </th>
  
                        <th>
                          Qty
                        </th>
  
                        <th>
                          Unit Price
                        </th>
  
                        <th>
                          Tax %
                        </th>
  
                        <th>
                          Tax
                        </th>
  
                        <th>
                          Total
                        </th>
  
                        <th>
                          Action
                        </th>
                      </tr>
                    </thead>
  
  
                    <tbody>
  
                      {items.map(
                        (
                          item,
                          index
                        ) => (
  
                        <tr key={item.id}>
  
                          <td>
                            <input
                              value={
                                item.description
                                || ""
                              }
                              onChange={
                                (event) =>
                                  updateItemValue(
                                    index,
                                    "description",
                                    event.target.value
                                  )
                              }
                            />
                          </td>
  
  
                          <td>
                            <input
                              type="number"
                              value={
                                item.quantity
                                ?? ""
                              }
                              onChange={
                                (event) =>
                                  updateItemValue(
                                    index,
                                    "quantity",
                                    event.target.value
                                  )
                              }
                            />
                          </td>
  
  
                          <td>
                            <input
                              type="number"
                              step="0.01"
                              value={
                                item.unit_price
                                ?? ""
                              }
                              onChange={
                                (event) =>
                                  updateItemValue(
                                    index,
                                    "unit_price",
                                    event.target.value
                                  )
                              }
                            />
                          </td>
  
  
                          <td>
                            <input
                              type="number"
                              step="0.01"
                              value={
                                item.tax_rate
                                ?? ""
                              }
                              onChange={
                                (event) =>
                                  updateItemValue(
                                    index,
                                    "tax_rate",
                                    event.target.value
                                  )
                              }
                            />
                          </td>
  
  
                          <td>
                            <input
                              type="number"
                              step="0.01"
                              value={
                                item.tax_amount
                                ?? ""
                              }
                              onChange={
                                (event) =>
                                  updateItemValue(
                                    index,
                                    "tax_amount",
                                    event.target.value
                                  )
                              }
                            />
                          </td>
  
  
                          <td>
                            <input
                              type="number"
                              step="0.01"
                              value={
                                item.line_total
                                ?? ""
                              }
                              onChange={
                                (event) =>
                                  updateItemValue(
                                    index,
                                    "line_total",
                                    event.target.value
                                  )
                              }
                            />
                          </td>
  
  
                          <td>
                            <button
                              className="small-save-button"
                              onClick={() =>
                                saveLineItem(
                                  item,
                                  index
                                )
                              }
                            >
                              Save
                            </button>
                          </td>
  
                        </tr>
  
                      ))}
  
                    </tbody>
  
                  </table>
  
                </div>
              )}
  
            </div>
  
  
            <div className="content-card review-section">
  
              <div className="card-header">
                <div>
                  <h2>
                    Validation Results
                  </h2>
  
                  <p>
                    Automated checks performed
                    on this invoice.
                  </p>
                </div>
              </div>
  
  
              {!validation ? (
  
                <div className="empty-state">
                  Revalidate the invoice to
                  view validation results.
                </div>
  
              ) : (
  
                <div className="validation-list">
  
                  {validation.validations.map(
                    (result) => (
  
                    <div
                      className="validation-row"
                      key={result.id}
                    >
  
                      <div
                        className={
                          result.status
                          === "passed"
                            ? "validation-icon passed"
                            : result.status
                            === "warning"
                              ? "validation-icon warning"
                              : "validation-icon failed"
                        }
                      >
  
                        {result.status
                        === "passed"
                          ? (
                            <CheckCircle2
                              size={17}
                            />
                          )
                          : (
                            <AlertCircle
                              size={17}
                            />
                          )
                        }
  
                      </div>
  
  
                      <div>
  
                        <strong>
                          {result.rule_name
                            .replaceAll(
                              "_",
                              " "
                            )
                          }
                        </strong>
  
                        <span>
                          {result.message}
                        </span>
  
                      </div>
  
                    </div>
  
                  ))}
  
                </div>
              )}
  
            </div>
  
          </>
        )}
  
      </div>
    );
  }
  
  
  function ReviewField({
    label,
    value,
    onChange,
    type = "text",
    step,
    confidence,
    confidenceClass,
  }) {
    return (
      <div className="review-field">
  
        <div className="review-field-label">
  
          <label>
            {label}
          </label>
  
          <span
            className={
              confidenceClass
            }
          >
            {confidence}
          </span>
  
        </div>
  
  
        <input
          type={type}
          step={step}
          value={value ?? ""}
          onChange={(event) =>
            onChange(
              event.target.value
            )
          }
        />
  
      </div>
    );
  }
  
  
  export default ReviewInvoice;