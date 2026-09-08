import hashlib
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.invoice import (
    FieldConfidence,
    Invoice,
    InvoiceItem,
    ValidationResult,
)
from app.schemas.invoice import (
    FieldConfidenceResponse,
    InvoiceConfidenceResponse,
    InvoiceFieldExtractionResponse,
    InvoiceOCRResponse,
    InvoiceTextExtractionResponse,
    InvoiceUploadResponse,
    LineItemExtractionResponse,
    InvoiceValidationResponse,
    ValidationResultResponse,
    DuplicateDetectionResponse,
    DuplicateInvoiceMatchResponse,
    InvoiceLineItemUpdate,
    InvoiceReviewResponse,
    InvoiceReviewUpdate,
    InvoiceListItemResponse,
)
from app.services.pdf_extractor import extract_text_from_pdf
from app.services.ocr_service import extract_text_with_ocr
from app.services.invoice_extractor import extract_invoice_fields
from app.services.line_item_extractor import (
    extract_line_items,
)
from app.services.confidence_service import (
    calculate_field_confidences,
)
from app.services.validation_service import (
    validate_invoice,
)
from app.services.duplicate_service import (
    find_duplicate_invoice,
)
from fastapi.responses import Response

from app.services.export_service import (
    build_invoice_data,
    create_csv_export,
    create_excel_export,
    create_json_export,
)

router = APIRouter(
    prefix="/api/invoices",
    tags=["Invoices"],
)


# Backend root folder
BACKEND_DIR = Path(__file__).resolve().parents[2]

# Upload folder
UPLOAD_DIR = BACKEND_DIR / "uploads"

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
}

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def generate_file_hash(file_content: bytes) -> str:
    """
    Generate SHA-256 hash for duplicate detection.
    """

    return hashlib.sha256(file_content).hexdigest()


@router.post(
    "/upload",
    response_model=InvoiceUploadResponse,
)
async def upload_invoice(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):

    # ----------------------------
    # 1. Validate filename
    # ----------------------------

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="File name is missing.",
        )

    original_filename = Path(file.filename).name

    extension = Path(
        original_filename
    ).suffix.lower()

    # ----------------------------
    # 2. Validate file type
    # ----------------------------

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file format. "
                "Only PDF, JPG, JPEG and PNG are allowed."
            ),
        )
    
    if (
        file.content_type
        and file.content_type
        not in ALLOWED_CONTENT_TYPES
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid file content type. "
                "Only PDF, JPG, JPEG and PNG "
                "invoices are supported."
            ),
        )

    # ----------------------------
    # 3. Read file
    # ----------------------------

    file_content = await file.read()

    if not file_content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    # ----------------------------
    # 4. Validate file size
    # ----------------------------

    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds 10 MB limit.",
        )

    # ----------------------------
    # 5. Generate SHA-256 hash
    # ----------------------------

    file_hash = generate_file_hash(
        file_content
    )

    # ----------------------------
    # 6. Duplicate detection
    # ----------------------------

    existing_invoice = (
        db.query(Invoice)
        .filter(
            Invoice.file_hash == file_hash
        )
        .first()
    )

    if existing_invoice:

        return InvoiceUploadResponse(
            id=existing_invoice.id,
            file_name=existing_invoice.file_name,
            processing_status=existing_invoice.processing_status,
            is_duplicate=True,
            message=(
                "Duplicate invoice detected. "
                "This file was already uploaded."
            ),
            created_at=existing_invoice.created_at,
        )

    # ----------------------------
    # 7. Generate safe filename
    # ----------------------------

    unique_filename = (
        f"{uuid.uuid4().hex}_{original_filename}"
    )

    file_path = (
        UPLOAD_DIR / unique_filename
    )

    # ----------------------------
    # 8. Save invoice file
    # ----------------------------

    try:

        with open(
            file_path,
            "wb",
        ) as saved_file:

            saved_file.write(
                file_content
            )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Unable to save file: {error}",
        )

    # ----------------------------
    # 9. Create database record
    # ----------------------------

    invoice = Invoice(
        file_name=original_filename,
        file_path=str(file_path),
        file_hash=file_hash,
        processing_status="uploaded",
        is_duplicate=False,
    )

    try:

        db.add(invoice)

        db.commit()

        db.refresh(invoice)

    except Exception:

        db.rollback()

        # Remove file if DB save failed
        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail="Unable to save invoice information.",
        )

    # ----------------------------
    # 10. Return response
    # ----------------------------

    return InvoiceUploadResponse(
        id=invoice.id,
        file_name=invoice.file_name,
        processing_status=invoice.processing_status,
        is_duplicate=False,
        message="Invoice uploaded successfully.",
        created_at=invoice.created_at,
    )

