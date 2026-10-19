# Konztruq

Konztruq is a customer-focused construction materials marketplace and delivery booking system built with Python and Streamlit for an OOP course project.

Customers can compare material prices across hardware stores, add their chosen offers to a cart, place orders for pickup, and book vehicle delivery by selecting a drop-off location on a map.

## Main Features

1. **Price Comparison and Add to Cart** - Search for construction materials, compare prices and stock across hardware stores, and add the offer from the store you choose. The cheapest in-stock offer may be highlighted, but it is never selected automatically.

2. **Order for Pickup** - Select cart items, enter a receipt name, and choose pickup. Orders and receipts are organized by hardware store.

3. **Vehicle Booking for Delivery** - Choose delivery details and a drop-off location on an interactive map. The system can check vehicle capacity against the material weight when the relevant feature is available.

Other features include a Hardware Stores page with store profiles and branches, pending-order cancellation, and sold-out products that remain visible for price comparison.

## Technology

* Python 3
* Streamlit
* Supabase (PostgreSQL)
* Folium and OpenStreetMap
* Geopy
* python-dotenv

## Python OOP in This Project

| Pillar        | Where to Find It                                                                                                                                                                                         |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Encapsulation | `models/vehicle_type.py` and `models/location.py` keep related data and validation behavior together.                                                                                                    |
| Abstraction   | `services/order_controller.py` provides order-related methods that hide database operations; `models/fulfillment.py` defines the fulfillment abstraction.                                                   |
| Inheritance   | `services/base_controller.py` provides shared behavior to service classes, if they inherit from it in the current implementation. `PickupFulfillment` and `DeliveryFulfillment` inherit from `Fulfillment`. |
| Polymorphism  | `PickupFulfillment` and `DeliveryFulfillment` implement common methods with different behavior, as defined in `models/fulfillment.py`.                                                                   |

The `oop_demo.py` script provides examples of the four OOP pillars using project classes.

## Project Structure

```text
Konztruq/
├── app.py                  Main Streamlit entry point and navigation
├── models/                 Domain classes and data models
├── views/                  Customer-facing Streamlit pages
├── controllers/            Coordinates page actions and application logic
├── database/               Supabase connection
└── oop_demo.py             OOP demonstration script
```

## Current Limitations

* A test customer is used instead of a complete real-user login system.
* Delivery fees may be displayed as "To be quoted."
* Stock may not be reduced automatically when an order is placed.
* Store ratings use sample data.
