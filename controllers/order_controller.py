from controllers.base_controller import BaseService


class OrderService(BaseService):
    """
    Handles database operations related to customer orders.

    This service communicates with the Supabase 'orders' and
    'order_items' tables.

    Business rules handled by this class:
        ONE HARDWARE STORE = ONE ORDER = ONE RECEIPT.
        If a cart contains items from two stores, the customer gets
        two separate orders. Each order has its own fulfillment
        choice (pickup or delivery).

        A customer may cancel an order only while it is still
        'pending'. The database policy enforces the same rule.

    Why this class exists:
        Carts and orders are different responsibilities.
        CartService manages what the customer MIGHT buy.
        OrderService manages what the customer DID order.
        Keeping them apart means a change to orders cannot break
        the cart, and the Streamlit pages never talk to Supabase
        directly.

    Relationship with other classes:
        - CartService.group_by_store() produces the store groups
          that create_order() receives.
        - The pages call create_order(), get_customer_orders() and
          cancel_order(). They do not need to know how Supabase works.

    OOP concepts actually used here:
        - Encapsulation: all order database work lives inside this
          class, and _rollback_order() is private by convention.
        - Abstraction: the pages call one method (create_order)
          and do not see the two inserts behind it.
        - Class constants: allowed fulfillment types, statuses, and
          status texts are defined once so no page retypes them.
        - Static method: get_status_text() needs no object data.
        Inheritance and polymorphism are NOT used, because nothing
        in this class needs them.

    Attributes:
        supabase: The Supabase connection used by every method.
    """

    # --------------------------------------------------------
    # CLASS CONSTANTS
    # --------------------------------------------------------

    # Allowed values of orders.fulfillment_type
    # (matches the chk_order_fulfillment_type database rule).
    FULFILLMENT_PICKUP = "pickup"
    FULFILLMENT_DELIVERY = "delivery"

    # Allowed values of orders.status
    # (matches the chk_order_status database rule).
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_PREPARING = "preparing"
    STATUS_READY_FOR_PICKUP = "ready_for_pickup"
    STATUS_OUT_FOR_DELIVERY = "out_for_delivery"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"

    # Customer-friendly text for every status.
    STATUS_TEXT = {
        STATUS_PENDING: "Pending",
        STATUS_CONFIRMED: "Confirmed by the store",
        STATUS_PREPARING: "Being prepared",
        STATUS_READY_FOR_PICKUP: "Ready for pickup",
        STATUS_OUT_FOR_DELIVERY: "Out for delivery",
        STATUS_COMPLETED: "Completed",
        STATUS_CANCELLED: "Cancelled"
    }

    def __init__(self):
        """
        Creates an OrderService with a Supabase connection.
        """
        super().__init__()

    # ========================================================
    # CREATING AN ORDER
    # ========================================================

    def create_order(
        self,
        customer_id,
        receipt_name,
        fulfillment_type,
        store_group
    ):
        """
        Creates ONE order for ONE hardware store.

        The store group comes from CartService.group_by_store().
        It contains the store information and the cart items the
        customer chose from that store.

        Every new order starts as 'pending'. The store moves it to
        confirmed, preparing, and so on later. This is true for both
        pickup and delivery orders.

        Steps:
            1. Validate the information.
            2. Insert one row into 'orders'.
            3. Insert one row per item into 'order_items'.
            4. If step 3 fails, delete the order again so no empty
               order is left behind.

        This method does NOT clear the cart. The page does that after
        the order is saved, because clearing the cart is CartService's
        job.

        The price of every item is copied into order_items
        (unit_price and subtotal) at the moment of ordering, so the
        receipt does not change if the store changes its price later.

        Args:
            customer_id: ID of the customer.
            receipt_name (str): Name that appears on the receipt.
            fulfillment_type (str): FULFILLMENT_PICKUP or
                FULFILLMENT_DELIVERY.
            store_group (dict): One store group with 'store_id',
                'store_name' and 'items'.

        Returns:
            dict: The created order row.

        Raises:
            ValueError: If the information is not valid.
            Exception: If Supabase did not save the order.
        """

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        receipt_name = (receipt_name or "").strip()

        if not receipt_name:
            raise ValueError("A Receipt Name is required.")

        if fulfillment_type not in (
            self.FULFILLMENT_PICKUP,
            self.FULFILLMENT_DELIVERY
        ):
            raise ValueError("Please choose Pickup or Delivery.")

        if not store_group.get("store_id"):
            raise ValueError(
                "This group has no valid hardware store, "
                "so an order cannot be created."
            )

        if not store_group.get("items"):
            raise ValueError("There are no items to order.")

        # ----------------------------------------------------
        # PREPARE THE ORDER ITEM ROWS
        # ----------------------------------------------------

        item_rows = []

        for item in store_group["items"]:
            item_rows.append({
                "listing_id": item["listing_id"],
                "quantity": int(item["quantity"]),
                "unit_price": round(float(item["price"]), 2),
                "subtotal": round(float(item["subtotal"]), 2)
            })

        total_amount = round(
            sum(row["subtotal"] for row in item_rows),
            2
        )

        # ----------------------------------------------------
        # INSERT THE ORDER
        # ----------------------------------------------------

        order_response = (
            self.supabase
            .table("orders")
            .insert({
                "customer_id": customer_id,
                "store_id": store_group["store_id"],
                "receipt_name": receipt_name,
                "fulfillment_type": fulfillment_type,
                "status": self.STATUS_PENDING,
                "total_amount": total_amount
            })
            .select("*")
            .execute()
        )

        if not order_response.data:
            raise Exception(
                "Supabase did not return the new order. "
                "Check the INSERT and SELECT policies on 'orders'."
            )

        order = order_response.data[0]
        order_id = order["order_id"]

        # ----------------------------------------------------
        # INSERT THE ORDER ITEMS
        # ----------------------------------------------------

        for row in item_rows:
            row["order_id"] = order_id

        try:
            items_response = (
                self.supabase
                .table("order_items")
                .insert(item_rows)
                .select("*")
                .execute()
            )

            if len(items_response.data or []) != len(item_rows):
                raise Exception(
                    "Supabase did not confirm all order items. "
                    "Check the INSERT and SELECT policies "
                    "on 'order_items'."
                )

        except Exception as error:
            self._rollback_order(order_id)
            raise Exception(
                f"The order could not be saved and was cancelled. "
                f"Details: {error}"
            )

        return order

    def _rollback_order(self, order_id):
        """
        Best-effort cleanup when an order could not be completed.

        It deletes the order row. The database rule
        ON DELETE CASCADE then removes any order items that were
        already saved for it.

        Errors are ignored here because the original error is the
        one the customer needs to see.

        Args:
            order_id: ID of the order to remove.
        """

        try:
            (
                self.supabase
                .table("orders")
                .delete()
                .eq("order_id", order_id)
                .execute()
            )
        except Exception:
            pass

    # ========================================================
    # CANCELLING AN ORDER
    # ========================================================

    def cancel_order(self, order_id):
        """
        Cancels an order that is still pending.

        The order stays in the database with the status 'cancelled',
        so the customer can still see it in My Orders.

        This method does NOT put the items back in the cart. The page
        does that through CartService, because the cart is CartService's
        responsibility.

        After the update the order is read again, because Supabase
        can accept an update and change nothing when a policy does
        not allow it.

        Args:
            order_id: ID of the order to cancel.

        Raises:
            Exception: If the order could not be cancelled.
        """

        (
            self.supabase
            .table("orders")
            .update({"status": self.STATUS_CANCELLED})
            .eq("order_id", order_id)
            .eq("status", self.STATUS_PENDING)
            .execute()
        )

        check = (
            self.supabase
            .table("orders")
            .select("status")
            .eq("order_id", order_id)
            .limit(1)
            .execute()
        )

        if not check.data or check.data[0]["status"] != self.STATUS_CANCELLED:
            raise Exception(
                "The order could not be cancelled. It may no longer be "
                "pending, or the UPDATE policy on 'orders' is missing."
            )

    # ========================================================
    # READING ORDERS
    # ========================================================

    def get_customer_orders(self, customer_id):
        """
        Gets all orders of a customer, newest first, together with
        the store information and the ordered items.

        Each returned order is a dictionary with:
            order_id, store_id, receipt_name, fulfillment_type,
            status, total_amount, created_at,
            store_name, address, items

        'items' is a list of dictionaries with:
            listing_id, product_name, unit, quantity,
            unit_price, subtotal

        Args:
            customer_id: ID of the customer.

        Returns:
            list: The customer's orders.
        """

        orders_response = (
            self.supabase
            .table("orders")
            .select(
                "order_id, store_id, receipt_name, fulfillment_type, "
                "status, total_amount, created_at, "
                "hardware_stores(store_name, address)"
            )
            .eq("customer_id", customer_id)
            .order("created_at", desc=True)
            .execute()
        )

        orders = orders_response.data

        if not orders:
            return []

        # Get the items of ALL these orders in ONE query.
        order_ids = [order["order_id"] for order in orders]

        items_response = (
            self.supabase
            .table("order_items")
            .select(
                "order_item_id, order_id, listing_id, quantity, "
                "unit_price, subtotal, "
                "store_listings(products(product_name, unit))"
            )
            .in_("order_id", order_ids)
            .execute()
        )

        items_by_order = {}

        for row in items_response.data:

            listing = row.get("store_listings") or {}
            product = listing.get("products") or {}

            item = {
                "listing_id": row["listing_id"],
                "product_name": product.get(
                    "product_name",
                    "(Product no longer available)"
                ),
                "unit": product.get("unit") or "unit",
                "quantity": int(row["quantity"]),
                "unit_price": float(row["unit_price"]),
                "subtotal": float(row["subtotal"])
            }

            items_by_order.setdefault(row["order_id"], []).append(item)

        # Combine everything into simple dictionaries.
        results = []

        for order in orders:

            store = order.get("hardware_stores") or {}
            items = items_by_order.get(order["order_id"], [])

            items.sort(key=lambda item: item["product_name"])

            results.append({
                "order_id": order["order_id"],
                "store_id": order["store_id"],
                "receipt_name": order["receipt_name"],
                "fulfillment_type": order["fulfillment_type"],
                "status": order["status"],
                "total_amount": float(order["total_amount"]),
                "created_at": order["created_at"],
                "store_name": store.get("store_name", "Unknown store"),
                "address": store.get("address") or "",
                "items": items
            })

        return results

    # ========================================================
    # DISPLAY HELPER
    # ========================================================

    @staticmethod
    def get_status_text(fulfillment_type, status):
        """
        Turns a status into a customer-friendly sentence.

        This is a static method because it does not need any object
        data. It only converts text.

        Args:
            fulfillment_type (str): 'pickup' or 'delivery'.
            status (str): The order status.

        Returns:
            str: Text to show the customer.
        """

        text = OrderService.STATUS_TEXT.get(
            status,
            str(status).replace("_", " ").title()
        )

        # A pending delivery order has no delivery booking yet.
        if (
            status == OrderService.STATUS_PENDING
            and fulfillment_type == OrderService.FULFILLMENT_DELIVERY
        ):
            text += " - delivery booking not completed yet"

        return text