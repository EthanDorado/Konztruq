class Location:
    """
    Represents ONE place on the map: an address text and, when known,
    its latitude and longitude.

    Why this class exists:
        A delivery has two places: where the materials are picked up
        (Point A) and where they are delivered (Point B). Both are
        "a place with an address and coordinates", so one class
        describes both. Today Point A is always the hardware store and
        Point B is chosen on the map. Later the customer will be able
        to choose Point A too, and this class will not need to change.

    Relationship with other classes:
        - LocationService creates Location objects from map searches.
        - DeliveryService saves and reads Location objects for
          delivery bookings.
        - The Book Delivery and My Orders pages show them.

    Attributes:
        address (str): Readable address or landmark text.
        latitude (float or None): North-south position.
        longitude (float or None): East-west position.

    OOP concepts used:
        - Class and object: each place on the map is one object.
        - Encapsulation: the rules for valid coordinates live here.
        - Reuse: the same class is used for pickup and delivery points.
    """

    def __init__(self, address, latitude=None, longitude=None):
        """
        Creates a Location object.

        Args:
            address (str): Address or landmark text.
            latitude (float, optional): Latitude in degrees.
            longitude (float, optional): Longitude in degrees.
        """

        self.address = (address or "").strip()

        self.latitude = float(latitude) if latitude is not None else None
        self.longitude = float(longitude) if longitude is not None else None

    def has_coordinates(self):
        """
        Checks whether this place has a valid map position.

        Returns:
            bool: True if latitude and longitude are both present and
            inside the valid range.
        """

        if self.latitude is None or self.longitude is None:
            return False

        return (
            -90 <= self.latitude <= 90
            and -180 <= self.longitude <= 180
        )

    def get_map_url(self):
        """
        Builds a link that opens this place on OpenStreetMap.

        Returns:
            str or None: The link, or None if there are no coordinates.
        """

        if not self.has_coordinates():
            return None

        lat = f"{self.latitude:.6f}"
        lng = f"{self.longitude:.6f}"

        return (
            f"https://www.openstreetmap.org/?mlat={lat}&mlon={lng}"
            f"#map=17/{lat}/{lng}"
        )

    def get_short_text(self):
        """
        Returns the address if there is one, otherwise the coordinates.
        """

        if self.address:
            return self.address

        if self.has_coordinates():
            return f"{self.latitude:.5f}, {self.longitude:.5f}"

        return "No location"