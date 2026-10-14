class Product:
    """
    Represents a construction material available in Konztruq.

    A Product describes what the item is, such as:
    "Portland Cement 40kg".

    The Product class does not store a store-specific price.
    Prices belong to StoreListing because different hardware
    stores can sell the same product at different prices.
    """

    def __init__(
        self,
        product_id,
        product_name,
        description,
        category,
        unit,
        weight_kg,
        is_active=True
    ):
        """
        Creates a Product object.

        Attributes:
            product_id: Unique ID of the product.
            product_name: Name of the construction material.
            description: Description of the product.
            category: Product category.
            unit: Selling unit, such as bag or piece.
            weight_kg: Weight of one unit in kilograms.
            is_active: Whether the product is currently available.
        """

        self.product_id = product_id
        self.product_name = product_name
        self.description = description
        self.category = category
        self.unit = unit
        self.weight_kg = weight_kg
        self.is_active = is_active

    def get_display_name(self):
        """
        Returns the product name for display in the application.
        """
        return self.product_name

    def get_weight(self):
        """
        Returns the weight of one product unit.
        """
        return self.weight_kg