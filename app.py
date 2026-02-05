import streamlit as st
from pathlib import Path
import json

from src.backend.donut import DonutOCR
from src.backend.gemini import extract_prices

# ------------------------
# Page config
# ------------------------

st.set_page_config(
    page_title="SplitBill AI",
    layout="wide",
)

st.title("💸 SplitBill AI")
st.caption("Upload a receipt → OCR → extract prices → split with friends")

# ------------------------
# Load models once
# ------------------------

@st.cache_resource
def load_models():
    donut = DonutOCR()
    return donut

donut = load_models()

# ------------------------
# Upload section
# ------------------------

st.header("Upload Receipt")

uploaded = st.file_uploader(
    "Upload receipt image",
    type=["png", "jpg", "jpeg"],
)

if uploaded:
    image_path = Path("temp_receipt.jpg")
    image_path.write_bytes(uploaded.read())

    st.image(image_path, caption="Uploaded receipt", use_container_width=True)

    if st.button("Process Receipt"):

        with st.spinner("Running OCR..."):
            out = donut.run(image_path)

        st.subheader("Raw OCR Output")
        st.json(out["parsed"])

        # Flatten Donut output → text
        ocr_text = json.dumps(out["parsed"], indent=2)

        with st.spinner("Extracting prices with Gemini..."):
            prices = extract_prices(ocr_text)

        st.subheader("Extracted Prices")
        st.json(prices)

        st.session_state["prices"] = prices


# ------------------------
# Split Bill Section
# ------------------------

if "prices" in st.session_state:

    st.header("Split")

    prices = st.session_state["prices"]

    items = prices.get("items", [])

    if not items:
        st.warning("No items detected.")
    else:

        # Add people
        st.subheader("Add People")

        people = st.text_input(
            "Input names (comma separated)",
            "Alice,Bob,Charlie",
        )

        people = [p.strip() for p in people.split(",") if p.strip()]

        st.write("People:", people)

        # ------------------
        # Assign items
        # ------------------

        st.subheader("Assign Items")

        assignments = {}

        for i, item in enumerate(items):

            col1, col2 = st.columns([2, 3])

            with col1:
                st.write(
                    f"**{item['name']}** — ${item['price']}"
                )

            with col2:
                chosen = st.multiselect(
                    f"Who had this?",
                    people,
                    key=f"item_{i}",
                )

                assignments[i] = chosen

    if st.button("Calculate Split"):

        totals = {p: 0.0 for p in people}
        pretax = {p: 0.0 for p in people}

        for idx, chosen in assignments.items():

            if not chosen:
                continue

            item = items[idx]
            share = float(item["price"]) / len(chosen)

            for person in chosen:
                pretax[person] += share

        subtotal = prices.get("subtotal")
        tax = prices.get("tax")

        if tax and subtotal:

            ratio = tax / subtotal

            for p in pretax:
                totals[p] = pretax[p] * (1 + ratio)

        else:
            totals = pretax.copy()

        st.subheader("Who Pays What")

        for person in totals:
            st.metric(
                person,
                f"${totals[person]:.2f}",
                help=f"Pretax: ${pretax[person]:.2f}",
            )

        st.subheader("Receipt Totals")

        st.write("Subtotal:", subtotal)
        st.write("Tax:", tax)
        st.write("Total:", prices.get("total"))
