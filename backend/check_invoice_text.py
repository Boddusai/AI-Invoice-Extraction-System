from app.database.database import SessionLocal
from app.models.invoice import Invoice


db = SessionLocal()

try:
    invoices = (
        db.query(Invoice)
        .order_by(Invoice.id.desc())
        .all()
    )

    for invoice in invoices:
        print("=" * 60)

        print("Invoice ID:", invoice.id)
        print("File:", invoice.file_name)
        print("Status:", invoice.processing_status)

        print("\nExtracted text:")

        if invoice.raw_ocr_text:
            print(invoice.raw_ocr_text[:1500])
        else:
            print("No text extracted.")

        print()

finally:
    db.close()