@router.post(
    "/{invoice_id}/extract-text",
    response_model=InvoiceTextExtractionResponse,
)
def extract_invoice_text(
    invoice_id: int,
    db: Session = Depends(get_db),
):

    # --------------------------------
    # 1. Find invoice
    # --------------------------------

    invoice = db.get(
        Invoice,
        invoice_id,
    )

    if invoice is None:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found.",
        )

    # --------------------------------
    # 2. Check file type
    # --------------------------------

    extension = Path(
        invoice.file_name
    ).suffix.lower()

    if extension != ".pdf":
        raise HTTPException(
            status_code=400,
            detail=(
                "Direct text extraction currently supports "
                "PDF files only. Image OCR will be added next."
            ),
        )

    # --------------------------------
    # 3. Extract PDF text
    # --------------------------------

    try:

        result = extract_text_from_pdf(
            invoice.file_path
        )

    except FileNotFoundError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    except Exception as error:

        invoice.processing_status = "extraction_failed"

        db.commit()

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )

    extracted_text = result["text"]

    # --------------------------------
    # 4. Determine extraction status
    # --------------------------------

    if extracted_text.strip():

        invoice.processing_status = (
            "text_extracted"
        )

        message = (
            "PDF text extracted successfully."
        )

    else:

        invoice.processing_status = (
            "ocr_required"
        )

        message = (
            "No embedded text was found. "
            "This PDF may be scanned and requires OCR."
        )

    # --------------------------------
    # 5. Save raw text
    # --------------------------------

    invoice.raw_ocr_text = extracted_text

    db.commit()

    db.refresh(invoice)

    # --------------------------------
    # 6. Response
    # --------------------------------

    return InvoiceTextExtractionResponse(
        invoice_id=invoice.id,
        file_name=invoice.file_name,
        processing_status=invoice.processing_status,
        page_count=result["page_count"],
        characters_extracted=result[
            "characters_extracted"
        ],
        extracted_text=extracted_text,
        message=message,
    )

@router.post(
    "/{invoice_id}/ocr",
    response_model=InvoiceOCRResponse,
)
def perform_invoice_ocr(
    invoice_id: int,
    db: Session = Depends(get_db),
):

    # -------------------------
    # 1. Find invoice
    # -------------------------

    invoice = db.get(
        Invoice,
        invoice_id
    )

    if invoice is None:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found."
        )

    # -------------------------
    # 2. Mark OCR as running
    # -------------------------

    invoice.processing_status = (
        "ocr_processing"
    )

    db.commit()

    # -------------------------
    # 3. Perform OCR
    # -------------------------

    try:

        result = extract_text_with_ocr(
            invoice.file_path
        )

    except FileNotFoundError as error:

        invoice.processing_status = (
            "ocr_failed"
        )

        db.commit()

        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except Exception as error:

        invoice.processing_status = (
            "ocr_failed"
        )

        db.commit()

        raise HTTPException(
            status_code=500,
            detail=f"OCR failed: {error}"
        )

    extracted_text = result["text"]

    # -------------------------
    # 4. Check OCR result
    # -------------------------

    if extracted_text.strip():

        invoice.processing_status = (
            "ocr_completed"
        )

        message = (
            "Invoice OCR completed successfully."
        )

    else:

        invoice.processing_status = (
            "ocr_no_text"
        )

        message = (
            "OCR completed but no readable text "
            "was detected."
        )

    # -------------------------
    # 5. Save extracted text
    # -------------------------

    invoice.raw_ocr_text = (
        extracted_text
    )

    db.commit()

    db.refresh(invoice)

    # -------------------------
    # 6. Return result
    # -------------------------

    return InvoiceOCRResponse(
        invoice_id=invoice.id,
        file_name=invoice.file_name,
        processing_status=(
            invoice.processing_status
        ),
        page_count=result[
            "page_count"
        ],
        characters_extracted=result[
            "characters_extracted"
        ],
        extracted_text=extracted_text,
        message=message,
    )

