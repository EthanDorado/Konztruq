import streamlit as st
from html import escape

from services.marketplace_service import MarketplaceService
from services.cart_service import CartService


# ============================================================
# TEMPORARY TEST CUSTOMER
# ============================================================

# for testing only
TEST_CUSTOMER_ID = "8166242c-f6e7-4e8d-8353-e88e16a8022b"


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Konztruq Marketplace",
    page_icon="🏗️",
    layout="wide"
)


# ============================================================
# KONZTRUQ COLORS
# ============================================================

CERULEAN_BLUE = "#007BA7"
ORANGE = "#F28C28"
NEAR_BLACK = "#111111"
LIGHT_BLUE = "#F4F9FB"
RED = "#C0392B"
LIGHT_RED = "#FDECEC"
BORDER = "#D9E5EA"


# ============================================================
# PAGE STYLING
# ============================================================

# NOTE: Cards are drawn with st.container(border=True).
# The CSS below styles those containers. A container that
# holds an ".oos-marker" element is an out-of-stock card
# and is styled red.

st.markdown(
    f"""
    <style>

        .stApp {{
            background-color: {LIGHT_BLUE};
            color: {NEAR_BLACK};
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background-color: white !important;
            border: 1px solid {BORDER} !important;
            border-radius: 14px !important;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.oos-marker) {{
            background-color: {LIGHT_RED} !important;
            border: 2px solid {RED} !important;
        }}

        .oos-marker {{
            display: none;
        }}

        .main-title {{
            color: {CERULEAN_BLUE};
            font-size: 36px;
            font-weight: 700;
        }}

        .product-name {{
            color: {NEAR_BLACK};
            font-size: 22px;
            font-weight: 700;
        }}

        .store-name {{
            color: {NEAR_BLACK};
            font-size: 20px;
            font-weight: 700;
        }}

        .cheapest {{
            color: {ORANGE};
            font-weight: 700;
            font-size: 14px;
        }}

        .out-of-stock {{
            color: {RED};
            font-weight: 700;
        }}

        .price-box {{
            background-color: white;
            border: 2px solid {CERULEAN_BLUE};
            border-radius: 10px;
            padding: 14px;
            margin-top: 12px;
            margin-bottom: 12px;
        }}

        .out-of-stock-price-box {{
            background-color: white;
            border: 2px solid {RED};
            border-radius: 10px;
            padding: 14px;
            margin-top: 12px;
            margin-bottom: 12px;
        }}

        .price-label {{
            font-size: 13px;
            color: #555555;
        }}

        .price-value {{
            font-size: 24px;
            font-weight: 700;
            color: {NEAR_BLACK};
        }}

        .estimated-total {{
            font-size: 18px;
            font-weight: 600;
            color: {NEAR_BLACK};
        }}

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SERVICES
# ============================================================

marketplace = MarketplaceService()
cart_service = CartService()


# ============================================================
# SESSION STATE
# ============================================================

# selected_product stores the product the customer currently
# wants to compare between hardware stores.
if "selected_product" not in st.session_state:
    st.session_state.selected_product = None


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clear_selected_product():
    """Goes back to the product list."""
    st.session_state.selected_product = None


def sort_listings(listings, sort_option):
    """
    Sorts store listings based on the option chosen by the customer.

    Out-of-stock listings are kept in the list.
    Only the order changes.
    """

    if sort_option == "Price: Low to High":
        return sorted(listings, key=lambda l: float(l["price"]))

    if sort_option == "Price: High to Low":
        return sorted(
            listings,
            key=lambda l: float(l["price"]),
            reverse=True
        )

    if sort_option == "Stock: High to Low":
        return sorted(
            listings,
            key=lambda l: l["stock_quantity"],
            reverse=True
        )

    if sort_option == "Stock: Low to High":
        return sorted(listings, key=lambda l: l["stock_quantity"])

    # "Relevance" currently means the default database ordering.
    return listings


def find_cheapest_price(listings):
    """
    Finds the lowest price among listings that are in stock.

    This is ONLY used to show the "cheapest" label.
    It never selects a store or adds anything to the cart.

    Returns:
        float or None: Lowest in-stock price, or None if every
        listing is out of stock.
    """

    prices = [
        float(listing["price"])
        for listing in listings
        if listing["stock_quantity"] > 0
    ]

    if not prices:
        return None

    return min(prices)


# ============================================================
# PRODUCT LIST
# ============================================================

def show_product_card(product):
    """Shows one product (not one store listing) in the results."""

    product_id = product["product_id"]
    store_count = marketplace.get_store_count(product_id)

    with st.container(border=True):

        st.markdown(
            f'<div class="product-name">'
            f'{escape(product["product_name"])}'
            f'</div>',
            unsafe_allow_html=True
        )

        if product.get("description"):
            st.write(product["description"])

        st.write(
            f"Category: {product.get('category', 'N/A')}  |  "
            f"Unit: {product.get('unit', 'N/A')}  |  "
            f"Weight: {product.get('weight_kg', 0)} kg"
        )

        st.write(f"**{store_count} store(s) offer this product.**")

        if st.button("View Store Offers", key=f"view_{product_id}"):
            st.session_state.selected_product = product
            st.rerun()


def show_product_list(search_term):
    """Searches (or lists) products and shows a card for each."""

    if search_term.strip():
        products = marketplace.search_products(search_term.strip())
    else:
        products = marketplace.get_products()

    if not products:
        st.info("No products found.")
        return

    st.subheader("Products")

    for product in products:
        show_product_card(product)


# ============================================================
# STORE OFFERS
# ============================================================

def add_listing_to_cart(listing_id, quantity, store_name):
    """
    Adds ONE selected store listing to the customer's cart.

    The database work is done by CartService.
    This function only calls it and shows the result.
    """

    try:
        cart = cart_service.get_or_create_cart(TEST_CUSTOMER_ID)

        cart_service.add_item(
            cart_id=cart["cart_id"],
            listing_id=listing_id,
            quantity=quantity
        )

        st.success(
            f"Added {quantity} item(s) from {store_name} to your cart."
        )

    except Exception as error:
        st.error(f"Could not add item to cart: {error}")


def show_store_card(product, listing, cheapest_price):
    """
    Shows ONE hardware store's offer for the selected product.

    Every variable here (price, stock, listing_id, ...) belongs to
    the single listing passed in. Each card has its own quantity
    control and its own Add to Cart button.
    """

    store = listing["hardware_stores"]
    store_name = escape(store["store_name"])
    address = escape(store.get("address") or "Branch location unavailable")

    price = float(listing["price"])
    stock = int(listing["stock_quantity"])
    listing_id = listing["listing_id"]
    unit = escape(product.get("unit") or "unit")

    is_out_of_stock = stock <= 0
    is_cheapest = (
        not is_out_of_stock
        and cheapest_price is not None
        and price == cheapest_price
    )

    with st.container(border=True):

        # --------------------------------------------------
        # OUT OF STOCK CARD
        # --------------------------------------------------

        if is_out_of_stock:

            # The marker lets the CSS style this card red.
            st.markdown(
                '<span class="oos-marker"></span>',
                unsafe_allow_html=True
            )

            st.markdown(
                f'<div class="store-name">{store_name}</div>',
                unsafe_allow_html=True
            )

            st.write(f"📍 {address}")

            st.markdown(
                '<div class="out-of-stock">OUT OF STOCK (Stock: 0)</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                f'<div class="out-of-stock-price-box">'
                f'<div class="price-label">Price per unit</div>'
                f'<div class="price-value">PHP {price:,.2f} / {unit}</div>'
                f'<div class="price-label">Price shown for comparison only</div>'
                f'</div>',
                unsafe_allow_html=True
            )

            st.number_input(
                "Quantity",
                min_value=1,
                value=1,
                step=1,
                disabled=True,
                key=f"quantity_oos_{listing_id}"
            )

            st.button(
                "Add to Cart",
                disabled=True,
                key=f"add_oos_{listing_id}"
            )

            return

        # --------------------------------------------------
        # AVAILABLE STORE CARD
        # --------------------------------------------------

        st.markdown(
            f'<div class="store-name">{store_name}</div>',
            unsafe_allow_html=True
        )

        st.write(f"📍 {address}")

        st.write(f"Stock available: **{stock}**")

        if is_cheapest:
            st.markdown(
                '<div class="cheapest">CHEAPEST AVAILABLE PRICE</div>',
                unsafe_allow_html=True
            )

        # The quantity widget is drawn AFTER the price box, so we
        # read its current value from session state to calculate
        # the estimated total.
        quantity_key = f"quantity_{listing_id}"

        selected_quantity = st.session_state.get(quantity_key, 1)
        selected_quantity = max(1, min(int(selected_quantity), stock))

        estimated_total = price * selected_quantity

        st.markdown(
            f'<div class="price-box">'
            f'<div class="price-label">Price per unit</div>'
            f'<div style="display: flex; justify-content: space-between; '
            f'align-items: center;">'
            f'<div class="price-value">PHP {price:,.2f} / {unit}</div>'
            f'<div class="estimated-total">'
            f'Estimated total: PHP {estimated_total:,.2f}'
            f'</div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        quantity_column, cart_column = st.columns([1, 1])

        with quantity_column:
            quantity = st.number_input(
                "Quantity",
                min_value=1,
                max_value=stock,
                value=1,
                step=1,
                key=quantity_key
            )

        with cart_column:
            # Spacer so the button lines up with the quantity box.
            st.write("")

            if st.button("Add to Cart", key=f"add_{listing_id}"):
                add_listing_to_cart(
                    listing_id,
                    quantity,
                    store["store_name"]
                )


def show_store_offers(product):
    """Shows every store listing for the selected product."""

    product_id = product["product_id"]

    st.button(
        "← Back to Products",
        key="back_to_products",
        on_click=clear_selected_product
    )

    st.markdown(
        f'<div class="product-name">{escape(product["product_name"])}</div>',
        unsafe_allow_html=True
    )

    if product.get("description"):
        st.write(product["description"])

    store_count = marketplace.get_store_count(product_id)

    st.write(f"**{store_count} store(s) offer this product.**")

    st.divider()

    left_column, right_column = st.columns([3, 1])

    with left_column:
        st.subheader("Store Offers")
        st.caption("Choose the hardware store you want to buy from.")

    with right_column:
        sort_option = st.selectbox(
            "Sort Offers",
            [
                "Relevance",
                "Price: Low to High",
                "Price: High to Low",
                "Stock: High to Low",
                "Stock: Low to High"
            ],
            key=f"sort_{product_id}"
        )

    listings = marketplace.get_product_listings(product_id)

    if not listings:
        st.warning("No store has listed this product.")
        return

    listings = sort_listings(listings, sort_option)
    cheapest_price = find_cheapest_price(listings)

    for listing in listings:
        show_store_card(product, listing, cheapest_price)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">Konztruq Marketplace</div>',
    unsafe_allow_html=True
)

st.write(
    "Search construction materials and compare prices "
    "from different hardware stores."
)


# ============================================================
# PRODUCT SEARCH
# ============================================================

search_term = st.text_input(
    "Search construction materials",
    placeholder="Example: cement, paint, rebar, hammer..."
)


# ============================================================
# MAIN FLOW
# ============================================================

if st.session_state.selected_product is None:
    show_product_list(search_term)
else:
    show_store_offers(st.session_state.selected_product)