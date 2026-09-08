import csv
import io
import json
from datetime import date, datetime
from decimal import Decimal

import xlsxwriter


def serialize_value(value):
    """
    Convert database values into JSON/CSV-safe values.
    """

    if value is None:
        return None

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    return value


def build_invoice_data(
    invoice,
    items,
    confidences,
    validations,
) -> dict:

    return {
        "invoice": {
            "id": invoice.id,
            "file_name": invoice.file_name,
            "vendor_name": invoice.vendor_name,
            "vendor_gstin": invoice.vendor_gstin,
            "invoice_number": invoice.invoice_number,
            "invoice_date": serialize_value(
                invoice.invoice_date
            ),
            "due_date": serialize_value(
                invoice.due_date
            ),
            "subtotal": serialize_value(
                invoice.subtotal
            ),
            "tax_amount": serialize_value(
                invoice.tax_amount
            ),
            "grand_total": serialize_value(
                invoice.grand_total
            ),
            "currency": invoice.currency,
            "is_duplicate": invoice.is_duplicate,
            "duplicate_of": invoice.duplicate_of,
            "processing_status": (
                invoice.processing_status
            ),
            "created_at": serialize_value(
                invoice.created_at
            ),
            "updated_at": serialize_value(
                invoice.updated_at
            ),
        },

        "line_items": [
            {
                "id": item.id,
                "description": item.description,
                "quantity": serialize_value(
                    item.quantity
                ),
                "unit_price": serialize_value(
                    item.unit_price
                ),
                "tax_rate": serialize_value(
                    item.tax_rate
                ),
                "tax_amount": serialize_value(
                    item.tax_amount
                ),
                "line_total": serialize_value(
                    item.line_total
                ),
                "confidence": serialize_value(
                    item.confidence
                ),
            }
            for item in items
        ],

        "confidence_scores": [
            {
                "field_name": score.field_name,
                "field_value": score.field_value,
                "confidence": score.confidence,
                "confidence_percentage": round(
                    score.confidence * 100,
                    2,
                ),
                "source_text": score.source_text,
            }
            for score in confidences
        ],

        "validations": [
            {
                "rule_name": result.rule_name,
                "status": result.status,
                "message": result.message,
            }
            for result in validations
        ],
    }


def create_json_export(data: dict) -> bytes:

    json_content = json.dumps(
        data,
        indent=4,
        ensure_ascii=False,
    )

    return json_content.encode(
        "utf-8"
    )


def create_csv_export(data: dict) -> bytes:
    """
    CSV contains invoice details followed by
    line items, confidence scores and validations.
    """

    output = io.StringIO()

    writer = csv.writer(output)

    # ----------------------------------
    # Invoice details
    # ----------------------------------

    writer.writerow(
        ["INVOICE DETAILS"]
    )

    writer.writerow(
        ["Field", "Value"]
    )

    for key, value in data[
        "invoice"
    ].items():

        writer.writerow(
            [
                key,
                "" if value is None else value,
            ]
        )

    writer.writerow([])

    # ----------------------------------
    # Line items
    # ----------------------------------

    writer.writerow(
        ["LINE ITEMS"]
    )

    writer.writerow(
        [
            "ID",
            "Description",
            "Quantity",
            "Unit Price",
            "Tax Rate",
            "Tax Amount",
            "Line Total",
            "Confidence",
        ]
    )

    for item in data["line_items"]:

        writer.writerow(
            [
                item["id"],
                item["description"],
                item["quantity"],
                item["unit_price"],
                item["tax_rate"],
                item["tax_amount"],
                item["line_total"],
                item["confidence"],
            ]
        )

    writer.writerow([])

    # ----------------------------------
    # Confidence scores
    # ----------------------------------

    writer.writerow(
        ["CONFIDENCE SCORES"]
    )

    writer.writerow(
        [
            "Field",
            "Value",
            "Confidence %",
            "Source Text",
        ]
    )

    for score in data[
        "confidence_scores"
    ]:

        writer.writerow(
            [
                score["field_name"],
                score["field_value"],
                score[
                    "confidence_percentage"
                ],
                score["source_text"],
            ]
        )

    writer.writerow([])

    # ----------------------------------
    # Validation
    # ----------------------------------

    writer.writerow(
        ["VALIDATION RESULTS"]
    )

    writer.writerow(
        [
            "Rule",
            "Status",
            "Message",
        ]
    )

    for result in data["validations"]:

        writer.writerow(
            [
                result["rule_name"],
                result["status"],
                result["message"],
            ]
        )

    return output.getvalue().encode(
        "utf-8-sig"
    )