@router.post(
    "/{invoice_id}/extract-fields",
    response_model=InvoiceFieldExtractionResponse,
)
def extract_fields(
    invoice_id: int,
    db: Session = Depends(get_db),
):

    # Find invoice
    invoice = db.get(
        Invoice,
        invoice_id,
    )

    if invoice is None:

        raise HTTPException(
            status_code=404,
            detail="Invoice not found.",
        )

    # Text must exist before field extraction
    if not invoice.raw_ocr_text:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invoice has no extracted text. "
                "Run PDF extraction or OCR first."
            ),
        )

    try:

        fields = extract_invoice_fields(
            invoice.raw_ocr_text
        )

        # Save fields
        invoice.vendor_name = fields[
            "vendor_name"
        ]

        invoice.vendor_gstin = fields[
            "vendor_gstin"
        ]

        invoice.invoice_number = fields[
            "invoice_number"
        ]

        invoice.invoice_date = fields[
            "invoice_date"
        ]

        invoice.due_date = fields[
            "due_date"
        ]

        invoice.subtotal = fields[
            "subtotal"
        ]

        invoice.tax_amount = fields[
            "tax_amount"
        ]

        invoice.grand_total = fields[
            "grand_total"
        ]

        invoice.currency = fields[
            "currency"
        ]

        invoice.processing_status = (
            "fields_extracted"
        )

        db.commit()

        db.refresh(invoice)

    except Exception as error:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Field extraction failed: {error}"
            ),
        )

    return InvoiceFieldExtractionResponse(
        invoice_id=invoice.id,
        vendor_name=invoice.vendor_name,
        vendor_gstin=invoice.vendor_gstin,
        invoice_number=invoice.invoice_number,
        invoice_date=invoice.invoice_date,
        due_date=invoice.due_date,
        subtotal=invoice.subtotal,
        tax_amount=invoice.tax_amount,
        grand_total=invoice.grand_total,
        currency=invoice.currency,
        processing_status=(
            invoice.processing_status
        ),
        message=(
            "Invoice fields extracted successfully."
        ),
    )

@router.post(
    "/{invoice_id}/extract-line-items",
    response_model=LineItemExtractionResponse,
)
def extract_invoice_line_items(
    invoice_id: int,
    db: Session = Depends(get_db),
):

    # -------------------------------
    # Find invoice
    # -------------------------------

    invoice = db.get(
        Invoice,
        invoice_id,
    )

    if invoice is None:

        raise HTTPException(
            status_code=404,
            detail="Invoice not found.",
        )

    if not invoice.raw_ocr_text:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invoice has no extracted text. "
                "Run PDF extraction or OCR first."
            ),
        )

    # -------------------------------
    # Extract items
    # -------------------------------

    try:

        extracted_items = (
            extract_line_items(
                invoice.raw_ocr_text
            )
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Line item extraction failed: "
                f"{error}"
            ),
        )

    if not extracted_items:

        raise HTTPException(
            status_code=422,
            detail=(
                "No line items could be detected "
                "from this invoice."
            ),
        )

    # -------------------------------
    # Remove previous extracted items
    #
    # This prevents duplicates if the
    # endpoint is executed twice.
    # -------------------------------

    db.query(
        InvoiceItem
    ).filter(
        InvoiceItem.invoice_id
        == invoice.id
    ).delete(
        synchronize_session=False
    )

    # -------------------------------
    # Save new line items
    # -------------------------------

    try:

        for item_data in extracted_items:

            item = InvoiceItem(
                invoice_id=invoice.id,

                description=item_data.get(
                    "description"
                ),

                quantity=item_data.get(
                    "quantity"
                ),

                unit_price=item_data.get(
                    "unit_price"
                ),

                tax_rate=item_data.get(
                    "tax_rate"
                ),

                tax_amount=item_data.get(
                    "tax_amount"
                ),

                line_total=item_data.get(
                    "line_total"
                ),

                confidence=item_data.get(
                    "confidence"
                ),
            )

            db.add(item)

        invoice.processing_status = (
            "line_items_extracted"
        )

        db.commit()

        db.refresh(invoice)

    except Exception as error:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Unable to save line items: "
                f"{error}"
            ),
        )

    saved_items = (
        db.query(InvoiceItem)
        .filter(
            InvoiceItem.invoice_id
            == invoice.id
        )
        .order_by(
            InvoiceItem.id
        )
        .all()
    )

    return LineItemExtractionResponse(
        invoice_id=invoice.id,
        item_count=len(saved_items),
        items=saved_items,
        processing_status=(
            invoice.processing_status
        ),
        message=(
            "Invoice line items extracted successfully."
        ),
    )

