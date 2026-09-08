import {
    AlertCircle,
    CheckCircle2,
    FileImage,
    FileText,
    Loader2,
    Upload,
    X,
  } from "lucide-react";
  
  import {
    useRef,
    useState,
  } from "react";
  
  import api from "../services/api";

  import {
    Link,
  } from "react-router-dom";
  
  
  function UploadInvoice() {
    const inputRef = useRef(null);
  
    const [selectedFile, setSelectedFile] =
      useState(null);
  
    const [dragActive, setDragActive] =
      useState(false);
  
    const [uploading, setUploading] =
      useState(false);
  
    const [processing, setProcessing] =
      useState(false);
  
    const [uploadProgress, setUploadProgress] =
      useState(0);
  
    const [invoiceId, setInvoiceId] =
      useState(null);
  
    const [uploadResult, setUploadResult] =
      useState(null);
  
    const [processResult, setProcessResult] =
      useState(null);
  
    const [error, setError] =
      useState("");
  
    const [steps, setSteps] = useState([]);
  
  
    const allowedExtensions = [
      "pdf",
      "jpg",
      "jpeg",
      "png",
    ];
  
  
    const validateFile = (file) => {
      if (!file) {
        return false;
      }
  
      const extension =
        file.name
          .split(".")
          .pop()
          .toLowerCase();
  
      if (
        !allowedExtensions.includes(
          extension
        )
      ) {
        setError(
          "Only PDF, JPG, JPEG and PNG files are allowed."
        );
  
        return false;
      }
  
      const maxSize =
        10 * 1024 * 1024;
  
      if (file.size > maxSize) {
        setError(
          "File must be smaller than 10 MB."
        );
  
        return false;
      }
  
      setError("");
  
      return true;
    };
  
  
    const selectFile = (file) => {
      if (!validateFile(file)) {
        return;
      }
  
      setSelectedFile(file);
  
      setUploadResult(null);
      setProcessResult(null);
  
      setInvoiceId(null);
  
      setUploadProgress(0);
  
      setSteps([]);
    };
  
  
    const handleInputChange = (event) => {
      const file =
        event.target.files?.[0];
  
      selectFile(file);
    };
  
  
    const handleDragOver = (event) => {
      event.preventDefault();
  
      setDragActive(true);
    };
  
  
    const handleDragLeave = (event) => {
      event.preventDefault();
  
      setDragActive(false);
    };
  
  
    const handleDrop = (event) => {
      event.preventDefault();
  
      setDragActive(false);
  
      const file =
        event.dataTransfer.files?.[0];
  
      selectFile(file);
    };
  
  
    const clearFile = () => {
      setSelectedFile(null);
  
      setUploadResult(null);
      setProcessResult(null);
  
      setInvoiceId(null);
  
      setUploadProgress(0);
      setSteps([]);
  
      setError("");
  
      if (inputRef.current) {
        inputRef.current.value = "";
      }
    };
  
  
    const formatFileSize = (bytes) => {
      if (bytes < 1024) {
        return `${bytes} B`;
      }
  
      if (
        bytes < 1024 * 1024
      ) {
        return `${(
          bytes / 1024
        ).toFixed(1)} KB`;
      }
  
      return `${(
        bytes
        / (1024 * 1024)
      ).toFixed(2)} MB`;
    };
  
  
    const addStep = (
      name,
      status,
      message = ""
    ) => {
      setSteps(
        (currentSteps) => [
          ...currentSteps,
          {
            name,
            status,
            message,
          },
        ]
      );
    };
  
  
    const uploadInvoice = async () => {
      if (!selectedFile) {
        setError(
          "Please select an invoice first."
        );
  
        return;
      }
  
      try {
        setUploading(true);
  
        setError("");
        setUploadResult(null);
        setProcessResult(null);
  
        setUploadProgress(0);
        setSteps([]);
  
        const formData =
          new FormData();
  
        formData.append(
          "file",
          selectedFile
        );
  
        const response =
          await api.post(
            "/api/invoices/upload",
            formData,
            {
              onUploadProgress: (
                progressEvent
              ) => {
                if (
                  !progressEvent.total
                ) {
                  return;
                }
  
                const percentage =
                  Math.round(
                    (
                      progressEvent.loaded
                      * 100
                    )
                    / progressEvent.total
                  );
  
                setUploadProgress(
                  percentage
                );
              },
            }
          );
  
        setUploadResult(
          response.data
        );
  
        setInvoiceId(
          response.data.id
        );
  
        if (
          response.data.is_duplicate
        ) {
          setError("");
  
          addStep(
            "Upload",
            "warning",
            "Exact duplicate file detected."
          );
        } else {
          addStep(
            "Upload",
            "success",
            "Invoice uploaded successfully."
          );
        }
  
      } catch (err) {
        console.error(err);
  
        setError(
          err.response?.data?.detail
          || "Invoice upload failed."
        );
  
      } finally {
        setUploading(false);
      }
    };
  
  
    const processInvoice = async () => {
      if (!invoiceId) {
        return;
      }
  
      try {
        setProcessing(true);
  
        setError("");
        setProcessResult(null);
  
        const extension =
          selectedFile.name
            .split(".")
            .pop()
            .toLowerCase();
  
        // =============================
        // PDF text extraction / OCR
        // =============================
  
        if (extension === "pdf") {
          addStep(
            "Text Extraction",
            "processing",
            "Reading PDF..."
          );
  
          const textResponse =
            await api.post(
              `/api/invoices/${invoiceId}/extract-text`
            );
  
          if (
            textResponse.data
              .processing_status
            === "ocr_required"
          ) {
            addStep(
              "Text Extraction",
              "warning",
              "Scanned PDF detected. OCR required."
            );
  
            addStep(
              "OCR",
              "processing",
              "Running OCR..."
            );
  
            await api.post(
              `/api/invoices/${invoiceId}/ocr`
            );
  
            addStep(
              "OCR",
              "success",
              "OCR completed."
            );
  
          } else {
            addStep(
              "Text Extraction",
              "success",
              "PDF text extracted."
            );
          }
  
        } else {
          addStep(
            "OCR",
            "processing",
            "Reading invoice image..."
          );
  
          await api.post(
            `/api/invoices/${invoiceId}/ocr`
          );
  
          addStep(
            "OCR",
            "success",
            "OCR completed."
          );
        }
  
  
        // =============================
        // Field extraction
        // =============================
  
        addStep(
          "Field Extraction",
          "processing",
          "Extracting invoice fields..."
        );
  
        const fieldsResponse =
          await api.post(
            `/api/invoices/${invoiceId}/extract-fields`
          );
  
        addStep(
          "Field Extraction",
          "success",
          "Invoice fields extracted."
        );
  
  
        // =============================
        // Line items
        // =============================
  
        addStep(
          "Line Items",
          "processing",
          "Extracting line items..."
        );
  
        try {
          await api.post(
            `/api/invoices/${invoiceId}/extract-line-items`
          );
  
          addStep(
            "Line Items",
            "success",
            "Line items extracted."
          );
  
        } catch (lineItemError) {
          console.warn(
            lineItemError
          );
  
          addStep(
            "Line Items",
            "warning",
            "No line items could be extracted."
          );
        }
  
  
        // =============================
        // Confidence
        // =============================
  
        addStep(
          "Confidence",
          "processing",
          "Calculating confidence..."
        );
  
        const confidenceResponse =
          await api.post(
            `/api/invoices/${invoiceId}/confidence-scores`
          );
  
        addStep(
          "Confidence",
          "success",
          `${confidenceResponse.data.overall_confidence_percentage}% overall confidence`
        );
  
  
        // =============================
        // Validation
        // =============================
  
        addStep(
          "Validation",
          "processing",
          "Validating invoice..."
        );
  
        const validationResponse =
          await api.post(
            `/api/invoices/${invoiceId}/validate`
          );
  
        addStep(
          "Validation",
          validationResponse.data
            .overall_status
          === "VALID"
            ? "success"
            : "warning",
          validationResponse.data
            .overall_status
        );
  
  
        // =============================
        // Duplicate detection
        // =============================
  
        addStep(
          "Duplicate Check",
          "processing",
          "Checking existing invoices..."
        );
  
        const duplicateResponse =
          await api.post(
            `/api/invoices/${invoiceId}/check-duplicate`
          );
  
        addStep(
          "Duplicate Check",
          duplicateResponse.data
            .is_duplicate
            ? "warning"
            : "success",
          duplicateResponse.data
            .is_duplicate
            ? `Duplicate of Invoice #${duplicateResponse.data.duplicate_of}`
            : "No duplicate detected."
        );
  
  
        setProcessResult({
          fields:
            fieldsResponse.data,
  
          confidence:
            confidenceResponse.data,
  
          validation:
            validationResponse.data,
  
          duplicate:
            duplicateResponse.data,
        });
  
      } catch (err) {
        console.error(err);
  
        setError(
          err.response?.data?.detail
          || "Invoice processing failed."
        );
  
        addStep(
          "Processing",
          "error",
          err.response?.data?.detail
          || "Processing failed."
        );
  
      } finally {
        setProcessing(false);
      }
    };
  
  
    return (
      <div>
  
        <div className="page-header">
          <div>
            <h1>
              Upload Invoice
            </h1>
  
            <p>
              Upload PDF or image invoices
              for automatic extraction and
              validation.
            </p>
          </div>
        </div>
  
  
        <div className="upload-layout">
  
          <div className="content-card">
  
            <div
              className={
                dragActive
                  ? "drop-zone active"
                  : "drop-zone"
              }
              onDragOver={
                handleDragOver
              }
              onDragLeave={
                handleDragLeave
              }
              onDrop={
                handleDrop
              }
              onClick={() =>
                inputRef.current?.click()
              }
            >
  
              <input
                ref={inputRef}
                type="file"
                hidden
                accept=".pdf,.jpg,.jpeg,.png"
                onChange={
                  handleInputChange
                }
              />
  
              <div className="upload-circle">
                <Upload size={28} />
              </div>
  
              <h3>
                Drag & drop your invoice
              </h3>
  
              <p>
                or click to browse files
              </p>
  
              <span>
                PDF, JPG, JPEG or PNG
                · Max 10 MB
              </span>
  
            </div>
  
  
            {selectedFile && (
              <div className="selected-file">
  
                <div className="file-preview-icon">
  
                  {selectedFile.type
                    .includes("pdf")
                    ? (
                      <FileText
                        size={25}
                      />
                    )
                    : (
                      <FileImage
                        size={25}
                      />
                    )}
  
                </div>
  
  
                <div className="selected-file-info">
  
                  <strong>
                    {selectedFile.name}
                  </strong>
  
                  <span>
                    {formatFileSize(
                      selectedFile.size
                    )}
                  </span>
  
                </div>
  
  
                <button
                  className="icon-button"
                  onClick={
                    clearFile
                  }
                  disabled={
                    uploading
                    || processing
                  }
                >
                  <X size={19} />
                </button>
  
              </div>
            )}
  
  
            {uploading && (
              <div className="progress-section">
  
                <div className="progress-header">
                  <span>
                    Uploading...
                  </span>
  
                  <strong>
                    {uploadProgress}%
                  </strong>
                </div>
  
                <div className="progress-track">
                  <div
                    className="progress-value"
                    style={{
                      width:
                        `${uploadProgress}%`,
                    }}
                  />
                </div>
  
              </div>
            )}
  
  
            {error && (
              <div className="upload-error">
                <AlertCircle
                  size={18}
                />
  
                <span>
                  {error}
                </span>
              </div>
            )}
  
  
            <div className="upload-actions">
  
              <button
                className="secondary-button"
                onClick={
                  clearFile
                }
                disabled={
                  !selectedFile
                  || uploading
                  || processing
                }
              >
                Clear
              </button>
  
              {!uploadResult && (
                <button
                  className="primary-action-button"
                  onClick={
                    uploadInvoice
                  }
                  disabled={
                    !selectedFile
                    || uploading
                  }
                >
  
                  {uploading
                    ? (
                      <>
                        <Loader2
                          className="spin"
                          size={18}
                        />
                        Uploading
                      </>
                    )
                    : (
                      <>
                        <Upload
                          size={18}
                        />
                        Upload Invoice
                      </>
                    )}
  
                </button>
              )}
  
  
              {uploadResult
                && !uploadResult.is_duplicate
                && !processResult
                && (
                  <button
                    className="primary-action-button"
                    onClick={
                      processInvoice
                    }
                    disabled={
                      processing
                    }
                  >
  
                    {processing
                      ? (
                        <>
                          <Loader2
                            className="spin"
                            size={18}
                          />
                          Processing
                        </>
                      )
                      : (
                        <>
                          <CheckCircle2
                            size={18}
                          />
                          Process Invoice
                        </>
                      )}
  
                  </button>
                )}
  
            </div>
  
          </div>
  
  
          <div className="content-card">
  
            <div className="card-header">
              <div>
                <h2>
                  Processing Status
                </h2>
  
                <p>
                  Track each invoice
                  processing stage.
                </p>
              </div>
            </div>
  
  
            {steps.length === 0 ? (
              <div className="processing-empty">
  
                <FileText
                  size={34}
                />
  
                <p>
                  Upload an invoice to
                  begin processing.
                </p>
  
              </div>
            ) : (
  
              <div className="processing-steps">
  
                {steps.map(
                  (
                    step,
                    index
                  ) => (
  
                  <div
                    className="processing-step"
                    key={
                      `${step.name}-${index}`
                    }
                  >
  
                    <div
                      className={
                        `step-indicator ${step.status}`
                      }
                    >
  
                      {step.status
                        === "processing"
                        ? (
                          <Loader2
                            className="spin"
                            size={17}
                          />
                        )
                        : step.status
                          === "error"
                          ? (
                            <AlertCircle
                              size={17}
                            />
                          )
                          : (
                            <CheckCircle2
                              size={17}
                            />
                          )}
  
                    </div>
  
                    <div>
                      <strong>
                        {step.name}
                      </strong>
  
                      <span>
                        {step.message}
                      </span>
                    </div>
  
                  </div>
  
                ))}
  
              </div>
            )}
  
          </div>
  
        </div>
  
  
        {uploadResult && (
          <div className="content-card result-card">
  
            <div className="card-header">
              <div>
                <h2>
                  Upload Result
                </h2>
  
                <p>
                  Invoice #{uploadResult.id}
                </p>
              </div>
            </div>
  
  
            {uploadResult.is_duplicate ? (
  
              <div className="duplicate-alert">
  
                <AlertCircle
                  size={22}
                />
  
                <div>
                  <strong>
                    Exact duplicate detected
                  </strong>
  
                  <p>
                    {
                      uploadResult.message
                    }
                  </p>
                </div>
  
              </div>
  
            ) : (
  
              <div className="success-alert">
  
                <CheckCircle2
                  size={22}
                />
  
                <div>
                  <strong>
                    Upload successful
                  </strong>
  
                  <p>
                    {
                      uploadResult.file_name
                    }
                    {" "}
                    is ready for processing.
                  </p>
                </div>
  
              </div>
  
            )}
  
          </div>
        )}
  
  
        {processResult && (
          <div className="content-card result-card">
  
            <div className="card-header">
              <div>
                <h2>
                  Extraction Summary
                </h2>
  
                <p>
                  AI processing completed
                  for Invoice #{invoiceId}.
                </p>
              </div>
            </div>
  
  
            <div className="summary-grid">
  
              <div>
                <span>Vendor</span>
                <strong>
                  {
                    processResult
                      .fields
                      .vendor_name
                    || "-"
                  }
                </strong>
              </div>
  
              <div>
                <span>
                  Invoice Number
                </span>
  
                <strong>
                  {
                    processResult
                      .fields
                      .invoice_number
                    || "-"
                  }
                </strong>
              </div>
  
              <div>
                <span>
                  Grand Total
                </span>
  
                <strong>
                  {processResult
                    .fields
                    .grand_total
                    ? `₹${processResult.fields.grand_total}`
                    : "-"
                  }
                </strong>
              </div>
  
              <div>
                <span>
                  Confidence
                </span>
  
                <strong
                  className={
                    processResult
                      .confidence
                      .overall_confidence_percentage
                    >= 90
                      ? "confidence-text-high"
                      : processResult
                          .confidence
                          .overall_confidence_percentage
                        >= 70
                        ? "confidence-text-medium"
                        : "confidence-text-low"
                  }
                >
                  {
                    processResult
                      .confidence
                      .overall_confidence_percentage
                  }%
                </strong>
              </div>
  
              <div>
                <span>
                  Validation
                </span>
  
                <strong>
                  {
                    processResult
                      .validation
                      .overall_status
                  }
                </strong>
              </div>
  
              <div>
                <span>
                  Duplicate
                </span>
  
                <strong>
                  {
                    processResult
                      .duplicate
                      .is_duplicate
                    ? "Yes"
                    : "No"
                  }
                </strong>
              </div>
  
            </div>

            <div className="processing-complete-actions">

                <Link
                    to={`/review/${invoiceId}`}
                    className="primary-action-button"
                >
                    Review Invoice
                </Link>

                <Link
                    to="/invoices"
                    className="secondary-link-button"
                >
                    View Invoice History
                </Link>

            </div>
  
          </div>
        )}
  
      </div>
    );
  }
  
  export default UploadInvoice;