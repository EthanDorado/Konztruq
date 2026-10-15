# Konztruq

Konztruq is a customer-focused construction-materials marketplace and delivery booking system, built as a Python OOP course project.

Customers compare material prices across hardware stores, buy by pickup or delivery, and book a vehicle for delivery by choosing the drop-off location on a map.

## Main features

1. **Price comparison and Add to Cart** - search a material, see every store's price and stock side by side, and add the store you choose to the cart. The cheapest in-stock offer is highlighted but never picked automatically.
2. **Order for Pickup** - choose which cart items to buy, enter a Receipt Name, and pick Pickup. One order and one receipt are created per hardware store.
3. **Vehicle booking with map delivery** - for delivery orders, the app weighs the materials, shows only the vehicles that can carry the load, and saves the delivery location picked on an interactive map.

Also included: a Hardware Stores tab with store profiles, ratings, and branches; cancelling pending orders; and sold-out items that stay visible for price checking.

## Technology

Python 3, Streamlit, Supabase (PostgreSQL), folium with OpenStreetMap, geopy, python-dotenv.

## Python OOP in this project

| Pillar | Where to find it |
|---|---|
| Encapsulation | `models/vehicle_type.py` (a vehicle keeps its weight limit and `can_carry()` together), `models/location.py` |
| Abstraction | `services/order_service.py` (`create_order()` hides the database steps), `models/fulfillment.py` (abstract class) |
| Inheritance | `services/base_service.py` is the parent of the Cart, Order, Delivery, Marketplace, and Store services; `PickupFulfillment` and `DeliveryFulfillment` inherit from `Fulfillment` |
| Polymorphism | `models/fulfillment.py` (Pickup and Delivery answer the same methods differently), used in `pages/3_My_Orders.py` |

## Project structure

```text
Hardware_Stores.py   main Streamlit page
pages/               Materials, Cart, Checkout, My Orders, Book Delivery
services/            business logic and database access (one class per job)
models/              domain classes (VehicleType, Location, Fulfillment, HardwareStore)
database/            Supabase connection
oop_demo.py          demonstration of the four OOP pillars
```

## Current limits

A test customer is used instead of real login, the delivery fee is shown as "To be quoted", stock is not reduced when an order is placed, and store ratings are sample data.