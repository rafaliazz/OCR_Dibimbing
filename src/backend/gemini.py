import os
import json
from dotenv import load_dotenv

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

MODEL_NAME = "gemini-2.5-flash"

SYSTEM_PROMPT = """
You extract only price-related information from OCR text of receipts.

Return VALID JSON ONLY.

Schema:

{
  "items": [
    {
      "name": string,
      "quantity": number,
      "price": number
    }
  ],
  "subtotal": number | null,
  "tax": number | null,
  "total": number | null
}

Rules:
- price = total price for that line item
- quantity defaults to 1 if missing
"""


def extract_prices(ocr_text: str):

    llm = ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        temperature=0,
        google_api_key=os.getenv("GEMINI_API_KEY"),
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=ocr_text),
    ]

    response = llm.invoke(messages)

    raw = response.content.strip()

    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    return json.loads(raw)
