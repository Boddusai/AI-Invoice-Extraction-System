from app.database.database import (
    SessionLocal,
)
from app.models.invoice import (
    FieldConfidence,
)


db = SessionLocal()

try:

    invoice_id = 3

    scores = (
        db.query(FieldConfidence)
        .filter(
            FieldConfidence.invoice_id
            == invoice_id
        )
        .order_by(
            FieldConfidence.id
        )
        .all()
    )

    print(
        f"\nConfidence scores for "
        f"Invoice {invoice_id}"
    )

    print("=" * 60)

    for score in scores:

        print(
            f"{score.field_name:20}"
            f"{score.confidence * 100:.2f}%"
            f"   Value: "
            f"{score.field_value}"
        )

finally:

    db.close()