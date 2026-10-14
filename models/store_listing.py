class StoreListing:
    """
    Represents a hardware store's offer for a specific product.

    A StoreListing connects a Product with a Hardware Store
    and stores information that can differ between stores,
    such as price and stock quantity.

    Example:

        Product:
            Portland Cement 40kg

        Store A:
            Price = PHP 280

        Store B:
            Price = PHP 265

    Both stores sell the same Product, but each has its own
    StoreListing.
    """

    def __init__(
        self,
        listing_id,
        store_id,
        product_id,
        price,
        stock_quantity,
        is_available=True
    ):
        """
        Creates a StoreListing object.

        Attributes:
            listing_id: Unique ID of the listing.
            store_id: ID of the hardware store.
            product_id: ID of the product being sold.
            price: Store's selling price.
            stock_quantity: Available stock.
            is_available: Whether customers can purchase it.
        """

        self.listing_id = listing_id
        self.store_id = store_id
        self.product_id = product_id
        self.price = price
        self.stock_quantity = stock_quantity
        self.is_available = is_available

    def is_in_stock(self):
        """
        Checks whether the listing has available stock.

        Returns:
            True if stock is greater than zero and the listing
            is available. Otherwise, returns False.
        """
        return self.stock_quantity > 0 and self.is_available

    def get_subtotal(self, quantity):
        """
        Calculates the cost of a specific quantity.

        Args:
            quantity: Number of items being purchased.

        Returns:
            Total price for the requested quantity.
        """
        return self.price * quantity