@router.post(
    "/{invoice_id}/confidence-scores",
    response_model=InvoiceConfidenceResponse,
)
def calculate_invoice_confidence(
    invoice_id: int,
    db: Session = Depends(get_db),
):

    # -------------------------------
    # Find invoice
    # -------------------------------

    invoice = db.get(
        Invoice,
        invoice_id,
    )

    if invoice is None:

        raise HTTPException(
            status_code=404,
            detail="Invoice not found.",
        )

    if not invoice.raw_ocr_text:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invoice text has not been extracted. "
                "Run PDF extraction or OCR first."
            ),
        )

    # Make sure structured extraction
    # has already been performed.
    if (
        invoice.vendor_name is None
        and invoice.invoice_number is None
        and invoice.grand_total is None
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Invoice fields have not been extracted. "
                "Run /extract-fields first."
            ),
        )

    # -------------------------------
    # Calculate scores
    # -------------------------------

    confidence_data = (
        calculate_field_confidences(
            invoice
        )
    )

    # -------------------------------
    # Delete old confidence data
    # -------------------------------

    db.query(
        FieldConfidence
    ).filter(
        FieldConfidence.invoice_id
        == invoice.id
    ).delete(
        synchronize_session=False
    )

    try:

        # ---------------------------
        # Save scores
        # ---------------------------

        for field in confidence_data:

            confidence_record = (
                FieldConfidence(
                    invoice_id=invoice.id,
                    field_name=field[
                        "field_name"
                    ],
                    field_value=field[
                        "field_value"
                    ],
                    confidence=field[
                        "confidence"
                    ],
                    source_text=field[
                        "source_text"
                    ],
                )
            )

            db.add(
                confidence_record
            )

        invoice.processing_status = (
            "confidence_scored"
        )

        db.commit()

        db.refresh(invoice)

    except Exception as error:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to save confidence "
                f"scores: {error}"
            ),
        )

    # -------------------------------
    # Read saved scores
    # -------------------------------

    saved_scores = (
        db.query(FieldConfidence)
        .filter(
            FieldConfidence.invoice_id
            == invoice.id
        )
        .order_by(
            FieldConfidence.id
        )
        .all()
    )

    # --------------------------------
    # Overall confidence
    #
    # Due date is optional, so if it is
    # missing we don't reduce the overall
    # invoice score because of it.
    # --------------------------------

    score_values = []

    for score in saved_scores:

        if (
            score.field_name == "due_date"
            and score.field_value is None
        ):
            continue

        score_values.append(
            score.confidence
        )

    if score_values:

        overall_confidence = (
            sum(score_values)
            / len(score_values)
        )

    else:

        overall_confidence = 0.0

    overall_confidence = round(
        overall_confidence,
        4,
    )

    return InvoiceConfidenceResponse(
        invoice_id=invoice.id,

        overall_confidence=(
            overall_confidence
        ),

        overall_confidence_percentage=round(
            overall_confidence * 100,
            2,
        ),

        fields=saved_scores,

        processing_status=(
            invoice.processing_status
        ),

        message=(
            "Confidence scores calculated "
            "successfully."
        ),
    )

