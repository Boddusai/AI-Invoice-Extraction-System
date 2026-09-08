import re
from typing import Optional


def clean_line(line: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        line,
    ).strip()


def to_float(
    value: str,
) -> Optional[float]:

    if not value:
        return None

    cleaned = (
        value
        .replace(",", "")
        .replace("₹", "")
        .strip()
    )

    try:
        return float(cleaned)

    except ValueError:
        return None


def is_number(
    value: str,
) -> bool:

    cleaned = (
        value
        .replace(",", "")
        .strip()
    )

    return bool(
        re.fullmatch(
            r"\d+(?:\.\d+)?",
            cleaned,
        )
    )


def calculate_confidence(
    item: dict,
) -> float:

    score = 0.0

    if item.get("description"):
        score += 0.25

    if item.get("quantity") is not None:
        score += 0.15

    if item.get("unit_price") is not None:
        score += 0.20

    if item.get("tax_amount") is not None:
        score += 0.15

    if item.get("tax_rate") is not None:
        score += 0.10

    if item.get("line_total") is not None:
        score += 0.15

    return round(
        min(score, 1.0),
        2,
    )


def extract_invoice_table_block(
    text: str,
) -> list[str]:

    lines = [
        clean_line(line)
        for line in text.splitlines()
        if clean_line(line)
    ]

    start_index = None
    end_index = None

    for index, line in enumerate(lines):

        lower = line.lower()

        if (
            "description of goods"
            in lower
            or "description of item"
            in lower
            or "item description"
            in lower
        ):
            start_index = index

        if (
            start_index is not None
            and (
                "total taxable amount"
                in lower
                or "subtotal"
                in lower
                or "grand total"
                in lower
            )
        ):
            end_index = index
            break

    if start_index is None:
        return []

    if end_index is None:
        end_index = len(lines)

    return lines[
        start_index + 1:
        end_index
    ]


def remove_table_headers(
    lines: list[str],
) -> list[str]:

    ignored_headers = {
        "hsn",
        "sac",
        "qty",
        "quantity",
        "uqc",
        "cur",
        "currency",
        "discount",
        "taxable",
        "value",
        "igst",
        "cgst",
        "sgst",
        "total invoice",
        "total invoice value",
        "unit price",
        "gross price",
        "(excl. tax)",
        "excl. tax",
        "@",
        "%",
    }

    result = []

    for line in lines:

        lower = line.lower().strip()

        if lower in ignored_headers:
            continue

        if lower.startswith(
            "unit price"
        ):
            continue

        if lower.startswith(
            "gross price"
        ):
            continue

        if lower.startswith(
            "total invoice value"
        ):
            continue

        result.append(line)

    return result


def extract_single_item_block(
    lines: list[str],
) -> Optional[dict]:

    lines = remove_table_headers(
        lines
    )

    if not lines:
        return None

    description_parts = []
    numeric_values = []

    hsn = None
    currency = None

    quantity = None

    for line in lines:

        upper = line.upper()

        if upper in {
            "INR",
            "USD",
            "EUR",
            "GBP",
        }:

            currency = upper
            continue

        # Six/eight digit values are often HSN/SAC.
        if (
            re.fullmatch(
                r"\d{4,8}",
                line,
            )
            and hsn is None
            and len(numeric_values) == 0
        ):

            hsn = line
            continue

        if is_number(line):

            numeric_values.append(
                to_float(line)
            )

            continue

        # Ignore common units
        if upper in {
            "NOS",
            "NO",
            "PCS",
            "PC",
            "EA",
            "UNIT",
            "UNITS",
        }:
            continue

        description_parts.append(
            line
        )

    if not numeric_values:

        return None

    # -------------------------------------------------
    # Expected invoice pattern:
    #
    # Unit Price
    # Qty
    # Gross Price
    # Discount
    # Taxable Value
    # Tax Amount
    # Tax Rate
    # Line Total
    # -------------------------------------------------

    unit_price = None
    tax_amount = None
    tax_rate = None
    line_total = None

    # Example:
    # 422.88
    # 1
    # 422.88
    # 0
    # 422.88
    # 76.12
    # 18
    # 499

    if len(numeric_values) >= 8:

        unit_price = numeric_values[0]

        quantity = numeric_values[1]

        tax_amount = numeric_values[-3]

        tax_rate = numeric_values[-2]

        line_total = numeric_values[-1]

    elif len(numeric_values) >= 5:

        unit_price = numeric_values[0]

        quantity = numeric_values[1]

        tax_amount = numeric_values[-2]

        line_total = numeric_values[-1]

    elif len(numeric_values) >= 3:

        unit_price = numeric_values[0]

        quantity = numeric_values[1]

        line_total = numeric_values[-1]

    description = " ".join(
        description_parts
    ).strip()

    item = {
        "description": description or None,
        "hsn": hsn,
        "quantity": quantity,
        "unit_price": unit_price,
        "tax_rate": tax_rate,
        "tax_amount": tax_amount,
        "line_total": line_total,
        "currency": currency,
    }

    item["confidence"] = (
        calculate_confidence(
            item
        )
    )

    return item


def extract_line_items(
    raw_text: str,
) -> list[dict]:

    if not raw_text:
        return []

    table_lines = (
        extract_invoice_table_block(
            raw_text
        )
    )

    if not table_lines:
        return []

    item = extract_single_item_block(
        table_lines
    )

    if item is None:
        return []

    return [item]