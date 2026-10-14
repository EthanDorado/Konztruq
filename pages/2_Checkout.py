import streamlit as st
from html import escape

from services.cart_service import CartService
from services.order_service import OrderService
from services.delivery_service import DeliveryService


# ============================================================
# TEMPORARY TEST CUSTOMER
# ============================================================

# Same test customer as the other pages.
# Later, this will come from the customer's login/account.
TEST_CUSTOMER_ID = "8166242c-f6e7-4e8d-8353-e88e16a8022b"


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Checkout - Konztruq",
    page_icon="🧾",
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
# HELPER FUNCTIONS
# ============================================================

def money(amount):
    """Formats a number as Philippine pesos."""
    return f"PHP {amount:,.2f}"


def kg(value):
    """Formats a weight in kilograms."""
    return f"{value:,.1f} kg"


# ============================================================
# SERVICES
# ============================================================

cart_service = CartService()
order_service = OrderService()
delivery_service = DeliveryService()


def place_orders(store_groups, fulfillment_choices, receipt_name):
    """
    Creates one order for every hardware store group.

    For each store group:
        1. OrderService creates the order and its items.
        2. CartService removes that store's items from the cart.

    Only the groups that are passed in are ordered. Cart items that
    the customer did not select are not in these groups, so they stay
    in the cart.

    If one store fails, the other stores are still processed,
    and the failure is reported to the customer.

    Args:
        store_groups (list): Store groups made of the selected items.
        fulfillment_choices (dict): Maps each store key to
            'pickup' or 'delivery'.
        receipt_name (str): Name for the receipts.

    Returns:
        tuple: (created_orders, error_messages)
    """

    created_orders = []
    error_messages = []

    for group in store_groups:

        group_key = group["store_id"] or group["store_name"]
        fulfillment_type = fulfillment_choices[group_key]

        # Step 1: create the order.
        try:
            order = order_service.create_order(
                TEST_CUSTOMER_ID,
                receipt_name,
                fulfillment_type,
                group
            )

        except Exception as error:
            error_messages.append(f"{group['store_name']}: {error}")
            continue

        created_orders.append(order)

        # Step 2: remove ONLY this store's ordered items from the cart.
        try:
            for item in group["items"]:
                cart_service.remove_item(item["cart_item_id"])

        except Exception as error:
            error_messages.append(
                f"{group['store_name']}: the order was created, but "
                f"its items could not be removed from your cart. "
                f"Please remove them yourself so you do not order "
                f"twice. Details: {error}"
            )

    return created_orders, error_messages


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">Checkout</div>',
    unsafe_allow_html=True
)

st.page_link("pages/1_Cart.py", label="← Back to Cart")


# ============================================================
# LOAD THE CART AND THE VEHICLES
# ============================================================

try:
    cart = cart_service.get_or_create_cart(TEST_CUSTOMER_ID)
    cart_items = cart_service.get_cart_details(cart["cart_id"])

except Exception as error:
    st.error(f"Could not load your cart: {error}")
    st.stop()

if not cart_items:
    st.info("Your cart is empty. Add items before checking out.")
    st.page_link("pages/0_Materials.py", label="Go to Materials")
    st.page_link("pages/3_My_Orders.py", label="View My Orders")
    st.stop()

# The vehicles are needed to check whether delivery is possible.
try:
    vehicles = delivery_service.get_active_vehicle_types()

except Exception as error:
    st.error(f"Could not load the delivery vehicles: {error}")
    vehicles = []


# ============================================================
# RECEIPT NAME
# ============================================================

st.subheader("Receipt Name")

st.caption(
    "This is the name that will appear on your receipt. "
    "You may use your own name or a company name."
)

# The receipt name is kept in session_state so it is not lost
# when the page refreshes or the customer changes pages.
receipt_name = st.text_input(
    "Receipt Name",
    value=st.session_state.get("receipt_name", ""),
    placeholder="Example: Juan Dela Cruz  or  ABC Construction"
)

st.session_state.receipt_name = receipt_name.strip()


# ============================================================
# ORDER SUMMARY: CHOOSE ITEMS + PICKUP / DELIVERY (PER STORE)
# ============================================================

st.subheader("Order Summary")

st.caption(
    "Select the items you want to buy now. Items you leave unselected "
    "stay in your cart. Each hardware store gets its own order and "
    "its own receipt, and you choose Pickup or Delivery for each one."
)

store_groups = cart_service.group_by_store(cart_items)

# Items the customer selected (these are the ones that will be ordered).
selected_items = []

# Maps each store to the choice the customer made.
fulfillment_choices = {}

# Stores where the customer chose Delivery but it is not possible.
blocked_stores = []

CHOICE_LABELS = {
    "Pickup": OrderService.FULFILLMENT_PICKUP,
    "Delivery": OrderService.FULFILLMENT_DELIVERY
}

