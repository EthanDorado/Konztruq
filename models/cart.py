class Cart:
    """
    Represents a customer's shopping cart.

    The Cart class keeps track of the customer's selected
    store listings and quantities.

    The actual cart data will eventually be stored in
    the Supabase 'carts' and 'cart_items' tables.

    OOP concepts used:
        - Class: Cart is a blueprint for a shopping cart.
        - Object: Each Cart object represents one customer's cart.
        - Encapsulation: Cart methods handle cart-related behavior.
    """

    def __init__(self, cart_id, customer_id=None):
        """
        Creates a Cart object.

        Args:
            cart_id: Unique ID of the cart.
            customer_id: Customer who owns the cart.
        """

        self.cart_id = cart_id
        self.customer_id = customer_id
        self.items = []

    def add_item(self, listing_id, quantity, price):
        """
        Adds a store listing to the cart.

        Args:
            listing_id: Store listing being purchased.
            quantity: Number of units.
            price: Price of one unit.
        """

        item = {
            "listing_id": listing_id,
            "quantity": quantity,
            "price": price
        }

        self.items.append(item)

    def get_total(self):
        """
        Calculates the total price of all items in the cart.

        Returns:
            The total cart amount.
        """

        total = 0

        for item in self.items:
            total += item["price"] * item["quantity"]

        return total