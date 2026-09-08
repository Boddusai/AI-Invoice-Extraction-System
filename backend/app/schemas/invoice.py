from datetime import date,datetime

from pydantic import BaseModel, ConfigDict


class InvoiceUploadResponse(BaseModel):
    id: int
    file_name: str
    processing_status: str
    is_duplicate: bool
    message: str
    created_at: datetime

class InvoiceTextExtractionResponse(BaseModel):
    invoice_id: int
    file_name: str
    processing_status: str
    page_count: int
    characters_extracted: int
    extracted_text: str
    message: str

class InvoiceOCRResponse(BaseModel):
    invoice_id: int
    file_name: str
    processing_status: str
    page_count: int
    characters_extracted: int
    extracted_text: str
    message: str

class InvoiceFieldExtractionResponse(BaseModel):
    invoice_id: int

    vendor_name: str | None = None
    vendor_gstin: str | None = None
    invoice_number: str | None = None

    invoice_date: date | None = None
    due_date: date | None = None

    subtotal: float | None = None
    tax_amount: float | None = None
    grand_total: float | None = None

    currency: str

    processing_status: str
    message: str

class InvoiceItemResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    description: str | None = None

    quantity: float | None = None
    unit_price: float | None = None

    tax_rate: float | None = None
    tax_amount: float | None = None

    line_total: float | None = None

    confidence: float | None = None


class LineItemExtractionResponse(BaseModel):
    invoice_id: int

    item_count: int

    items: list[InvoiceItemResponse]

    processing_status: str

    message: str

class FieldConfidenceResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    field_name: str
    field_value: str | None = None
    confidence: float
    source_text: str | None = None


class InvoiceConfidenceResponse(BaseModel):
    invoice_id: int

    overall_confidence: float

    overall_confidence_percentage: float

    fields: list[
        FieldConfidenceResponse
    ]

    processing_status: str

    message: str

class ValidationResultResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    rule_name: str
    status: str
    message: str | None = None


class InvoiceValidationResponse(BaseModel):
    invoice_id: int

    overall_status: str

    passed_count: int
    warning_count: int
    failed_count: int

    validations: list[
        ValidationResultResponse
    ]

    processing_status: str

    message: str

class DuplicateInvoiceMatchResponse(BaseModel):

    invoice_id: int
    file_name: str

    invoice_number: str | None = None

    vendor_name: str | None = None

    vendor_gstin: str | None = None

    grand_total: float | None = None


class DuplicateDetectionResponse(BaseModel):

    invoice_id: int

    is_duplicate: bool

    duplicate_of: int | None = None

    duplicate_score: int

    matched_fields: list[str]

    matched_invoice: (
        DuplicateInvoiceMatchResponse
        | None
    ) = None

    processing_status: str

    message: str

class InvoiceReviewUpdate(BaseModel):
    vendor_name: str | None = None
    vendor_gstin: str | None = None

    invoice_number: str | None = None

    invoice_date: date | None = None
    due_date: date | None = None

    subtotal: float | None = None
    tax_amount: float | None = None
    grand_total: float | None = None

    currency: str | None = None


class InvoiceLineItemUpdate(BaseModel):
    description: str | None = None

    quantity: float | None = None
    unit_price: float | None = None

    tax_rate: float | None = None
    tax_amount: float | None = None

    line_total: float | None = None


class InvoiceReviewItemResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    description: str | None = None

    quantity: float | None = None
    unit_price: float | None = None

    tax_rate: float | None = None
    tax_amount: float | None = None

    line_total: float | None = None

    confidence: float | None = None


class InvoiceReviewResponse(BaseModel):
    invoice_id: int
    file_name: str

    vendor_name: str | None = None
    vendor_gstin: str | None = None

    invoice_number: str | None = None

    invoice_date: date | None = None
    due_date: date | None = None

    subtotal: float | None = None
    tax_amount: float | None = None
    grand_total: float | None = None

    currency: str

    is_duplicate: bool
    duplicate_of: int | None = None

    processing_status: str

    items: list[InvoiceReviewItemResponse]

class InvoiceListItemResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    file_name: str

    vendor_name: str | None = None
    invoice_number: str | None = None

    invoice_date: date | None = None

    grand_total: float | None = None

    currency: str

    processing_status: str

    is_duplicate: bool

    created_at: datetime