import re
from datetime import date
from decimal import Decimal, InvalidOperation


GSTIN_PATTERN = re.compile(
    r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z]$"
)

AMOUNT_TOLERANCE = Decimal("0.05")


def to_decimal(value):
    if value is None:
        return None

    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def create_result(
    rule_name: str,
    status: str,
    message: str,
) -> dict:

    return {
        "rule_name": rule_name,
        "status": status,
        "message": message,
    }


def validate_required_fields(invoice) -> dict:

    missing_fields = []

    required_fields = {
        "vendor_name": invoice.vendor_name,
        "invoice_number": invoice.invoice_number,
        "invoice_date": invoice.invoice_date,
        "grand_total": invoice.grand_total,
    }

    for field_name, value in required_fields.items():

        if value is None or value == "":
            missing_fields.append(field_name)

    if missing_fields:

        return create_result(
            "required_fields",
            "failed",
            (
                "Missing required fields: "
                + ", ".join(missing_fields)
            ),
        )

    return create_result(
        "required_fields",
        "passed",
        "All required invoice fields are present.",
    )


def validate_gstin(invoice) -> dict:

    gstin = invoice.vendor_gstin

    if not gstin:

        return create_result(
            "gstin_format",
            "warning",
            "GSTIN was not detected.",
        )

    if GSTIN_PATTERN.fullmatch(
        gstin.upper()
    ):

        return create_result(
            "gstin_format",
            "passed",
            "GSTIN format is valid.",
        )

    return create_result(
        "gstin_format",
        "failed",
        "GSTIN format is invalid.",
    )


def validate_amounts(invoice) -> dict:

    subtotal = to_decimal(
        invoice.subtotal
    )

    tax_amount = to_decimal(
        invoice.tax_amount
    )

    grand_total = to_decimal(
        invoice.grand_total
    )

    if grand_total is None:

        return create_result(
            "total_calculation",
            "failed",
            "Grand total is missing.",
        )

    if (
        subtotal is None
        or tax_amount is None
    ):

        return create_result(
            "total_calculation",
            "warning",
            (
                "Subtotal or tax amount is missing, "
                "so total calculation could not "
                "be fully validated."
            ),
        )

    calculated_total = (
        subtotal + tax_amount
    )

    difference = abs(
        calculated_total - grand_total
    )

    if difference <= AMOUNT_TOLERANCE:

        return create_result(
            "total_calculation",
            "passed",
            (
                f"Subtotal {subtotal} + "
                f"Tax {tax_amount} = "
                f"Grand Total {grand_total}."
            ),
        )

    return create_result(
        "total_calculation",
        "failed",
        (
            f"Amount mismatch: subtotal "
            f"{subtotal} + tax {tax_amount} "
            f"= {calculated_total}, but "
            f"grand total is {grand_total}."
        ),
    )


def validate_positive_amounts(invoice) -> dict:

    amounts = {
        "subtotal": invoice.subtotal,
        "tax_amount": invoice.tax_amount,
        "grand_total": invoice.grand_total,
    }

    invalid_fields = []

    for field_name, value in amounts.items():

        if value is None:
            continue

        decimal_value = to_decimal(
            value
        )

        if (
            decimal_value is None
            or decimal_value < 0
        ):
            invalid_fields.append(
                field_name
            )

    if invalid_fields:

        return create_result(
            "positive_amounts",
            "failed",
            (
                "Invalid negative or malformed "
                "amounts found in: "
                + ", ".join(invalid_fields)
            ),
        )

    return create_result(
        "positive_amounts",
        "passed",
        "Invoice amounts are non-negative.",
    )


def validate_invoice_date(invoice) -> dict:

    if invoice.invoice_date is None:

        return create_result(
            "invoice_date",
            "failed",
            "Invoice date is missing.",
        )

    if invoice.invoice_date > date.today():

        return create_result(
            "invoice_date",
            "warning",
            (
                "Invoice date is in the future: "
                f"{invoice.invoice_date}."
            ),
        )

    return create_result(
        "invoice_date",
        "passed",
        (
            f"Invoice date "
            f"{invoice.invoice_date} is valid."
        ),
    )


