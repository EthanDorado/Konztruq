import streamlit as st
import folium
from streamlit_folium import st_folium
from html import escape

from models.location import Location
from services.order_service import OrderService
from services.delivery_service import DeliveryService
from services.location_service import LocationService


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
    page_title="Book Delivery - Konztruq",
    page_icon="🚚",
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

        .order-ref {{
            color: #555555;
            font-size: 14px;
        }}

        .weight-total {{
            color: {ORANGE};
            font-size: 20px;
            font-weight: 700;
        }}

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def kg(value):
    """Formats a weight in kilograms."""
    return f"{value:,.1f} kg"


# ============================================================
# SERVICES
# ============================================================

order_service = OrderService()
delivery_service = DeliveryService()
location_service = LocationService()


def show_map(center, zoom, pin, key):
    """
    Draws the interactive map and returns what the customer did on it.

    The map is OpenStreetMap, drawn with folium. When the customer
    clicks the map, 'last_clicked' holds the clicked position.

    Args:
        center (tuple): (latitude, longitude) the map is centered on.
        zoom (int): How far the map is zoomed in.
        pin (Location or None): The pin to show, if one was placed.
        key (str): Unique key of this map component.

    Returns:
        dict or None: Information returned by the map component.
    """

    folium_map = folium.Map(location=list(center), zoom_start=zoom)

    if pin is not None:
        folium.Marker(
            [pin.latitude, pin.longitude],
            tooltip="Delivery location",
            icon=folium.Icon(color="darkblue")
        ).add_to(folium_map)

    # Newer versions of streamlit-folium can fill the page width.
    # Older versions need a fixed width.
    try:
        return st_folium(
            folium_map,
            height=420,
            use_container_width=True,
            returned_objects=["last_clicked"],
            key=key
        )

    except TypeError:
        return st_folium(
            folium_map,
            height=420,
            width=800,
            returned_objects=["last_clicked"],
            key=key
        )


def show_booking_card(order, vehicles):
    """
    Shows the booking form for ONE delivery order.

    The customer sees the weight of the order, the vehicles that can
    carry it, and chooses the delivery location on a map. The booking
    itself is saved by DeliveryService.

    Args:
        order (dict): One order from OrderService.
        vehicles (list): All active VehicleType objects.
    """

    order_id = order["order_id"]
    order_ref = str(order_id)[:8].upper()

    try:
        materials = delivery_service.get_order_materials(order_id)

    except Exception as error:
        st.error(f"Could not load the order materials: {error}")
        return

    total_weight = delivery_service.calculate_total_weight(materials)

    booked = False

    with st.container(border=True):

        st.markdown(
            f'<div class="store-name">🏪 {escape(order["store_name"])}</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            f'<div class="order-ref">Order #{order_ref}  ·  '
            f'Receipt Name: {escape(order["receipt_name"])}</div>',
            unsafe_allow_html=True
        )

        st.caption(
            "Need to change something? You can cancel this order in "
            "My Orders and put its items back in your cart."
        )

        # ----------------------------------------------------
        # MATERIALS AND WEIGHT
        # ----------------------------------------------------

        for material in materials:

            if material["total_weight_kg"] is None:
                weight_text = "weight unknown"
            else:
                weight_text = kg(material["total_weight_kg"])

            st.write(
                f"• {material['description']} × {material['quantity']}"
                f"  ({weight_text})"
            )

        missing = [
            m["description"]
            for m in materials
            if m["total_weight_kg"] is None
        ]

        if total_weight is None:

            if missing:
                st.error(
                    "A vehicle cannot be chosen because the weight of "
                    "these products is missing: " + ", ".join(missing)
                )
            else:
                st.error("This order has no materials to deliver.")

            return

        st.markdown(
            f'<div class="weight-total">Total weight: {kg(total_weight)}</div>',
            unsafe_allow_html=True
        )

        # ----------------------------------------------------
        # VEHICLES THAT CAN CARRY THE ORDER
        # ----------------------------------------------------

        suitable = delivery_service.find_suitable_vehicles(
            vehicles,
            total_weight
        )

        too_small = [
            vehicle for vehicle in vehicles
            if not vehicle.can_carry(total_weight)
        ]

        if not suitable:

            largest = vehicles[-1]

            st.error(
                f"No single vehicle can carry {kg(total_weight)}. "
                f"The largest vehicle is {largest.get_display_label()}. "
                f"Please cancel this order in My Orders and buy fewer "
                f"items, or choose Pickup."
            )

            return

        # The smallest vehicle that fits is the recommended one.
        # The customer can still choose a larger vehicle.
        recommended_id = suitable[0].vehicle_type_id
        vehicle_by_id = {v.vehicle_type_id: v for v in suitable}

        def vehicle_label(vehicle_type_id):
            """Text shown next to each radio option."""
            text = vehicle_by_id[vehicle_type_id].get_display_label()

            if vehicle_type_id == recommended_id:
                text += "  -  recommended (smallest that fits)"

            return text

        selected_vehicle_id = st.radio(
            "Choose a vehicle",
            list(vehicle_by_id.keys()),
            index=0,
            format_func=vehicle_label,
            key=f"vehicle_{order_id}"
        )

        if too_small:
            st.caption(
                "Too small for this order: "
                + ", ".join(v.vehicle_name for v in too_small)
            )

        # ----------------------------------------------------
        # PICKUP LOCATION
        # ----------------------------------------------------

        st.write(f"📍 **Pickup location:** {order['address']}")

        # ----------------------------------------------------
        # DELIVERY LOCATION ON A MAP
        # ----------------------------------------------------

        st.subheader("Delivery location")

        st.caption(
            "Click anywhere on the map to drop a pin where the "
            "materials should be delivered. You can also search for "
            "a place first."
        )

        pin_key = f"pin_{order_id}"
        pin = st.session_state.get(pin_key)

        # --- Search box (press Enter to search) ---

        search_text = st.text_input(
            "Search for a place or address (optional)",
            placeholder="Example: SM City Davao, Ecoland",
            key=f"search_{order_id}"
        ).strip()

        last_search_key = f"last_search_{order_id}"

        if search_text and search_text != st.session_state.get(last_search_key):

            st.session_state[last_search_key] = search_text

            with st.spinner("Searching..."):
                found_place = location_service.search_place(search_text)

            if found_place is None:
                st.warning(
                    "That place could not be found. Try a different "
                    "name, or click on the map."
                )
            else:
                st.session_state[pin_key] = found_place
                st.rerun()

        # --- The map ---

        if pin is not None:
            center = (pin.latitude, pin.longitude)
            zoom = LocationService.PIN_ZOOM
            pin_tag = f"{pin.latitude}_{pin.longitude}"
        else:
            center = (
                LocationService.DEFAULT_LATITUDE,
                LocationService.DEFAULT_LONGITUDE
            )
            zoom = LocationService.DEFAULT_ZOOM
            pin_tag = "none"

        # The key changes whenever the pin changes, so the map
        # always redraws centered on the newest pin.
        map_data = show_map(
            center,
            zoom,
            pin,
            key=f"map_{order_id}_{pin_tag}"
        )

        clicked = map_data.get("last_clicked") if map_data else None

        if clicked:

            clicked_lat = round(float(clicked["lat"]), 6)
            clicked_lng = round(float(clicked["lng"]), 6)

            is_new_pin = (
                pin is None
                or (pin.latitude, pin.longitude) != (clicked_lat, clicked_lng)
            )

            if is_new_pin:

                with st.spinner("Looking up the address..."):
                    address = location_service.reverse_geocode(
                        clicked_lat,
                        clicked_lng
                    )

                st.session_state[pin_key] = Location(
                    address or "",
                    clicked_lat,
                    clicked_lng
                )
                st.rerun()

        # --- The chosen location ---

        delivery_address = ""

        if pin is None:

            st.info(
                "No location chosen yet. Click on the map to drop a pin."
            )

        else:

            st.success(
                f"Pin placed at {pin.latitude:.5f}, {pin.longitude:.5f}"
            )

            # The key includes the pin position, so a new pin always
            # starts with its own address text.
            delivery_address = st.text_area(
                "Delivery address or landmark",
                value=pin.address,
                placeholder="House or lot number, street, barangay, city",
                key=f"address_{order_id}_{pin.latitude}_{pin.longitude}",
                help="You can edit this text, for example to add a landmark."
            )

            if not pin.address:
                st.caption(
                    "The address could not be looked up automatically. "
                    "Please type it above."
                )

        st.write("**Delivery fee:** To be quoted")

        # ----------------------------------------------------
        # CONFIRM
        # ----------------------------------------------------

        if st.button(
            "Confirm Delivery Booking",
            type="primary",
            disabled=(pin is None),
            key=f"book_{order_id}"
        ):

            try:
                delivery_service.create_booking(
                    order,
                    selected_vehicle_id,
                    Location(delivery_address, pin.latitude, pin.longitude),
                    materials
                )
                booked = True

            except Exception as error:
                st.error(str(error))

    # Leave the page AFTER the try/except, outside the card.
    if booked:
        st.session_state.last_booked_order_id = order_id
        st.switch_page("pages/3_My_Orders.py")


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">Book Delivery</div>',
    unsafe_allow_html=True
)

