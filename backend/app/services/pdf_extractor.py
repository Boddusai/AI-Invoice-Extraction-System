from pathlib import Path

import pymupdf


def extract_text_from_pdf(file_path: str) -> dict:
    """
    Extract text from a digital PDF using PyMuPDF.

    Returns:
        {
            "text": "...",
            "page_count": 2,
            "characters_extracted": 1500
        }
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"PDF file not found: {file_path}"
        )

    if path.suffix.lower() != ".pdf":
        raise ValueError(
            "Text extraction currently supports PDF files only."
        )

    extracted_pages = []

    try:
        document = pymupdf.open(str(path))

        page_count = len(document)

        for page_number, page in enumerate(
            document,
            start=1,
        ):
            page_text = page.get_text("text")

            if page_text:
                extracted_pages.append(
                    f"\n--- Page {page_number} ---\n"
                    f"{page_text.strip()}"
                )

        document.close()

        full_text = "\n".join(
            extracted_pages
        ).strip()

        return {
            "text": full_text,
            "page_count": page_count,
            "characters_extracted": len(full_text),
        }

    except Exception as error:
        raise RuntimeError(
            "Unable to read this PDF. "
            "The file may be corrupted, encrypted, "
            f"or unsupported. Details: {error}"
        )