for group in store_groups:

    group_key = group["store_id"] or group["store_name"]

    # The selected items of THIS store.
    group_selected = []

    with st.container(border=True):

        st.markdown(
            f'<div class="store-name">🏪 {escape(group["store_name"])}</div>',
            unsafe_allow_html=True
        )

        if group["address"]:
            st.write(f"📍 {group['address']}")

        # ----------------------------------------------------
        # ITEMS WITH A SELECT BOX
        # ----------------------------------------------------

        for item in group["items"]:

            st.divider()

            select_column, info_column = st.columns([1, 6])

            with select_column:
                include = st.checkbox(
                    "Buy this",
                    value=True,
                    key=f"include_{item['cart_item_id']}"
                )

            with info_column:

                st.markdown(
                    f'<div class="item-name">'
                    f'{escape(item["product_name"])}'
                    f'</div>',
                    unsafe_allow_html=True
                )

                st.write(
                    f"{money(item['price'])} × {item['quantity']} "
                    f"({item['unit']})  =  **{money(item['subtotal'])}**"
                )

                if item["problem"]:
                    st.warning(item["problem"])

                if not include:
                    st.caption(
                        "Not included in this purchase. "
                        "It stays in your cart."
                    )

            if include:
                group_selected.append(item)

        st.divider()

        # A store with nothing selected gets no order and no choice.
        if not group_selected:
            st.caption("No items from this store are selected.")
            continue

        selected_subtotal = sum(item["subtotal"] for item in group_selected)

        st.markdown(
            f'<div class="store-subtotal">'
            f'Store subtotal: {money(selected_subtotal)}'
            f'</div>',
            unsafe_allow_html=True
        )

        selected_items.extend(group_selected)

        # ----------------------------------------------------
        # PICKUP OR DELIVERY FOR THIS STORE
        # ----------------------------------------------------

        selected_label = st.radio(
            "How do you want to receive this order?",
            list(CHOICE_LABELS.keys()),
            key=f"fulfillment_{group_key}",
            horizontal=True
        )

        fulfillment_choices[group_key] = CHOICE_LABELS[selected_label]

        if selected_label == "Pickup":

            if group["address"]:
                st.info(f"You will pick this order up at: {group['address']}")
            else:
                st.info("You will pick this order up at the store.")

        else:

            # Check NOW that one vehicle can carry these items, so the
            # customer never places a delivery order that cannot be booked.
            try:
                delivery_check = delivery_service.check_delivery_for_items(
                    group_selected,
                    vehicles
                )

            except Exception as error:
                delivery_check = {
                    "ok": False,
                    "total_weight": None,
                    "message": (
                        f"Could not check delivery for this store: {error}"
                    )
                }

            if delivery_check["ok"]:
                st.caption(
                    f"Weight of the selected items: "
                    f"{kg(delivery_check['total_weight'])}. After you place "
                    f"the order, you will choose a vehicle and the delivery "
                    f"location on a map."
                )
            else:
                st.error(delivery_check["message"])
                blocked_stores.append(group["store_name"])

# Only the selected items are ordered and counted.
selected_groups = cart_service.group_by_store(selected_items)

cart_total = cart_service.calculate_cart_total(selected_items)

st.markdown(
    f'<div class="cart-total">TOTAL (selected items): {money(cart_total)}</div>',
    unsafe_allow_html=True
)


# ============================================================
# READINESS CHECK + PLACE ORDER
# ============================================================

st.divider()

selected_problems = [item for item in selected_items if item["problem"]]

ready = (
    bool(selected_items)
    and not selected_problems
    and not blocked_stores
    and bool(st.session_state.receipt_name)
)

if not selected_items:
    st.warning("Select at least one item to buy.")

elif selected_problems:
    st.error(
        "Some selected items need attention. Deselect them, or go back "
        "to the cart and fix or remove them."
    )

elif blocked_stores:
    st.error(
        "Delivery is not possible for: " + ", ".join(blocked_stores)
        + ". Choose Pickup, lower the quantities, or deselect some items."
    )

elif not st.session_state.receipt_name:
    st.warning("Please enter a Receipt Name to continue.")

else:
    st.success(
        f"Order information is ready.\n\n"
        f"Receipt Name: **{st.session_state.receipt_name}**  |  "
        f"Hardware stores: **{len(selected_groups)}**  |  "
        f"Total: **{money(cart_total)}**"
    )
    st.caption(
        "Each order starts as Pending until the hardware store "
        "confirms it."
    )

place_order_clicked = st.button(
    "Place Order",
    type="primary",
    disabled=not ready
)

if place_order_clicked:

    created_orders, error_messages = place_orders(
        selected_groups,
        fulfillment_choices,
        st.session_state.receipt_name
    )

    for message in error_messages:
        st.error(message)

    if created_orders:

        # Remember which orders are new so My Orders can show them.
        st.session_state.last_order_ids = [
            order["order_id"] for order in created_orders
        ]

        # If any new order is a delivery order, the customer
        # still has to choose a vehicle and a delivery location.
        has_delivery_order = any(
            order["fulfillment_type"] == OrderService.FULFILLMENT_DELIVERY
            for order in created_orders
        )

        if error_messages:
            st.success(
                f"{len(created_orders)} order(s) were created. "
                f"Some stores had a problem (see above)."
            )
            st.page_link("pages/3_My_Orders.py", label="View My Orders")

            if has_delivery_order:
                st.page_link(
                    "pages/4_Book_Delivery.py",
                    label="Book delivery"
                )

        elif has_delivery_order:
            st.switch_page("pages/4_Book_Delivery.py")

        else:
            st.switch_page("pages/3_My_Orders.py")