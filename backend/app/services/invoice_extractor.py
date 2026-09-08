import re
from datetime import datetime
from typing import Optional


def normalize_text(text: str) -> str:
    """
    Clean OCR/PDF text while preserving line structure.
    """

    if not text:
        return ""

    text = text.replace("\r", "\n")

    # Repair dates broken by OCR/PDF extraction:
    # 31/07
    # /2026
    # becomes 31/07/2026
    text = re.sub(
        r"(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{2,4})",
        r"\1/\2/\3",
        text,
    )

    # Remove excessive spaces
    lines = []

    for line in text.splitlines():
        cleaned = re.sub(
            r"[ \t]+",
            " ",
            line,
        ).strip()

        if cleaned:
            lines.append(cleaned)

    return "\n".join(lines)


def parse_date(
    value: Optional[str],
):
    if not value:
        return None

    value = value.strip()

    formats = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d.%m.%Y",
        "%Y-%m-%d",
        "%d/%m/%y",
        "%d-%m-%y",
    ]

    for date_format in formats:

        try:
            return datetime.strptime(
                value,
                date_format,
            ).date()

        except ValueError:
            continue

    return None


def extract_gstin(
    text: str,
) -> Optional[str]:

    pattern = (
        r"\b"
        r"[0-9]{2}"
        r"[A-Z]{5}"
        r"[0-9]{4}"
        r"[A-Z]"
        r"[0-9A-Z]"
        r"Z"
        r"[0-9A-Z]"
        r"\b"
    )

    match = re.search(
        pattern,
        text.upper(),
    )

    if match:
        return match.group(0)

    return None