def create_excel_export(
    data: dict,
) -> bytes:

    output = io.BytesIO()

    workbook = xlsxwriter.Workbook(
        output,
        {
            "in_memory": True
        },
    )

    # ==================================
    # Formats
    # ==================================

    title_format = workbook.add_format(
        {
            "bold": True,
            "font_size": 16,
            "align": "center",
            "valign": "vcenter",
        }
    )

    header_format = workbook.add_format(
        {
            "bold": True,
            "border": 1,
            "align": "center",
            "valign": "vcenter",
        }
    )

    label_format = workbook.add_format(
        {
            "bold": True,
            "border": 1,
        }
    )

    value_format = workbook.add_format(
        {
            "border": 1,
        }
    )

    money_format = workbook.add_format(
        {
            "border": 1,
            "num_format": "#,##0.00",
        }
    )

    percent_format = workbook.add_format(
        {
            "border": 1,
            "num_format": "0.00%",
        }
    )

    wrap_format = workbook.add_format(
        {
            "border": 1,
            "text_wrap": True,
            "valign": "top",
        }
    )

    # ==================================
    # Sheet 1 — Invoice
    # ==================================

    invoice_sheet = workbook.add_worksheet(
        "Invoice Details"
    )

    invoice_sheet.merge_range(
        "A1:B1",
        "Invoice Details",
        title_format,
    )

    invoice_sheet.set_column(
        "A:A",
        24,
    )

    invoice_sheet.set_column(
        "B:B",
        45,
    )

    invoice_sheet.write(
        2,
        0,
        "Field",
        header_format,
    )

    invoice_sheet.write(
        2,
        1,
        "Value",
        header_format,
    )

    row = 3

    for key, value in data[
        "invoice"
    ].items():

        display_name = (
            key.replace(
                "_",
                " ",
            )
            .title()
        )

        invoice_sheet.write(
            row,
            0,
            display_name,
            label_format,
        )

        if (
            key
            in {
                "subtotal",
                "tax_amount",
                "grand_total",
            }
            and value is not None
        ):

            invoice_sheet.write_number(
                row,
                1,
                float(value),
                money_format,
            )

        else:

            invoice_sheet.write(
                row,
                1,
                "" if value is None else value,
                value_format,
            )

        row += 1

    # ==================================
    # Sheet 2 — Line Items
    # ==================================

    items_sheet = workbook.add_worksheet(
        "Line Items"
    )

    item_headers = [
        "ID",
        "Description",
        "Quantity",
        "Unit Price",
        "Tax Rate %",
        "Tax Amount",
        "Line Total",
        "Confidence",
    ]

    for column, header in enumerate(
        item_headers
    ):

        items_sheet.write(
            0,
            column,
            header,
            header_format,
        )

    items_sheet.set_column(
        "A:A",
        8,
    )

    items_sheet.set_column(
        "B:B",
        45,
    )

    items_sheet.set_column(
        "C:H",
        15,
    )

    for row_index, item in enumerate(
        data["line_items"],
        start=1,
    ):

        items_sheet.write(
            row_index,
            0,
            item["id"],
            value_format,
        )

        items_sheet.write(
            row_index,
            1,
            item["description"] or "",
            wrap_format,
        )

        items_sheet.write(
            row_index,
            2,
            item["quantity"] or 0,
            value_format,
        )

        items_sheet.write(
            row_index,
            3,
            item["unit_price"] or 0,
            money_format,
        )

        items_sheet.write(
            row_index,
            4,
            item["tax_rate"] or 0,
            value_format,
        )

        items_sheet.write(
            row_index,
            5,
            item["tax_amount"] or 0,
            money_format,
        )

        items_sheet.write(
            row_index,
            6,
            item["line_total"] or 0,
            money_format,
        )

        confidence = (
            item["confidence"] or 0
        )

        items_sheet.write_number(
            row_index,
            7,
            confidence,
            percent_format,
        )

    # ==================================
    # Sheet 3 — Confidence
    # ==================================

    confidence_sheet = (
        workbook.add_worksheet(
            "Confidence Scores"
        )
    )

    confidence_headers = [
        "Field",
        "Extracted Value",
        "Confidence",
        "Source Text",
    ]

    for column, header in enumerate(
        confidence_headers
    ):

        confidence_sheet.write(
            0,
            column,
            header,
            header_format,
        )

    confidence_sheet.set_column(
        "A:A",
        22,
    )

    confidence_sheet.set_column(
        "B:B",
        30,
    )

    confidence_sheet.set_column(
        "C:C",
        15,
    )

    confidence_sheet.set_column(
        "D:D",
        70,
    )

    for row_index, score in enumerate(
        data["confidence_scores"],
        start=1,
    ):

        confidence_sheet.write(
            row_index,
            0,
            score["field_name"],
            value_format,
        )

        confidence_sheet.write(
            row_index,
            1,
            score["field_value"] or "",
            value_format,
        )

        confidence_sheet.write_number(
            row_index,
            2,
            score["confidence"],
            percent_format,
        )

        confidence_sheet.write(
            row_index,
            3,
            score["source_text"] or "",
            wrap_format,
        )

    # ==================================
    # Sheet 4 — Validation
    # ==================================

    validation_sheet = (
        workbook.add_worksheet(
            "Validation Results"
        )
    )

    validation_headers = [
        "Rule",
        "Status",
        "Message",
    ]

    for column, header in enumerate(
        validation_headers
    ):

        validation_sheet.write(
            0,
            column,
            header,
            header_format,
        )

    validation_sheet.set_column(
        "A:A",
        28,
    )

    validation_sheet.set_column(
        "B:B",
        15,
    )

    validation_sheet.set_column(
        "C:C",
        70,
    )

    for row_index, result in enumerate(
        data["validations"],
        start=1,
    ):

        validation_sheet.write(
            row_index,
            0,
            result["rule_name"],
            value_format,
        )

        validation_sheet.write(
            row_index,
            1,
            result["status"],
            value_format,
        )

        validation_sheet.write(
            row_index,
            2,
            result["message"] or "",
            wrap_format,
        )

    workbook.close()

    output.seek(0)

    return output.getvalue()