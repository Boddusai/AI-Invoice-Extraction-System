from app.database.database import Base, engine

# Important:
# Import models before create_all
from app.models.invoice import (
    Invoice,
    InvoiceItem,
    FieldConfidence,
    ValidationResult,
)


def create_tables():
    print("Creating database tables...")

    Base.metadata.create_all(bind=engine)

    print("Database tables created successfully!")


if __name__ == "__main__":
    create_tables()