st.page_link("pages/3_My_Orders.py", label="← My Orders")


# ============================================================
# LOAD ORDERS, BOOKINGS AND VEHICLES
# ============================================================

try:
    orders = order_service.get_customer_orders(TEST_CUSTOMER_ID)

    bookings = delivery_service.get_bookings_for_orders(
        [order["order_id"] for order in orders]
    )

    vehicles = delivery_service.get_active_vehicle_types()

except Exception as error:
    st.error(f"Could not load your delivery information: {error}")
    st.stop()


# ============================================================
# DELIVERY ORDERS THAT STILL NEED A BOOKING
# ============================================================

waiting_orders = [
    order for order in orders
    if order["fulfillment_type"] == OrderService.FULFILLMENT_DELIVERY
    and order["status"] == OrderService.STATUS_PENDING
    and order["order_id"] not in bookings
]

if not waiting_orders:
    st.info("You have no delivery orders waiting for a vehicle booking.")
    st.page_link("pages/0_Materials.py", label="Go to Materials")
    st.stop()

if not vehicles:
    st.warning("No delivery vehicles are available yet.")
    st.stop()

st.caption(
    "Choose a vehicle for the order and pick the delivery location on "
    "the map. Each hardware store has its own order, so each one is "
    "booked separately."
)

# With several waiting orders, the customer books one at a time,
# so only one map is on the screen.
if len(waiting_orders) == 1:

    chosen_order = waiting_orders[0]

else:

    order_labels = {
        order["order_id"]: (
            f"{order['store_name']}  -  Order "
            f"#{str(order['order_id'])[:8].upper()}  -  "
            f"PHP {order['total_amount']:,.2f}"
        )
        for order in waiting_orders
    }

    chosen_order_id = st.selectbox(
        "Which order do you want to book?",
        list(order_labels.keys()),
        format_func=lambda order_id: order_labels[order_id]
    )

    chosen_order = next(
        order for order in waiting_orders
        if order["order_id"] == chosen_order_id
    )

show_booking_card(chosen_order, vehicles)