@router.post(
    "/{invoice_id}/validate",
    response_model=InvoiceValidationResponse,
)
def validate_invoice_endpoint(
    invoice_id: int,
    db: Session = Depends(get_db),
):

    # ---------------------------------
    # Find invoice
    # ---------------------------------

    invoice = db.get(
        Invoice,
        invoice_id,
    )

    if invoice is None:

        raise HTTPException(
            status_code=404,
            detail="Invoice not found.",
        )

    if not invoice.raw_ocr_text:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invoice text has not been "
                "extracted yet."
            ),
        )

    # ---------------------------------
    # Load line items
    # ---------------------------------

    items = (
        db.query(InvoiceItem)
        .filter(
            InvoiceItem.invoice_id
            == invoice.id
        )
        .order_by(
            InvoiceItem.id
        )
        .all()
    )

    # ---------------------------------
    # Run validation
    # ---------------------------------

    validation_data = (
        validate_invoice(
            invoice,
            items,
        )
    )

    # ---------------------------------
    # Remove previous validation data
    # ---------------------------------

    db.query(
        ValidationResult
    ).filter(
        ValidationResult.invoice_id
        == invoice.id
    ).delete(
        synchronize_session=False
    )

    try:

        for result in validation_data[
            "results"
        ]:

            validation_record = (
                ValidationResult(
                    invoice_id=invoice.id,
                    rule_name=result[
                        "rule_name"
                    ],
                    status=result[
                        "status"
                    ],
                    message=result[
                        "message"
                    ],
                )
            )

            db.add(
                validation_record
            )

        invoice.processing_status = (
            "validated"
        )

        db.commit()

        db.refresh(invoice)

    except Exception as error:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to save validation "
                f"results: {error}"
            ),
        )

    saved_results = (
        db.query(ValidationResult)
        .filter(
            ValidationResult.invoice_id
            == invoice.id
        )
        .order_by(
            ValidationResult.id
        )
        .all()
    )

    return InvoiceValidationResponse(
        invoice_id=invoice.id,

        overall_status=validation_data[
            "overall_status"
        ],

        passed_count=validation_data[
            "passed_count"
        ],

        warning_count=validation_data[
            "warning_count"
        ],

        failed_count=validation_data[
            "failed_count"
        ],

        validations=saved_results,

        processing_status=(
            invoice.processing_status
        ),

        message=(
            "Invoice validation completed."
        ),
    )

@router.post(
    "/{invoice_id}/check-duplicate",
    response_model=DuplicateDetectionResponse,
)
def check_invoice_duplicate(
    invoice_id: int,
    db: Session = Depends(get_db),
):

    # --------------------------------
    # Find current invoice
    # --------------------------------

    invoice = db.get(
        Invoice,
        invoice_id,
    )

    if invoice is None:

        raise HTTPException(
            status_code=404,
            detail="Invoice not found.",
        )

    # --------------------------------
    # Structured fields must exist
    # --------------------------------

    if (
        invoice.invoice_number is None
        and invoice.vendor_gstin is None
        and invoice.grand_total is None
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Invoice fields have not been "
                "extracted. Run /extract-fields "
                "before duplicate detection."
            ),
        )

    # --------------------------------
    # Find other invoices
    # --------------------------------

    candidates = (
        db.query(Invoice)
        .filter(
            Invoice.id != invoice.id
        )
        .all()
    )

    duplicate_result = (
        find_duplicate_invoice(
            invoice,
            candidates,
        )
    )

    # --------------------------------
    # Duplicate found
    # --------------------------------

    if duplicate_result[
        "is_duplicate"
    ]:

        matched_invoice = (
            duplicate_result[
                "duplicate_invoice"
            ]
        )

        invoice.is_duplicate = True

        invoice.duplicate_of = (
            matched_invoice.id
        )

        invoice.processing_status = (
            "duplicate_detected"
        )

        message = (
            "Possible duplicate invoice "
            "detected."
        )

    else:

        matched_invoice = None

        invoice.is_duplicate = False

        invoice.duplicate_of = None

        invoice.processing_status = (
            "duplicate_checked"
        )

        message = (
            "No duplicate invoice detected."
        )

    try:

        db.commit()

        db.refresh(invoice)

    except Exception as error:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to save duplicate "
                f"check result: {error}"
            ),
        )

    # --------------------------------
    # Create matched invoice response
    # --------------------------------

    matched_response = None

    if matched_invoice:

        matched_response = (
            DuplicateInvoiceMatchResponse(
                invoice_id=matched_invoice.id,
                file_name=(
                    matched_invoice.file_name
                ),
                invoice_number=(
                    matched_invoice.invoice_number
                ),
                vendor_name=(
                    matched_invoice.vendor_name
                ),
                vendor_gstin=(
                    matched_invoice.vendor_gstin
                ),
                grand_total=(
                    matched_invoice.grand_total
                ),
            )
        )

    return DuplicateDetectionResponse(
        invoice_id=invoice.id,

        is_duplicate=(
            invoice.is_duplicate
        ),

        duplicate_of=(
            invoice.duplicate_of
        ),

        duplicate_score=(
            duplicate_result["score"]
        ),

        matched_fields=(
            duplicate_result[
                "matched_fields"
            ]
        ),

        matched_invoice=(
            matched_response
        ),

        processing_status=(
            invoice.processing_status
        ),

        message=message,
    )

