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

        print("Vendor:", invoice.vendor_name)
        print("GSTIN:", invoice.vendor_gstin)
        print(
            "Invoice Number:",
            invoice.invoice_number,
        )

        print(
            "Invoice Date:",
            invoice.invoice_date,
        )

        print(
            "Due Date:",
            invoice.due_date,
        )

        print(
            "Subtotal:",
            invoice.subtotal,
        )

        print(
            "Tax:",
            invoice.tax_amount,
        )

        print(
            "Grand Total:",
            invoice.grand_total,
        )

        print(
            "Currency:",
            invoice.currency,
        )

finally:

    db.close()