def extract_invoice_number(
    text: str,
) -> Optional[str]:

    patterns = [
        r"Invoice\s*(?:No\.?|Number)\s*[:#-]?\s*([A-Z0-9][A-Z0-9/_-]+)",
        r"Invoice\s*#\s*[:#-]?\s*([A-Z0-9][A-Z0-9/_-]+)",
        r"Invoice\s*:\s*#?\s*([A-Z0-9][A-Z0-9/_-]+)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:
            return match.group(1).strip()

    return None


def extract_date_by_label(
    text: str,
    label: str,
):
    pattern = (
        rf"{label}"
        r"\s*[:#-]?\s*"
        r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
    )

    match = re.search(
        pattern,
        text,
        re.IGNORECASE,
    )

    if match:

        return parse_date(
            match.group(1)
        )

    return None


def parse_amount(
    value: str,
) -> Optional[float]:

    if not value:
        return None

    value = (
        value
        .replace(",", "")
        .replace("₹", "")
        .strip()
    )

    try:
        return float(value)

    except ValueError:
        return None


def extract_amount_by_patterns(
    text: str,
    patterns: list[str],
) -> Optional[float]:

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:

            amount = parse_amount(
                match.group(1)
            )

            if amount is not None:
                return amount

    return None


def extract_vendor_name(
    text: str,
) -> Optional[str]:

    lines = text.splitlines()

    ignored_words = {
        "invoice",
        "tax invoice",
        "original",
        "duplicate",
        "triplicate",
        "authorized signatory",
    }

    for line in lines[:15]:

        cleaned = line.strip()

        if not cleaned:
            continue

        lowered = cleaned.lower()

        if lowered.startswith("--- page"):
            continue

        if lowered in ignored_words:
            continue

        if "invoice no" in lowered:
            continue

        if "invoice date" in lowered:
            continue

        if "gstin" in lowered:
            continue

        if len(cleaned) < 3:
            continue

        # Avoid choosing a mostly numeric line
        if re.fullmatch(
            r"[\d\s:/#.-]+",
            cleaned,
        ):
            continue

        return cleaned[:255]

    return None


def detect_currency(
    text: str,
) -> str:

    upper_text = text.upper()

    if (
        "INR" in upper_text
        or "₹" in text
        or "RS." in upper_text
        or "RS " in upper_text
    ):
        return "INR"

    if (
        "USD" in upper_text
        or "$" in text
    ):
        return "USD"

    if (
        "EUR" in upper_text
        or "€" in text
    ):
        return "EUR"

    if (
        "GBP" in upper_text
        or "£" in text
    ):
        return "GBP"

    return "INR"

def extract_invoice_summary(
    text: str,
) -> dict:
    """
    Extract summary values from invoices where labels
    and amounts appear on separate lines.

    Example:

    Total Taxable Amount :
    IGST :
    CGST :
    SGST :
    Grand Total(incl. of taxes) :
    422.88
    76.12
    0.00
    0.00
    499.00
    """

    result = {
        "subtotal": None,
        "tax_amount": None,
        "grand_total": None,
    }

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    # -----------------------------------
    # Find summary labels
    # -----------------------------------

    taxable_index = None
    grand_total_index = None

    for index, line in enumerate(lines):

        lowered = line.lower()

        if (
            "total taxable amount"
            in lowered
        ):
            taxable_index = index

        if (
            "grand total"
            in lowered
        ):
            grand_total_index = index

    # -----------------------------------
    # Special summary block handling
    # -----------------------------------

    if (
        taxable_index is not None
        and grand_total_index is not None
    ):

        amount_lines = []

        # Amounts normally appear after
        # the Grand Total label
        for line in lines[
            grand_total_index + 1:
            grand_total_index + 15
        ]:

            cleaned = (
                line
                .replace(",", "")
                .replace("₹", "")
                .strip()
            )

            if re.fullmatch(
                r"\d+(?:\.\d{1,2})?",
                cleaned,
            ):

                try:
                    amount_lines.append(
                        float(cleaned)
                    )
                except ValueError:
                    pass

        # Typical GST summary:
        #
        # taxable
        # IGST
        # CGST
        # SGST
        # grand total

        if len(amount_lines) >= 1:
            result["subtotal"] = (
                amount_lines[0]
            )

        if len(amount_lines) >= 2:

            # First GST amount
            tax_total = amount_lines[1]

            # If CGST / SGST also exist,
            # add them.
            if len(amount_lines) >= 4:

                tax_total = (
                    amount_lines[1]
                    + amount_lines[2]
                    + amount_lines[3]
                )

            result["tax_amount"] = (
                tax_total
            )

        if len(amount_lines) >= 5:

            result["grand_total"] = (
                amount_lines[4]
            )

        elif len(amount_lines) >= 3:

            # Fallback:
            # final number is usually total
            result["grand_total"] = (
                amount_lines[-1]
            )

    return result


def extract_invoice_fields(
    raw_text: str,
) -> dict:

    text = normalize_text(
        raw_text
    )

    vendor_name = extract_vendor_name(
        text
    )

    vendor_gstin = extract_gstin(
        text
    )

    invoice_number = extract_invoice_number(
        text
    )

    invoice_date = extract_date_by_label(
        text,
        r"Invoice\s*Date",
    )

    due_date = extract_date_by_label(
        text,
        r"(?:Due\s*Date|Payment\s*Due)",
    )

    subtotal = extract_amount_by_patterns(
        text,
        [
            r"Sub\s*Total\s*[:₹Rs.\s]*([\d,]+(?:\.\d{1,2})?)",
            r"Subtotal\s*[:₹Rs.\s]*([\d,]+(?:\.\d{1,2})?)",
            r"Total\s+Taxable\s+Amount\s*[:₹Rs.\s]*([\d,]+(?:\.\d{1,2})?)",
            r"Taxable\s+Value\s*[:₹Rs.\s]*([\d,]+(?:\.\d{1,2})?)",
        ],
    )

    tax_amount = extract_amount_by_patterns(
        text,
        [
            r"Total\s+Tax\s*[:₹Rs.\s]*([\d,]+(?:\.\d{1,2})?)",
            r"Tax\s+Amount\s*[:₹Rs.\s]*([\d,]+(?:\.\d{1,2})?)",
            r"IGST\s*[:₹Rs.\s]*([\d,]+(?:\.\d{1,2})?)",
            r"GST\s*[:₹Rs.\s]*([\d,]+(?:\.\d{1,2})?)",
        ],
    )

    grand_total = extract_amount_by_patterns(
        text,
        [
            r"Grand\s+Total(?:\s*\([^)]*\))?\s*[:₹Rs.\s]*([\d,]+(?:\.\d{1,2})?)",
            r"Total\s+Invoice\s+Value\s*[:₹Rs.\s]*([\d,]+(?:\.\d{1,2})?)",
            r"Amount\s+Payable\s*[:₹Rs.\s]*([\d,]+(?:\.\d{1,2})?)",
            r"Net\s+Amount\s*[:₹Rs.\s]*([\d,]+(?:\.\d{1,2})?)",
        ],
    )

    currency = detect_currency(
        text
    )

    summary = extract_invoice_summary(
        text
    )

    # Use summary block values when
    # normal regex extraction failed
    # or produced an unreliable total.

    if summary["subtotal"] is not None:
        subtotal = summary["subtotal"]

    if summary["tax_amount"] is not None:
        tax_amount = summary["tax_amount"]

    if summary["grand_total"] is not None:
        grand_total = summary["grand_total"]

    return {
        "vendor_name": vendor_name,
        "vendor_gstin": vendor_gstin,
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "due_date": due_date,
        "subtotal": subtotal,
        "tax_amount": tax_amount,
        "grand_total": grand_total,
        "currency": currency,
    }