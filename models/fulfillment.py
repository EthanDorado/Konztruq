from abc import ABC, abstractmethod


class Fulfillment(ABC):
    """
    Abstract parent class: describes HOW an order reaches the customer.

    Why this class exists:
        An order is either picked up at the store or delivered, and many
        parts of the app behave differently for each one: the label shown
        at checkout, the note under it, the check that decides whether
        the choice is possible, and how the receipt describes it.
        Instead of repeating "if pickup ... else delivery" in every page,
        each way is its own class, and the pages simply ask the object.

    Relationship with other classes:
        - PickupFulfillment and DeliveryFulfillment are the CHILD classes.
        - The Checkout and My Orders pages call the same methods on
          whichever child they have. The child decides what to do.
        - The value of TYPE matches the 'fulfillment_type' column of the
          'orders' table ('pickup' or 'delivery').

    Attributes:
        TYPE (str): A class attribute. Each child sets it to its own
            value. The parent leaves it as None.

    Methods every child MUST provide (abstract methods):
        get_label(), requires_booking(), get_checkout_note(),
        check_items(), get_receipt_heading(), get_pending_note().

    OOP concepts used:
        - Abstraction: this class cannot be created directly. It only
          defines WHAT every fulfillment must be able to do. The children
          define HOW.
        - Inheritance: PickupFulfillment and DeliveryFulfillment extend
          this class.
        - Polymorphism: every child has the same methods, but each one
          behaves in its own way (method overriding). A page can call
          fulfillment.get_label() without knowing which child it holds.
        - Factory method: create() builds the right child from the text
          stored in the database.
    """

    # Each child class sets its own value ('pickup' or 'delivery').
    TYPE = None

    @classmethod
    def create(cls, fulfillment_type):
        """
        Builds the right child object for a fulfillment type.

        Always call it on the parent: Fulfillment.create("pickup").
        Python finds the matching child by looking at the subclasses of
        Fulfillment, so a new type (for example a courier) would only
        need a new child class.

        Args:
            fulfillment_type (str): 'pickup' or 'delivery'.

        Returns:
            Fulfillment: A PickupFulfillment or DeliveryFulfillment object.

        Raises:
            ValueError: If the type is not known.
        """

        for subclass in cls.__subclasses__():
            if subclass.TYPE == fulfillment_type:
                return subclass()

        raise ValueError(f"Unknown fulfillment type: {fulfillment_type}")

    def get_type(self):
        """
        Returns the text saved in orders.fulfillment_type
        ('pickup' or 'delivery').
        """

        return self.TYPE

    @abstractmethod
    def get_label(self):
        """Returns the name shown to the customer, for example 'Pickup'."""

    @abstractmethod
    def requires_booking(self):
        """
        Says whether an order of this kind needs a vehicle booking after
        it is placed.

        Returns:
            bool: True if a delivery booking is needed.
        """

    @abstractmethod
    def get_checkout_note(self, store_address):
        """
        Returns the sentence shown at checkout under the customer's choice.

        Args:
            store_address (str): Address of the hardware store.
        """

    @abstractmethod
    def check_items(self, items, delivery_service, vehicles):
        """
        Checks whether this way of receiving the items is possible.

        Every child accepts the same three inputs, even when it does not
        need all of them. That is what lets a page call it without
        knowing which child it holds.

        Args:
            items (list): The selected cart items of ONE store.
            delivery_service: A DeliveryService object.
            vehicles (list): VehicleType objects.

        Returns:
            dict: {"ok": bool, "total_weight": float or None,
                   "message": text or None}
        """

    @abstractmethod
    def get_receipt_heading(self, store_address):
        """
        Returns the line shown on the receipt that says how the order
        is received (markdown text).

        Args:
            store_address (str): Address of the hardware store.
        """

    @abstractmethod
    def get_pending_note(self, has_booking):
        """
        Returns extra text for the status line of a pending order.

        Args:
            has_booking (bool): True if a delivery booking exists.

        Returns:
            str: Text to add after the status, or an empty string.
        """


class PickupFulfillment(Fulfillment):
    """
    The customer collects the order at the hardware store.

    A child of Fulfillment. It overrides every abstract method with the
    behavior of a pickup order: no vehicle, no booking, and no weight
    limit.
    """

    TYPE = "pickup"

    def get_label(self):
        """Returns 'Pickup'."""
        return "Pickup"

    def requires_booking(self):
        """A pickup order never needs a delivery booking."""
        return False

    def get_checkout_note(self, store_address):
        """Tells the customer where to collect the order."""

        if store_address:
            return f"You will pick this order up at: {store_address}"

        return "You will pick this order up at the store."

    def check_items(self, items, delivery_service, vehicles):
        """Pickup is always possible, so the check always passes."""

        return {"ok": True, "total_weight": None, "message": None}

    def get_receipt_heading(self, store_address):
        """Shows where the order is collected."""

        if store_address:
            return f"**Pick up at:** 📍 {store_address}"

        return "**Pick up at:** the store"

    def get_pending_note(self, has_booking):
        """A pending pickup order has nothing extra to explain."""
        return ""


class DeliveryFulfillment(Fulfillment):
    """
    The order is delivered by a vehicle booked by the customer.

    A child of Fulfillment. It overrides every abstract method with the
    behavior of a delivery order: it needs a booking, and the load must
    fit in one of the vehicles.
    """

    TYPE = "delivery"

    def get_label(self):
        """Returns 'Delivery'."""
        return "Delivery"

    def requires_booking(self):
        """A delivery order needs a vehicle booking."""
        return True

    def get_checkout_note(self, store_address):
        """Tells the customer what happens after placing the order."""

        return (
            "After you place the order, you will choose a vehicle and "
            "the delivery location on a map."
        )

    def check_items(self, items, delivery_service, vehicles):
        """
        Asks the DeliveryService whether one vehicle can carry the items.

        If the check itself fails, the customer is told and delivery is
        treated as not possible.
        """

        try:
            return delivery_service.check_delivery_for_items(items, vehicles)

        except Exception as error:
            return {
                "ok": False,
                "total_weight": None,
                "message": (
                    f"Could not check delivery for this store: {error}"
                )
            }

    def get_receipt_heading(self, store_address):
        """Shows that the order is delivered."""
        return "**Fulfillment:** Delivery"

    def get_pending_note(self, has_booking):
        """Explains that a pending delivery still needs its booking."""

        if has_booking:
            return ""

        return " - delivery booking not completed yet"