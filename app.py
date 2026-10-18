
import streamlit as st

# Configure the whole application once.
st.set_page_config(
    page_title="Konztruq",
    layout="wide",
)

# Register all customer-facing screens.
pages = {
    "Marketplace": [
        st.Page(
            "views/hardware_view.py",
            title="Hardware Stores",
            default=True,
        ),
        st.Page(
            "views/materials_view.py",
            title="Materials",
        ),
    ],
    "Shopping": [
        st.Page(
            "views/cart_view.py",
            title="Cart",
        ),
        st.Page(
            "views/checkout_view.py",
            title="Checkout",
        ),
        st.Page(
            "views/orders_view.py",
            title="My Orders",
        ),
    ],
    "Delivery": [
        st.Page(
            "views/delivery_view.py",
            title="Book Delivery",
        ),
    ],
}

# Show the sidebar and run only the selected page.
selected_page = st.navigation(pages)
selected_page.run()