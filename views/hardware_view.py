import streamlit as st
from html import escape

from models.hardware_store import HardwareStore
from controllers.cart_controller import CartService
from controllers.store_controller import StoreService


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
    page_title="Hardware Stores - Konztruq",
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
# A container that holds an ".oos-marker" element is a sold-out
# material card and is styled red.

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

        .store-name {{
            color: {CERULEAN_BLUE};
            font-size: 24px;
            font-weight: 700;
        }}

        .rating {{
            color: {ORANGE};
            font-size: 18px;
            font-weight: 700;
        }}

        .material-name {{
            color: {NEAR_BLACK};
            font-size: 20px;
            font-weight: 700;
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
# HELPER FUNCTIONS
# ============================================================

def money(amount):
    """Formats a number as Philippine pesos."""
    return f"PHP {amount:,.2f}"


# ============================================================
# SERVICES
# ============================================================

store_controller = StoreService()
cart_controller = CartService()


# ============================================================
# SESSION STATE
# ============================================================

# hw_selected: the main store (hardware) the customer opened.
# hw_location: the exact store location (main or branch) whose
#              materials are shown.
if "hw_selected" not in st.session_state:
    st.session_state.hw_selected = None

if "hw_location" not in st.session_state:
    st.session_state.hw_location = None


def open_hardware(store_id, has_branches):
    """
    Opens a hardware.

    A hardware with branches first asks the customer to choose a
    branch. A hardware with one location goes straight to its profile.
    """
    st.session_state.hw_selected = store_id
    st.session_state.hw_location = None if has_branches else store_id


def open_location(store_id):
    """Opens the profile of one chosen branch."""
    st.session_state.hw_location = store_id


def back_to_branches():
    """Goes back to the branch chooser."""
    st.session_state.hw_location = None


def back_to_directory():
    """Goes back to the list of hardware stores."""
    st.session_state.hw_selected = None
    st.session_state.hw_location = None


# ============================================================
# ADD TO CART
# ============================================================

def add_listing_to_cart(listing_id, quantity, store_name):
    """
    Adds ONE material of this store to the customer's cart.

    The database work is done by CartService.
    This function only calls it and shows the result.
    """

    try:
        cart = cart_controller.get_or_create_cart(TEST_CUSTOMER_ID)

        cart_controller.add_item(
            cart_id=cart["cart_id"],
            listing_id=listing_id,
            quantity=quantity
        )

        st.success(
            f"Added {quantity} item(s) from {store_name} to your cart."
        )

    except Exception as error:
        st.error(f"Could not add item to cart: {error}")


# ============================================================
# VIEW 1: DIRECTORY OF HARDWARE STORES
# ============================================================

def show_directory(directory):
    """
    Shows one box for every hardware.

    Each box already shows the rating, address, phone numbers, and
    branches, so the customer sees them before opening the hardware.
    """

    st.markdown(
        '<div class="main-title">Hardware Stores</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Browse hardware stores, check their ratings and contact "
        "details, and see what materials each one sells."
    )

    if not directory:
        st.info("No hardware stores found.")
        return

    columns = st.columns(2)

    for index, hardware in enumerate(directory):

        main = hardware["main"]
        branches = hardware["branches"]

        rating_text = HardwareStore.format_rating(hardware["average_rating"])

        if branches and hardware["average_rating"] is not None:
            rating_text += (
                f"  (average of {len(hardware['locations'])} locations)"
            )

        with columns[index % 2]:

            with st.container(border=True):

                st.markdown(
                    f'<div class="store-name">{escape(main.store_name)}</div>',
                    unsafe_allow_html=True
                )

                st.markdown(
                    f'<div class="rating">{escape(rating_text)}</div>',
                    unsafe_allow_html=True
                )

                st.write(f"📍 {main.address}")

                for line in main.get_contact_lines():
                    st.write(line)

                if branches:
                    st.write(
                        "🏬 **Branches:** "
                        + ", ".join(b.get_branch_label() for b in branches)
                    )
                else:
                    st.caption("Single location - no other branches")

                st.button(
                    "View this hardware",
                    key=f"open_{main.store_id}",
                    on_click=open_hardware,
                    args=(main.store_id, bool(branches))
                )


# ============================================================
# VIEW 2: CHOOSE A BRANCH
# ============================================================

def show_branch_chooser(hardware):
    """
    Shows every location of a hardware that has branches, so the
    customer can choose the one to buy from.

    Each location shows its own address, phone numbers, and rating.
    """

    main = hardware["main"]

    st.button(
        "← All hardware stores",
        key="back_directory_from_branches",
        on_click=back_to_directory
    )

    st.markdown(
        f'<div class="store-name">{escape(main.store_name)}</div>',
        unsafe_allow_html=True
    )

    st.write(
        f"This hardware has {len(hardware['branches'])} branch(es). "
        f"Choose the branch you want to buy from."
    )

    for location in hardware["locations"]:

        with st.container(border=True):

            st.markdown(
                f'<div class="material-name">'
                f'{escape(location.get_branch_label())}'
                f'</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                f'<div class="rating">{escape(location.get_rating_text())}</div>',
                unsafe_allow_html=True
            )

            st.write(f"📍 {location.address}")

            for line in location.get_contact_lines():
                st.write(line)

            st.button(
                "Choose this branch",
                key=f"branch_{location.store_id}",
                on_click=open_location,
                args=(location.store_id,)
            )


# ============================================================
# VIEW 3: STORE PROFILE WITH ITS OWN MATERIALS
# ============================================================

def show_material_card(material, store_name):
    """
    Shows ONE material of the opened store.

    A sold-out material is still shown, in red, with its price and
    with disabled controls. Konztruq is also a price-checking
    application.
    """

    listing_id = material["listing_id"]

    price = material["price"]
    stock = material["stock"]
    unit = escape(material["unit"] or "unit")

    if material["weight_kg"] is not None:
        weight_text = f"{material['weight_kg']:,.1f} kg"
    else:
        weight_text = "not set"

    is_out_of_stock = stock <= 0

    with st.container(border=True):

        # The marker lets the CSS style a sold-out card red.
        if is_out_of_stock:
            st.markdown(
                '<span class="oos-marker"></span>',
                unsafe_allow_html=True
            )

        st.markdown(
            f'<div class="material-name">'
            f'{escape(material["product_name"])}'
            f'</div>',
            unsafe_allow_html=True
        )

        if material["description"]:
            st.write(material["description"])

        st.write(
            f"Category: {material['category'] or 'N/A'}  |  "
            f"Unit: {material['unit'] or 'N/A'}  |  "
            f"Weight: {weight_text}"
        )

        # --------------------------------------------------
        # SOLD OUT
        # --------------------------------------------------

        if is_out_of_stock:

            st.markdown(
                '<div class="out-of-stock">OUT OF STOCK (Stock: 0)</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                f'<div class="out-of-stock-price-box">'
                f'<div class="price-label">Price per unit</div>'
                f'<div class="price-value">{money(price)} / {unit}</div>'
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
                key=f"store_qty_oos_{listing_id}"
            )

            st.button(
                "Add to Cart",
                disabled=True,
                key=f"store_add_oos_{listing_id}"
            )

            return

        # --------------------------------------------------
        # AVAILABLE
        # --------------------------------------------------

        st.write(f"Stock available: **{stock}**")

        # The quantity box is drawn AFTER the price box, so its
        # current value is read from session state.
        quantity_key = f"store_qty_{listing_id}"

        selected_quantity = st.session_state.get(quantity_key, 1)
        selected_quantity = max(1, min(int(selected_quantity), stock))

        estimated_total = price * selected_quantity

        st.markdown(
            f'<div class="price-box">'
            f'<div class="price-label">Price per unit</div>'
            f'<div style="display: flex; justify-content: space-between; '
            f'align-items: center;">'
            f'<div class="price-value">{money(price)} / {unit}</div>'
            f'<div class="estimated-total">'
            f'Estimated total: {money(estimated_total)}'
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

            if st.button("Add to Cart", key=f"store_add_{listing_id}"):
                add_listing_to_cart(listing_id, quantity, store_name)


def show_store_profile(hardware, location):
    """
    Shows the profile of ONE store location: its rating, address,
    phone numbers, and only its own materials.
    """

    has_branches = bool(hardware["branches"])

    if has_branches:
        st.button(
            "← Choose another branch",
            key="back_to_branches",
            on_click=back_to_branches
        )

    st.button(
        "← All hardware stores",
        key="back_directory_from_profile",
        on_click=back_to_directory
    )

    # ----------------------------------------------------
    # PROFILE HEADER
    # ----------------------------------------------------

    with st.container(border=True):

        st.markdown(
            f'<div class="store-name">{escape(location.store_name)}</div>',
            unsafe_allow_html=True
        )

        if has_branches:
            st.caption(f"Branch: {location.get_branch_label()}")

        st.markdown(
            f'<div class="rating">{escape(location.get_rating_text())}</div>',
            unsafe_allow_html=True
        )

        st.write(f"📍 {location.address}")

        for line in location.get_contact_lines():
            st.write(line)

    st.page_link("views/cart_view.py", label="Go to my cart")

    # ----------------------------------------------------
    # THIS STORE'S MATERIALS
    # ----------------------------------------------------

    st.subheader("Materials")

    search_text = st.text_input(
        "Search this store's materials",
        placeholder="Example: cement, paint, rebar...",
        key=f"store_search_{location.store_id}"
    )

    try:
        materials = store_controller.get_store_products(
            location.store_id,
            search_text
        )

    except Exception as error:
        st.error(f"Could not load the materials: {error}")
        return

    if not materials:

        if search_text.strip():
            st.info("No materials match your search.")
        else:
            st.info("This store has not listed any materials yet.")

        return

    st.caption(f"{len(materials)} material(s)")

    for material in materials:
        show_material_card(material, location.store_name)


# ============================================================
# MAIN FLOW
# ============================================================

try:
    directory = store_controller.get_hardware_directory()

except Exception as error:
    st.error(f"Could not load the hardware stores: {error}")
    st.stop()

hardware_by_id = {
    hardware["main"].store_id: hardware
    for hardware in directory
}

selected_hardware = hardware_by_id.get(st.session_state.hw_selected)

if selected_hardware is None:

    show_directory(directory)

else:

    selected_location = next(
        (
            location
            for location in selected_hardware["locations"]
            if location.store_id == st.session_state.hw_location
        ),
        None
    )

    if selected_location is None:
        show_branch_chooser(selected_hardware)
    else:
        show_store_profile(selected_hardware, selected_location)