@router.get(
    "/{invoice_id}/review",
    response_model=InvoiceReviewResponse,
)
def get_invoice_for_review(
    invoice_id: int,
    db: Session = Depends(get_db),
):

    invoice = db.get(
        Invoice,
        invoice_id,
    )

    if invoice is None:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found.",
        )

    items = (
        db.query(InvoiceItem)
        .filter(
            InvoiceItem.invoice_id
            == invoice.id
        )
        .order_by(
            InvoiceItem.id
        )
        .all()
    )

    return InvoiceReviewResponse(
        invoice_id=invoice.id,
        file_name=invoice.file_name,

        vendor_name=invoice.vendor_name,
        vendor_gstin=invoice.vendor_gstin,

        invoice_number=invoice.invoice_number,

        invoice_date=invoice.invoice_date,
        due_date=invoice.due_date,

        subtotal=invoice.subtotal,
        tax_amount=invoice.tax_amount,
        grand_total=invoice.grand_total,

        currency=invoice.currency,

        is_duplicate=invoice.is_duplicate,
        duplicate_of=invoice.duplicate_of,

        processing_status=(
            invoice.processing_status
        ),

        items=items,
    )

@router.patch(
    "/{invoice_id}/review",
    response_model=InvoiceReviewResponse,
)
def update_invoice_review(
    invoice_id: int,
    data: InvoiceReviewUpdate,
    db: Session = Depends(get_db),
):

    invoice = db.get(
        Invoice,
        invoice_id,
    )

    if invoice is None:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found.",
        )

    updates = data.model_dump(
        exclude_unset=True
    )

    # Only allow these fields to change
    allowed_fields = {
        "vendor_name",
        "vendor_gstin",
        "invoice_number",
        "invoice_date",
        "due_date",
        "subtotal",
        "tax_amount",
        "grand_total",
        "currency",
    }

    for field_name, value in updates.items():

        if field_name in allowed_fields:

            setattr(
                invoice,
                field_name,
                value,
            )

    # --------------------------------
    # Existing confidence/validation
    # may no longer be accurate after
    # a manual correction.
    # --------------------------------

    db.query(
        FieldConfidence
    ).filter(
        FieldConfidence.invoice_id
        == invoice.id
    ).delete(
        synchronize_session=False
    )

    db.query(
        ValidationResult
    ).filter(
        ValidationResult.invoice_id
        == invoice.id
    ).delete(
        synchronize_session=False
    )

    # Duplicate status must also
    # be recalculated after editing.
    invoice.is_duplicate = False
    invoice.duplicate_of = None

    invoice.processing_status = (
        "reviewed"
    )

    try:

        db.commit()
        db.refresh(invoice)

    except Exception as error:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Unable to update invoice: "
                f"{error}"
            ),
        )

    items = (
        db.query(InvoiceItem)
        .filter(
            InvoiceItem.invoice_id
            == invoice.id
        )
        .order_by(
            InvoiceItem.id
        )
        .all()
    )

    return InvoiceReviewResponse(
        invoice_id=invoice.id,
        file_name=invoice.file_name,

        vendor_name=invoice.vendor_name,
        vendor_gstin=invoice.vendor_gstin,

        invoice_number=invoice.invoice_number,

        invoice_date=invoice.invoice_date,
        due_date=invoice.due_date,

        subtotal=invoice.subtotal,
        tax_amount=invoice.tax_amount,
        grand_total=invoice.grand_total,

        currency=invoice.currency,

        is_duplicate=invoice.is_duplicate,
        duplicate_of=invoice.duplicate_of,

        processing_status=(
            invoice.processing_status
        ),

        items=items,
    )

