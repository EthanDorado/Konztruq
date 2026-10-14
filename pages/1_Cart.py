import streamlit as st
from html import escape

from services.cart_service import CartService


# ============================================================
# TEMPORARY TEST CUSTOMER
# ============================================================

# Same test customer as app.py.
# Later, this will come from the customer's login/account.
TEST_CUSTOMER_ID = "8166242c-f6e7-4e8d-8353-e88e16a8022b"


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="My Cart - Konztruq",
    page_icon="🛒",
    layout="wide"
)


# ============================================================
# KONZTRUQ COLORS
# ============================================================

CERULEAN_BLUE = "#007BA7"
ORANGE = "#F28C28"
NEAR_BLACK = "#111111"
LIGHT_BLUE = "#F4F9FB"
BORDER = "#D9E5EA"


# ============================================================
# PAGE STYLING
# ============================================================

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

        .main-title {{
            color: {CERULEAN_BLUE};
            font-size: 36px;
            font-weight: 700;
        }}

        .store-name {{
            color: {CERULEAN_BLUE};
            font-size: 22px;
            font-weight: 700;
        }}

        .item-name {{
            color: {NEAR_BLACK};
            font-size: 18px;
            font-weight: 700;
        }}

        .subtotal {{
            color: {NEAR_BLACK};
            font-weight: 600;
        }}

        .store-subtotal {{
            color: {NEAR_BLACK};
            font-size: 18px;
            font-weight: 700;
            text-align: right;
        }}

        .cart-total {{
            color: {ORANGE};
            font-size: 28px;
            font-weight: 700;
        }}

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HELPER
# ============================================================

def money(amount):
    """Formats a number as Philippine pesos."""
    return f"PHP {amount:,.2f}"


# ============================================================
# SERVICE
# ============================================================

cart_service = CartService()


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">My Cart</div>',
    unsafe_allow_html=True
)


# ============================================================
# LOAD THE CART
# ============================================================

try:
    cart = cart_service.get_or_create_cart(TEST_CUSTOMER_ID)
    cart_items = cart_service.get_cart_details(cart["cart_id"])

except Exception as error:
    st.error(f"Could not load your cart: {error}")
    st.stop()

if not cart_items:
    st.info("Your cart is empty.")
    st.page_link("pages/0_Materials.py", label="Go to Materials")
    st.stop()


# ============================================================
# STORE GROUPS
# ============================================================

store_groups = cart_service.group_by_store(cart_items)

if len(store_groups) > 1:
    st.caption(
        f"Your cart has items from {len(store_groups)} hardware stores. "
        f"Items are grouped by store."
    )

for group in store_groups:

    with st.container(border=True):

        st.markdown(
            f'<div class="store-name">🏪 {escape(group["store_name"])}</div>',
            unsafe_allow_html=True
        )

        if group["address"]:
            st.write(f"📍 {group['address']}")

        for item in group["items"]:

            st.divider()

            info_column, quantity_column, remove_column = st.columns(
                [4, 2, 1]
            )

            changed = False

            # ------------------------------------------------
            # PRODUCT, PRICE AND SUBTOTAL
            # ------------------------------------------------

            with info_column:

                st.markdown(
                    f'<div class="item-name">'
                    f'{escape(item["product_name"])}'
                    f'</div>',
                    unsafe_allow_html=True
                )

                st.write(
                    f"{money(item['price'])} × {item['quantity']} "
                    f"({item['unit']})"
                )

                st.markdown(
                    f'<div class="subtotal">'
                    f'Subtotal: {money(item["subtotal"])}'
                    f'</div>',
                    unsafe_allow_html=True
                )

                if item["problem"]:
                    st.warning(item["problem"])

            # ------------------------------------------------
            # CHANGE QUANTITY
            # ------------------------------------------------

            with quantity_column:

                # The current quantity is part of the key, so the
                # box always starts from the quantity in the database.
                # max_value must never be lower than the current value.
                max_quantity = max(item["stock_quantity"], item["quantity"])

                new_quantity = st.number_input(
                    "Quantity",
                    min_value=1,
                    max_value=max_quantity,
                    value=item["quantity"],
                    step=1,
                    key=f"qty_{item['cart_item_id']}_{item['quantity']}"
                )

            if new_quantity != item["quantity"]:

                try:
                    cart_service.update_quantity(
                        item["cart_item_id"],
                        new_quantity
                    )
                    changed = True

                except Exception as error:
                    st.error(f"Could not change quantity: {error}")

            # ------------------------------------------------
            # REMOVE
            # ------------------------------------------------

            with remove_column:

                # Small spacer so the button lines up with the box.
                st.write("")

                if st.button(
                    "Remove",
                    key=f"remove_{item['cart_item_id']}"
                ):

                    try:
                        cart_service.remove_item(item["cart_item_id"])
                        changed = True

                    except Exception as error:
                        st.error(f"Could not remove item: {error}")

            # Rerun AFTER the try/except so the page shows new values.
            if changed:
                st.rerun()

        st.divider()

        st.markdown(
            f'<div class="store-subtotal">'
            f'Store subtotal: {money(group["subtotal"])}'
            f'</div>',
            unsafe_allow_html=True
        )


# ============================================================
# CART TOTAL
# ============================================================

cart_total = cart_service.calculate_cart_total(cart_items)

st.markdown(
    f'<div class="cart-total">TOTAL: {money(cart_total)}</div>',
    unsafe_allow_html=True
)

st.page_link("pages/2_Checkout.py", label="Proceed to Checkout")