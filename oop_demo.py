"""
Konztruq - Four Pillars of OOP demo.

Run it from the project folder:   python oop_demo.py

It prints one example of each pillar from the real Konztruq code.
It does NOT use the internet or the database.
"""

import sys

sys.stdout.reconfigure(encoding="utf-8")

from models.vehicle_type import VehicleType
from models.location import Location
from models.fulfillment import (
    Fulfillment,
    PickupFulfillment,
    DeliveryFulfillment
)
from services.cart_service import CartService
from services.order_service import OrderService
from services.delivery_service import DeliveryService
from services.marketplace_service import MarketplaceService


def title(text):
    """Prints a heading."""
    print()
    print("=" * 62)
    print(text)
    print("=" * 62)


# ------------------------------------------------------------
title("1. ENCAPSULATION - data and rules kept together in one class")

multicab = VehicleType("demo-id", "Multicab", 500)

print("Vehicle:", multicab.get_display_label())
print("Can carry 450 kg?", multicab.can_carry(450))
print("Can carry 800 kg?", multicab.can_carry(800))
print(
    "Valid map position?",
    Location("Davao City", 7.0731, 125.6128).has_coordinates()
)
print(
    "Latitude 999 valid?",
    Location("Bad place", 999, 125.6).has_coordinates()
)

# ------------------------------------------------------------
title("2. ABSTRACTION - hide the details, show only what is needed")

try:
    Fulfillment()
except TypeError:
    print("Fulfillment is an abstract class: it cannot be created directly.")

print("The pages only call create_order() and create_booking().")
print("The database steps are hidden inside the services.")

# ------------------------------------------------------------
title("3. INHERITANCE - children reuse their parent")

for service_class in (
    MarketplaceService,
    CartService,
    OrderService,
    DeliveryService
):
    print(
        f"{service_class.__name__} inherits from "
        f"{service_class.__bases__[0].__name__}"
    )

for fulfillment_class in (PickupFulfillment, DeliveryFulfillment):
    print(
        f"{fulfillment_class.__name__} inherits from "
        f"{fulfillment_class.__bases__[0].__name__}"
    )

# ------------------------------------------------------------
title("4. POLYMORPHISM - same method call, different behavior")

address = "J.P. Laurel Avenue, Davao City"

for fulfillment_type in ("pickup", "delivery"):

    option = Fulfillment.create(fulfillment_type)

    print()
    print("Object:", type(option).__name__)
    print("  get_label():", option.get_label())
    print("  requires_booking():", option.requires_booking())
    print("  get_checkout_note():", option.get_checkout_note(address))
    print("  get_receipt_heading():", option.get_receipt_heading(address))
    print("  get_pending_note():", repr(option.get_pending_note(False)))