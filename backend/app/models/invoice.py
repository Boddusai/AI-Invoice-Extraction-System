from datetime import datetime, date

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    file_hash: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        unique=True,
        index=True,
    )

    vendor_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    vendor_gstin: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    invoice_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    invoice_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    subtotal: Mapped[float | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    tax_amount: Mapped[float | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    grand_total: Mapped[float | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        default="INR",
    )

    raw_ocr_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    processing_status: Mapped[str] = mapped_column(
        String(50),
        default="uploaded",
    )

    is_duplicate: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    duplicate_of: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("invoices.id"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    items: Mapped[list["InvoiceItem"]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
    )

    confidences: Mapped[list["FieldConfidence"]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
    )

    validations: Mapped[list["ValidationResult"]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
    )

class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    invoice_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "invoices.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    quantity: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    unit_price: Mapped[float | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    tax_rate: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    tax_amount: Mapped[float | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    line_total: Mapped[float | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    invoice: Mapped["Invoice"] = relationship(
        back_populates="items",
    )

class FieldConfidence(Base):
    __tablename__ = "field_confidences"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    invoice_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "invoices.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    field_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    field_value: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    source_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    invoice: Mapped["Invoice"] = relationship(
        back_populates="confidences",
    )

class ValidationResult(Base):
    __tablename__ = "validation_results"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    invoice_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "invoices.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    rule_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    invoice: Mapped["Invoice"] = relationship(
        back_populates="validations",
    )