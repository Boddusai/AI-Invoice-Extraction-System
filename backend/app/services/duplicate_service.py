import re
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher


DUPLICATE_THRESHOLD = 70


def normalize_string(
    value: str | None,
) -> str | None:

    if not value:
        return None

    value = value.upper().strip()

    value = re.sub(
        r"[^A-Z0-9]",
        "",
        value,
    )

    return value or None


def normalize_vendor_name(
    value: str | None,
) -> str | None:

    return normalize_string(value)


def normalize_ocr_identifier(
    value: str | None,
) -> str | None:
    """
    Normalize characters commonly confused by OCR.

    I / L / 1
    O / 0
    """

    value = normalize_string(value)

    if not value:
        return None

    replacements = str.maketrans(
        {
            "I": "1",
            "L": "1",
            "O": "0",
        }
    )

    return value.translate(
        replacements
    )


def identifier_similarity(
    value1: str | None,
    value2: str | None,
) -> float:

    first = normalize_ocr_identifier(
        value1
    )

    second = normalize_ocr_identifier(
        value2
    )

    if not first or not second:
        return 0.0

    return SequenceMatcher(
        None,
        first,
        second,
    ).ratio()


def amounts_match(
    value1,
    value2,
    tolerance: Decimal = Decimal("0.05"),
) -> bool:

    if (
        value1 is None
        or value2 is None
    ):
        return False

    try:

        amount1 = Decimal(
            str(value1)
        )

        amount2 = Decimal(
            str(value2)
        )

        return abs(
            amount1 - amount2
        ) <= tolerance

    except (
        InvalidOperation,
        ValueError,
        TypeError,
    ):

        return False


def compare_invoices(
    current_invoice,
    candidate_invoice,
) -> dict:

    score = 0

    matched_fields = []

    # --------------------------------
    # Invoice number
    # --------------------------------

    current_number = normalize_string(
        current_invoice.invoice_number
    )

    candidate_number = normalize_string(
        candidate_invoice.invoice_number
    )

    if (
        current_number
        and candidate_number
    ):

        if (
            current_number
            == candidate_number
        ):

            score += 45

            matched_fields.append(
                "invoice_number"
            )

        else:

            similarity = (
                identifier_similarity(
                    current_number,
                    candidate_number,
                )
            )

            # OCR-tolerant comparison
            if similarity >= 0.90:

                score += 45

                matched_fields.append(
                    "invoice_number_fuzzy"
                )

            elif similarity >= 0.80:

                score += 30

                matched_fields.append(
                    "invoice_number_possible"
                )

    # --------------------------------
    # GSTIN
    # --------------------------------

    current_gstin = normalize_string(
        current_invoice.vendor_gstin
    )

    candidate_gstin = normalize_string(
        candidate_invoice.vendor_gstin
    )

    if (
        current_gstin
        and candidate_gstin
        and current_gstin
        == candidate_gstin
    ):

        score += 25

        matched_fields.append(
            "vendor_gstin"
        )

    # --------------------------------
    # Vendor fallback
    # --------------------------------

    else:

        current_vendor = (
            normalize_vendor_name(
                current_invoice.vendor_name
            )
        )

        candidate_vendor = (
            normalize_vendor_name(
                candidate_invoice.vendor_name
            )
        )

        if (
            current_vendor
            and candidate_vendor
            and (
                current_vendor
                in candidate_vendor
                or candidate_vendor
                in current_vendor
            )
        ):

            score += 15

            matched_fields.append(
                "vendor_name"
            )

    # --------------------------------
    # Invoice date
    # --------------------------------

    if (
        current_invoice.invoice_date
        and candidate_invoice.invoice_date
        and current_invoice.invoice_date
        == candidate_invoice.invoice_date
    ):

        score += 15

        matched_fields.append(
            "invoice_date"
        )

    # --------------------------------
    # Grand total
    # --------------------------------

    if amounts_match(
        current_invoice.grand_total,
        candidate_invoice.grand_total,
    ):

        score += 15

        matched_fields.append(
            "grand_total"
        )

    return {
        "is_duplicate": (
            score >= DUPLICATE_THRESHOLD
        ),
        "score": score,
        "matched_fields": matched_fields,
    }


def find_duplicate_invoice(
    current_invoice,
    candidate_invoices,
):

    best_match = None
    best_score = 0
    best_fields = []

    for candidate in candidate_invoices:

        if (
            candidate.id
            == current_invoice.id
        ):
            continue

        comparison = compare_invoices(
            current_invoice,
            candidate,
        )

        if (
            comparison["score"]
            > best_score
        ):

            best_score = (
                comparison["score"]
            )

            best_match = candidate

            best_fields = comparison[
                "matched_fields"
            ]

    is_duplicate = (
        best_match is not None
        and best_score
        >= DUPLICATE_THRESHOLD
    )

    return {
        "is_duplicate": is_duplicate,

        "duplicate_invoice": (
            best_match
            if is_duplicate
            else None
        ),

        "score": best_score,

        "matched_fields": (
            best_fields
        ),
    }