def validate_due_date(invoice) -> dict:

    if invoice.due_date is None:

        return create_result(
            "due_date",
            "passed",
            (
                "Due date is not present; "
                "this field is optional."
            ),
        )

    if invoice.invoice_date is None:

        return create_result(
            "due_date",
            "warning",
            (
                "Due date exists but invoice date "
                "is unavailable for comparison."
            ),
        )

    if invoice.due_date < invoice.invoice_date:

        return create_result(
            "due_date",
            "failed",
            (
                "Due date occurs before "
                "the invoice date."
            ),
        )

    return create_result(
        "due_date",
        "passed",
        "Due date is valid.",
    )


def validate_line_items(
    invoice,
    items,
) -> list[dict]:

    results = []

    if not items:

        results.append(
            create_result(
                "line_items_present",
                "warning",
                (
                    "No line items are available "
                    "for validation."
                ),
            )
        )

        return results

    results.append(
        create_result(
            "line_items_present",
            "passed",
            (
                f"{len(items)} line item(s) "
                "available for validation."
            ),
        )
    )

    invalid_items = []

    for item in items:

        quantity = to_decimal(
            item.quantity
        )

        unit_price = to_decimal(
            item.unit_price
        )

        tax_amount = to_decimal(
            item.tax_amount
        )

        line_total = to_decimal(
            item.line_total
        )

        if (
            quantity is None
            or unit_price is None
            or line_total is None
        ):
            continue

        expected_before_tax = (
            quantity * unit_price
        )

        if tax_amount is not None:
            expected_total = (
                expected_before_tax
                + tax_amount
            )
        else:
            expected_total = (
                expected_before_tax
            )

        difference = abs(
            expected_total - line_total
        )

        if difference > AMOUNT_TOLERANCE:

            invalid_items.append(
                item.id
            )

    if invalid_items:

        results.append(
            create_result(
                "line_item_calculation",
                "failed",
                (
                    "Calculation mismatch in "
                    "line item IDs: "
                    + ", ".join(
                        str(item_id)
                        for item_id in invalid_items
                    )
                ),
            )
        )

    else:

        results.append(
            create_result(
                "line_item_calculation",
                "passed",
                (
                    "Line-item calculations "
                    "are valid."
                ),
            )
        )

    # ----------------------------------
    # Compare sum of item totals
    # with invoice grand total
    # ----------------------------------

    grand_total = to_decimal(
        invoice.grand_total
    )

    item_totals = [
        to_decimal(item.line_total)
        for item in items
        if item.line_total is not None
    ]

    item_totals = [
        value
        for value in item_totals
        if value is not None
    ]

    if (
        grand_total is not None
        and item_totals
    ):

        summed_total = sum(
            item_totals,
            Decimal("0.00"),
        )

        difference = abs(
            summed_total - grand_total
        )

        if difference <= AMOUNT_TOLERANCE:

            results.append(
                create_result(
                    "line_items_vs_total",
                    "passed",
                    (
                        f"Line-item total "
                        f"{summed_total} matches "
                        f"invoice total "
                        f"{grand_total}."
                    ),
                )
            )

        else:

            results.append(
                create_result(
                    "line_items_vs_total",
                    "failed",
                    (
                        f"Line-item sum is "
                        f"{summed_total}, but "
                        f"invoice total is "
                        f"{grand_total}."
                    ),
                )
            )

    else:

        results.append(
            create_result(
                "line_items_vs_total",
                "warning",
                (
                    "Unable to compare line-item "
                    "total with invoice grand total."
                ),
            )
        )

    return results


def determine_overall_status(
    results: list[dict],
) -> str:

    statuses = [
        result["status"]
        for result in results
    ]

    if "failed" in statuses:
        return "INVALID"

    if "warning" in statuses:
        return "WARNING"

    return "VALID"


def validate_invoice(
    invoice,
    items,
) -> dict:

    results = [
        validate_required_fields(
            invoice
        ),
        validate_gstin(
            invoice
        ),
        validate_amounts(
            invoice
        ),
        validate_positive_amounts(
            invoice
        ),
        validate_invoice_date(
            invoice
        ),
        validate_due_date(
            invoice
        ),
    ]

    results.extend(
        validate_line_items(
            invoice,
            items,
        )
    )

    overall_status = (
        determine_overall_status(
            results
        )
    )

    passed_count = sum(
        1
        for result in results
        if result["status"] == "passed"
    )

    warning_count = sum(
        1
        for result in results
        if result["status"] == "warning"
    )

    failed_count = sum(
        1
        for result in results
        if result["status"] == "failed"
    )

    return {
        "overall_status": overall_status,
        "passed_count": passed_count,
        "warning_count": warning_count,
        "failed_count": failed_count,
        "results": results,
    }