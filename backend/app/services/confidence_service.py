import re
from decimal import Decimal
from typing import Any


GSTIN_PATTERN = re.compile(
    r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z]$"
)


def value_to_string(
    value: Any,
) -> str | None:

    if value is None:
        return None

    return str(value)


def calculate_amount_consistency(
    subtotal,
    tax_amount,
    grand_total,
) -> bool:
    """
    Check:

    subtotal + tax ≈ grand total
    """

    if (
        subtotal is None
        or tax_amount is None
        or grand_total is None
    ):
        return False

    try:

        subtotal_value = Decimal(
            str(subtotal)
        )

        tax_value = Decimal(
            str(tax_amount)
        )

        total_value = Decimal(
            str(grand_total)
        )

        difference = abs(
            (subtotal_value + tax_value)
            - total_value
        )

        return difference <= Decimal(
            "0.05"
        )

    except Exception:
        return False


def find_source_text(
    raw_text: str,
    value: Any,
) -> str | None:
    """
    Find a small source-text section containing
    the extracted value.
    """

    if not raw_text or value is None:
        return None

    value_string = str(value)

    # Date objects become YYYY-MM-DD in Python,
    # which may not occur directly in the invoice,
    # so source matching is best-effort.
    lines = raw_text.splitlines()

    for index, line in enumerate(lines):

        if (
            value_string.lower()
            in line.lower()
        ):

            start = max(
                0,
                index - 1,
            )

            end = min(
                len(lines),
                index + 2,
            )

            return " | ".join(
                line.strip()
                for line in lines[
                    start:end
                ]
                if line.strip()
            )[:500]

    return None


def calculate_field_confidences(
    invoice,
) -> list[dict]:

    raw_text = (
        invoice.raw_ocr_text or ""
    )

    amount_consistent = (
        calculate_amount_consistency(
            invoice.subtotal,
            invoice.tax_amount,
            invoice.grand_total,
        )
    )

    results = []

    # -----------------------------------
    # Vendor name
    # -----------------------------------

    if invoice.vendor_name:

        confidence = 0.90

        if (
            invoice.vendor_name.lower()
            in raw_text.lower()
        ):
            confidence = 0.96

    else:
        confidence = 0.0

    results.append(
        {
            "field_name": "vendor_name",
            "field_value": value_to_string(
                invoice.vendor_name
            ),
            "confidence": confidence,
            "source_text": find_source_text(
                raw_text,
                invoice.vendor_name,
            ),
        }
    )

    # -----------------------------------
    # GSTIN
    # -----------------------------------

    if invoice.vendor_gstin:

        if GSTIN_PATTERN.fullmatch(
            invoice.vendor_gstin.upper()
        ):
            confidence = 0.99
        else:
            confidence = 0.60

    else:
        confidence = 0.0

    results.append(
        {
            "field_name": "vendor_gstin",
            "field_value": value_to_string(
                invoice.vendor_gstin
            ),
            "confidence": confidence,
            "source_text": find_source_text(
                raw_text,
                invoice.vendor_gstin,
            ),
        }
    )

    # -----------------------------------
    # Invoice number
    # -----------------------------------

    if invoice.invoice_number:

        confidence = 0.93

        if (
            invoice.invoice_number.lower()
            in raw_text.lower()
        ):
            confidence = 0.98

    else:
        confidence = 0.0

    results.append(
        {
            "field_name": "invoice_number",
            "field_value": value_to_string(
                invoice.invoice_number
            ),
            "confidence": confidence,
            "source_text": find_source_text(
                raw_text,
                invoice.invoice_number,
            ),
        }
    )

    # -----------------------------------
    # Invoice date
    # -----------------------------------

    if invoice.invoice_date:
        confidence = 0.95
    else:
        confidence = 0.0

    results.append(
        {
            "field_name": "invoice_date",
            "field_value": value_to_string(
                invoice.invoice_date
            ),
            "confidence": confidence,
            "source_text": None,
        }
    )

    # -----------------------------------
    # Due date
    # -----------------------------------

    if invoice.due_date:
        confidence = 0.90
    else:
        confidence = 0.0

    results.append(
        {
            "field_name": "due_date",
            "field_value": value_to_string(
                invoice.due_date
            ),
            "confidence": confidence,
            "source_text": None,
        }
    )

    # -----------------------------------
    # Subtotal
    # -----------------------------------

    if invoice.subtotal is not None:

        confidence = (
            0.98
            if amount_consistent
            else 0.85
        )

    else:
        confidence = 0.0

    results.append(
        {
            "field_name": "subtotal",
            "field_value": value_to_string(
                invoice.subtotal
            ),
            "confidence": confidence,
            "source_text": find_source_text(
                raw_text,
                invoice.subtotal,
            ),
        }
    )

    # -----------------------------------
    # Tax
    # -----------------------------------

    if invoice.tax_amount is not None:

        confidence = (
            0.98
            if amount_consistent
            else 0.85
        )

    else:
        confidence = 0.0

    results.append(
        {
            "field_name": "tax_amount",
            "field_value": value_to_string(
                invoice.tax_amount
            ),
            "confidence": confidence,
            "source_text": find_source_text(
                raw_text,
                invoice.tax_amount,
            ),
        }
    )

    # -----------------------------------
    # Grand total
    # -----------------------------------

    if invoice.grand_total is not None:

        confidence = (
            0.99
            if amount_consistent
            else 0.88
        )

    else:
        confidence = 0.0

    results.append(
        {
            "field_name": "grand_total",
            "field_value": value_to_string(
                invoice.grand_total
            ),
            "confidence": confidence,
            "source_text": find_source_text(
                raw_text,
                invoice.grand_total,
            ),
        }
    )

    # -----------------------------------
    # Currency
    # -----------------------------------

    if invoice.currency:

        confidence = 0.90

        if (
            invoice.currency.upper()
            in raw_text.upper()
        ):
            confidence = 0.97

    else:
        confidence = 0.0

    results.append(
        {
            "field_name": "currency",
            "field_value": value_to_string(
                invoice.currency
            ),
            "confidence": confidence,
            "source_text": find_source_text(
                raw_text,
                invoice.currency,
            ),
        }
    )

    return results