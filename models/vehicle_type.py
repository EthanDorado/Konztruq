class VehicleType:
    """
    Represents one kind of delivery vehicle that a customer can book,
    for example "Pickup truck".

    Why this class exists:
        Choosing a vehicle depends on one rule: the vehicle must be
        able to carry the total weight of the order. That rule belongs
        to the vehicle itself, so it lives in this class and not in the
        Streamlit page.

    Relationship with other classes:
        - DeliveryService reads rows from the 'vehicle_types' table and
          turns each row into a VehicleType object.
        - The Book Delivery page asks each VehicleType whether it can
          carry the order.

    Attributes:
        vehicle_type_id: Unique ID of the vehicle type.
        vehicle_name (str): Name shown to the customer.
        max_weight_kg (float): Heaviest load this vehicle can carry.
        description (str or None): Short description of the vehicle.
        is_active (bool): Whether customers can book this vehicle.

    OOP concepts used:
        - Class and object: each database row becomes one object.
        - Encapsulation: the capacity rule is kept inside the class
          that owns the capacity data.
        - Class method: from_row() is an alternative constructor that
          builds an object from a database row.
    """

    def __init__(
        self,
        vehicle_type_id,
        vehicle_name,
        max_weight_kg,
        description=None,
        is_active=True
    ):
        """
        Creates a VehicleType object.

        Args:
            vehicle_type_id: Unique ID of the vehicle type.
            vehicle_name (str): Name of the vehicle.
            max_weight_kg (float): Maximum load in kilograms.
            description (str, optional): Short description.
            is_active (bool, optional): Whether it can be booked.
        """

        self.vehicle_type_id = vehicle_type_id
        self.vehicle_name = vehicle_name
        self.max_weight_kg = float(max_weight_kg)
        self.description = description
        self.is_active = is_active

    @classmethod
    def from_row(cls, row):
        """
        Builds a VehicleType from one row of the 'vehicle_types' table.

        Args:
            row (dict): A row returned by Supabase.

        Returns:
            VehicleType: The matching object.
        """

        return cls(
            vehicle_type_id=row["vehicle_type_id"],
            vehicle_name=row["vehicle_name"],
            max_weight_kg=row["max_weight_kg"],
            description=row.get("description"),
            is_active=row.get("is_active", True)
        )

    def can_carry(self, weight_kg):
        """
        Checks whether this vehicle can carry a given weight.

        Args:
            weight_kg (float): Total weight of the order.

        Returns:
            bool: True if the weight is within the vehicle's limit.
        """

        return float(weight_kg) <= self.max_weight_kg

    def get_spare_capacity(self, weight_kg):
        """
        Calculates how much more weight the vehicle could still carry.

        Args:
            weight_kg (float): Total weight of the order.

        Returns:
            float: Spare capacity in kilograms (negative if too heavy).
        """

        return self.max_weight_kg - float(weight_kg)

    def get_display_label(self):
        """
        Returns the text shown to the customer, for example
        "Bongo / Light truck (up to 1,000 kg)".
        """

        return f"{self.vehicle_name} (up to {self.max_weight_kg:,.0f} kg)"