@router.patch(
    "/{invoice_id}/review",
    response_model=InvoiceReviewResponse,
)
def update_invoice_review(
    invoice_id: int,
    data: InvoiceReviewUpdate,
    db: Session = Depends(get_db),
):

    invoice = db.get(
        Invoice,
        invoice_id,
    )

    if invoice is None:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found.",
        )

    updates = data.model_dump(
        exclude_unset=True
    )

    # Only allow these fields to change
    allowed_fields = {
        "vendor_name",
        "vendor_gstin",
        "invoice_number",
        "invoice_date",
        "due_date",
        "subtotal",
        "tax_amount",
        "grand_total",
        "currency",
    }

    for field_name, value in updates.items():

        if field_name in allowed_fields:

            setattr(
                invoice,
                field_name,
                value,
            )

    # --------------------------------
    # Existing confidence/validation
    # may no longer be accurate after
    # a manual correction.
    # --------------------------------

    db.query(
        FieldConfidence
    ).filter(
        FieldConfidence.invoice_id
        == invoice.id
    ).delete(
        synchronize_session=False
    )

    db.query(
        ValidationResult
    ).filter(
        ValidationResult.invoice_id
        == invoice.id
    ).delete(
        synchronize_session=False
    )

    # Duplicate status must also
    # be recalculated after editing.
    invoice.is_duplicate = False
    invoice.duplicate_of = None

    invoice.processing_status = (
        "reviewed"
    )

    try:

        db.commit()
        db.refresh(invoice)

    except Exception as error:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Unable to update invoice: "
                f"{error}"
            ),
        )

    items = (
        db.query(InvoiceItem)
        .filter(
            InvoiceItem.invoice_id
            == invoice.id
        )
        .order_by(
            InvoiceItem.id
        )
        .all()
    )

    return InvoiceReviewResponse(
        invoice_id=invoice.id,
        file_name=invoice.file_name,

        vendor_name=invoice.vendor_name,
        vendor_gstin=invoice.vendor_gstin,

        invoice_number=invoice.invoice_number,

        invoice_date=invoice.invoice_date,
        due_date=invoice.due_date,

        subtotal=invoice.subtotal,
        tax_amount=invoice.tax_amount,
        grand_total=invoice.grand_total,

        currency=invoice.currency,

        is_duplicate=invoice.is_duplicate,
        duplicate_of=invoice.duplicate_of,

        processing_status=(
            invoice.processing_status
        ),

        items=items,
    )

