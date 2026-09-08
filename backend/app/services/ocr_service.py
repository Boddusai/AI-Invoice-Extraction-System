import os
import shutil
from pathlib import Path

import cv2
import numpy as np
import pymupdf
import pytesseract


def configure_tesseract():
    """
    Configure Tesseract OCR for:

    1. Environment variable
    2. Linux / Docker / Render
    3. Local Windows development
    """

    # ---------------------------------
    # 1. Environment variable
    # ---------------------------------

    env_path = os.getenv(
        "TESSERACT_CMD"
    )

    if env_path:
        pytesseract.pytesseract.tesseract_cmd = (
            env_path
        )

        return


    # ---------------------------------
    # 2. Search system PATH
    #
    # Linux / Docker usually finds:
    # /usr/bin/tesseract
    # ---------------------------------

    system_path = shutil.which(
        "tesseract"
    )

    if system_path:

        pytesseract.pytesseract.tesseract_cmd = (
            system_path
        )

        return


    # ---------------------------------
    # 3. Windows fallback
    # ---------------------------------

    windows_path = Path(
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )

    if windows_path.exists():

        pytesseract.pytesseract.tesseract_cmd = (
            str(windows_path)
        )

        return


    # ---------------------------------
    # Not found
    # ---------------------------------

    raise RuntimeError(
        "Tesseract OCR executable was not found. "
        "Install Tesseract or set TESSERACT_CMD."
    )


# Configure Tesseract when this module loads
configure_tesseract()


def preprocess_image(
    image: np.ndarray
) -> np.ndarray:
    """
    Improve invoice image quality before OCR.
    """

    if image is None:

        raise ValueError(
            "Invalid image."
        )


    # ---------------------------------
    # Convert to grayscale
    # ---------------------------------

    if len(image.shape) == 3:

        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY
        )

    else:

        gray = image


    # ---------------------------------
    # Enlarge image
    # ---------------------------------

    gray = cv2.resize(
        gray,
        None,
        fx=2,
        fy=2,
        interpolation=cv2.INTER_CUBIC
    )


    # ---------------------------------
    # Reduce noise
    # ---------------------------------

    gray = cv2.GaussianBlur(
        gray,
        (3, 3),
        0
    )


    # ---------------------------------
    # Black / white threshold
    # ---------------------------------

    processed = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY
        + cv2.THRESH_OTSU
    )[1]


    return processed


def run_tesseract(
    image: np.ndarray
) -> str:
    """
    Run OCR on a processed image.
    """

    processed_image = (
        preprocess_image(
            image
        )
    )


    text = pytesseract.image_to_string(
        processed_image,
        config="--oem 3 --psm 6"
    )


    return text.strip()


def extract_text_from_image(
    file_path: str
) -> dict:
    """
    Extract text from JPG, JPEG or PNG invoice.
    """

    path = Path(
        file_path
    )


    if not path.exists():

        raise FileNotFoundError(
            f"Invoice image not found: {file_path}"
        )


    image = cv2.imread(
        str(path)
    )


    if image is None:

        raise ValueError(
            "Unable to read invoice image."
        )


    text = run_tesseract(
        image
    )


    return {
        "text": text,
        "page_count": 1,
        "characters_extracted": len(
            text
        ),
    }


def extract_text_from_scanned_pdf(
    file_path: str
) -> dict:
    """
    Convert scanned PDF pages to images
    and run OCR on every page.
    """

    path = Path(
        file_path
    )


    if not path.exists():

        raise FileNotFoundError(
            f"PDF not found: {file_path}"
        )


    document = pymupdf.open(
        str(path)
    )


    extracted_pages = []


    try:

        for page_number, page in enumerate(
            document,
            start=1
        ):

            # ---------------------------------
            # Render PDF page at higher quality
            # ---------------------------------

            matrix = pymupdf.Matrix(
                2.5,
                2.5
            )


            pix = page.get_pixmap(
                matrix=matrix,
                alpha=False
            )


            # ---------------------------------
            # Convert rendered page to PNG
            # ---------------------------------

            image_bytes = pix.tobytes(
                "png"
            )


            image_array = np.frombuffer(
                image_bytes,
                dtype=np.uint8
            )


            image = cv2.imdecode(
                image_array,
                cv2.IMREAD_COLOR
            )


            if image is None:

                continue


            # ---------------------------------
            # OCR page
            # ---------------------------------

            page_text = run_tesseract(
                image
            )


            if page_text:

                extracted_pages.append(
                    f"--- Page {page_number} ---\n"
                    f"{page_text}"
                )


        text = "\n\n".join(
            extracted_pages
        ).strip()


        return {
            "text": text,
            "page_count": len(
                document
            ),
            "characters_extracted": len(
                text
            ),
        }


    finally:

        document.close()


def extract_text_with_ocr(
    file_path: str
) -> dict:
    """
    Automatically select OCR method
    based on invoice file type.
    """

    extension = Path(
        file_path
    ).suffix.lower()


    if extension == ".pdf":

        return (
            extract_text_from_scanned_pdf(
                file_path
            )
        )


    if extension in {
        ".jpg",
        ".jpeg",
        ".png",
    }:

        return (
            extract_text_from_image(
                file_path
            )
        )


    raise ValueError(
        "Unsupported OCR file type. "
        "Only PDF, JPG, JPEG and PNG are supported."
    )