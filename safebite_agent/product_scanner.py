"""Image-to-label text extraction for review in the SafeBite app."""

import base64
import json
from io import BytesIO

from google import genai
from pydantic import BaseModel, ConfigDict, Field

from safebite_agent import config

MAX_IMAGE_BYTES = 10 * 1024 * 1024


class ProductScan(BaseModel):
    """Structured candidate text extracted from a product label image."""

    model_config = ConfigDict(extra="forbid")

    product_name: str = Field(description="Product name, or empty string when unreadable/absent")
    product_code: str = Field(
        description="Visible alphanumeric product or batch code, or empty string when absent"
    )
    ingredients_text_en: str = Field(
        description="English ingredient list copied as printed, empty if no English version exists"
    )
    ingredients_text_pt: str = Field(
        description="Portuguese ingredient list copied as printed, empty if no Portuguese version exists"
    )
    contains_text_en: str = Field(
        description="English contains/allergen statement copied as printed, or empty string"
    )
    contains_text_pt: str = Field(
        description="Portuguese contains/allergen statement copied as printed, or empty string"
    )
    may_contain_text_en: str = Field(
        description="English may-contain statement copied as printed, or empty string"
    )
    may_contain_text_pt: str = Field(
        description="Portuguese may-contain statement copied as printed, or empty string"
    )
    uncertain_fields: list[str] = Field(
        description="Fields that are blurry, cropped, partly hidden, or uncertain"
    )


class ProductScanError(RuntimeError):
    """User-safe image scanning failure."""


def _validate_image(image_bytes: bytes) -> str:
    """Validate actual image format, decodability, and safe, useful dimensions."""
    from PIL import Image, UnidentifiedImageError

    try:
        with Image.open(BytesIO(image_bytes)) as image:
            image_format = image.format
            width, height = image.size
            if image_format not in {"JPEG", "PNG"}:
                raise ProductScanError("Use a JPG, JPEG, or PNG photo of the label.")
            if width < 160 or height < 100:
                raise ProductScanError("The image is too small to read. Use a larger label photo.")
            if width * height > 20_000_000:
                raise ProductScanError("The image dimensions are too large. Upload a smaller photo.")
            image.verify()
    except ProductScanError:
        raise
    except (Image.DecompressionBombError, UnidentifiedImageError, OSError, ValueError):
        raise ProductScanError("The file is not a readable JPEG or PNG image.") from None
    return "image/jpeg" if image_format == "JPEG" else "image/png"


def extract_label_from_image(image_bytes: bytes) -> ProductScan:
    """Ask the configured Gemini model to transcribe a label image into reviewable fields."""
    if not image_bytes:
        raise ProductScanError("The selected image is empty.")
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise ProductScanError("The image is larger than 10 MB. Upload a smaller photo.")
    mime_type = _validate_image(image_bytes)
    if not config.GOOGLE_API_KEY:
        raise ProductScanError("Photo scanning needs GOOGLE_API_KEY in app settings.")

    prompt = """Read this food package label. Transcribe only text visibly printed on the package.
For each ingredient list and allergen statement, put the English wording in the *_en field and the
Portuguese wording in the *_pt field. Do not put Spanish or any other language in either field.
When both English and Portuguese are present, preserve both separately; the application will choose
English first and Portuguese only when no English wording exists. Never translate text. Do not infer
hidden or missing text and do not assess whether the food is safe. If a field or language version is
absent, return an empty string. Put blurry, cropped, obscured, or uncertain field names in
uncertain_fields. Capture a visible product name and any visible alphanumeric product/batch code.
This output will be shown to a person for review before use."""
    try:
        client = genai.Client(api_key=config.GOOGLE_API_KEY)
        interaction = client.interactions.create(
            model=config.MODEL,
            input=[
                {"type": "text", "text": prompt},
                {
                    "type": "image",
                    "data": base64.b64encode(image_bytes).decode("ascii"),
                    "mime_type": mime_type,
                },
            ],
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": ProductScan.model_json_schema(),
            },
        )
    except Exception as exc:  # Provider SDKs expose multiple transport exception types.
        raise ProductScanError(
            "Could not read the label image. Check the model API settings and retry."
        ) from exc
    output = (getattr(interaction, "output_text", None) or "").strip()
    if not output:
        raise ProductScanError("The image scan returned no text. Try a clearer, closer photo.")
    try:
        return ProductScan.model_validate_json(output)
    except ValueError:
        raise ProductScanError("The scan result could not be read. Try the photo again.") from None