@router.get(
    "/{invoice_id}/export/{export_format}",
)
def export_invoice(
    invoice_id: int,
    export_format: str,
    db: Session = Depends(get_db),
):

    invoice = db.get(
        Invoice,
        invoice_id,
    )

    if invoice is None:

        raise HTTPException(
            status_code=404,
            detail="Invoice not found.",
        )

    export_format = (
        export_format
        .strip()
        .lower()
    )

    allowed_formats = {
        "json",
        "csv",
        "xlsx",
    }

    if export_format not in allowed_formats:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported export format. "
                "Use json, csv or xlsx."
            ),
        )

    # -------------------------------
    # Load related data
    # -------------------------------

    items = (
        db.query(InvoiceItem)
        .filter(
            InvoiceItem.invoice_id
            == invoice.id
        )
        .order_by(
            InvoiceItem.id
        )
        .all()
    )

    confidences = (
        db.query(FieldConfidence)
        .filter(
            FieldConfidence.invoice_id
            == invoice.id
        )
        .order_by(
            FieldConfidence.id
        )
        .all()
    )

    validations = (
        db.query(ValidationResult)
        .filter(
            ValidationResult.invoice_id
            == invoice.id
        )
        .order_by(
            ValidationResult.id
        )
        .all()
    )

    data = build_invoice_data(
        invoice,
        items,
        confidences,
        validations,
    )

    safe_invoice_number = (
        invoice.invoice_number
        or str(invoice.id)
    )

    safe_invoice_number = "".join(
        character
        if character.isalnum()
        or character in {"-", "_"}
        else "_"
        for character
        in safe_invoice_number
    )

    # ===============================
    # JSON
    # ===============================

    if export_format == "json":

        content = create_json_export(
            data
        )

        filename = (
            f"invoice_"
            f"{safe_invoice_number}.json"
        )

        return Response(
            content=content,
            media_type="application/json",
            headers={
                "Content-Disposition":
                    f'attachment; filename="{filename}"'
            },
        )

    # ===============================
    # CSV
    # ===============================

    if export_format == "csv":

        content = create_csv_export(
            data
        )

        filename = (
            f"invoice_"
            f"{safe_invoice_number}.csv"
        )

        return Response(
            content=content,
            media_type=(
                "text/csv; charset=utf-8"
            ),
            headers={
                "Content-Disposition":
                    f'attachment; filename="{filename}"'
            },
        )

    # ===============================
    # Excel
    # ===============================

    content = create_excel_export(
        data
    )

    filename = (
        f"invoice_"
        f"{safe_invoice_number}.xlsx"
    )

    return Response(
        content=content,
        media_type=(
            "application/"
            "vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition":
                f'attachment; filename="{filename}"'
        },
    )

@router.get(
    "",
    response_model=list[InvoiceListItemResponse],
)
def get_all_invoices(
    db: Session = Depends(get_db),
):

    invoices = (
        db.query(Invoice)
        .order_by(
            Invoice.created_at.desc()
        )
        .all()
    )

    return invoices

@router.get(
    "/{invoice_id}",
)
def get_invoice_details(
    invoice_id: int,
    db: Session = Depends(get_db),
):

    invoice = db.get(
        Invoice,
        invoice_id,
    )

    if invoice is None:

        raise HTTPException(
            status_code=404,
            detail="Invoice not found.",
        )

    items = (
        db.query(InvoiceItem)
        .filter(
            InvoiceItem.invoice_id
            == invoice.id
        )
        .order_by(
            InvoiceItem.id
        )
        .all()
    )

    confidences = (
        db.query(FieldConfidence)
        .filter(
            FieldConfidence.invoice_id
            == invoice.id
        )
        .order_by(
            FieldConfidence.id
        )
        .all()
    )

    validations = (
        db.query(ValidationResult)
        .filter(
            ValidationResult.invoice_id
            == invoice.id
        )
        .order_by(
            ValidationResult.id
        )
        .all()
    )

    return {
        "invoice": {
            "id": invoice.id,
            "file_name": invoice.file_name,

            "vendor_name":
                invoice.vendor_name,

            "vendor_gstin":
                invoice.vendor_gstin,

            "invoice_number":
                invoice.invoice_number,

            "invoice_date":
                invoice.invoice_date,

            "due_date":
                invoice.due_date,

            "subtotal":
                invoice.subtotal,

            "tax_amount":
                invoice.tax_amount,

            "grand_total":
                invoice.grand_total,

            "currency":
                invoice.currency,

            "processing_status":
                invoice.processing_status,

            "is_duplicate":
                invoice.is_duplicate,

            "duplicate_of":
                invoice.duplicate_of,
        },

        "items": items,

        "confidence_scores":
            confidences,

        "validations":
            validations,
    }