from geopy.geocoders import Nominatim

from models.location import Location


class LocationService:
    """
    Finds places on the map and turns map positions into addresses.

    It uses OpenStreetMap's free Nominatim service through the
    'geopy' library. No API key is needed.

    What it is responsible for:
        - search_place(): turns typed text into a Location with a
          map position.
        - reverse_geocode(): turns a map position into an address.

    Why this class exists:
        All talking to the map provider is kept in ONE class. If the
        project later switches to Google Maps, only this class (and the
        small map function in the Book Delivery page) changes. The rest
        of the application does not know which provider is used.

    Important behavior:
        Network problems never crash the page. If a lookup fails, the
        methods return None, and the customer can still type the
        address by hand.

    Relationship with other classes:
        - Creates Location objects (models/location.py).
        - Used only by the Book Delivery page.

    OOP concepts used:
        - Encapsulation: the geocoder object is hidden inside the class.
        - Abstraction: callers ask for "a place" or "an address" and
          do not see the provider.
        - Class constants: the default map position and zoom levels.

    Attributes:
        geocoder: The geopy Nominatim object used for all lookups.
    """

    # The map starts on Davao City until the customer picks a place.
    DEFAULT_LATITUDE = 7.0731
    DEFAULT_LONGITUDE = 125.6128

    # How far the map is zoomed in (bigger number = closer).
    DEFAULT_ZOOM = 12
    PIN_ZOOM = 16

    def __init__(self):
        """
        Creates a LocationService.

        Nominatim asks every application to identify itself with a
        user_agent, so this project uses its own name.
        """

        self.geocoder = Nominatim(
            user_agent="konztruq-school-project",
            timeout=6
        )

    def search_place(self, query):
        """
        Looks up a place by name or address (Philippines only).

        Args:
            query (str): Text typed by the customer.

        Returns:
            Location or None: The place found, or None if nothing was
            found or the service could not be reached.
        """

        query = (query or "").strip()

        if not query:
            return None

        try:
            result = self.geocoder.geocode(
                query,
                country_codes="ph",
                exactly_one=True
            )

        except Exception:
            # Never crash the page because of the map service.
            return None

        if result is None:
            return None

        return Location(
            result.address,
            result.latitude,
            result.longitude
        )

    def reverse_geocode(self, latitude, longitude):
        """
        Finds the address of a position on the map.

        Args:
            latitude (float): Latitude of the clicked point.
            longitude (float): Longitude of the clicked point.

        Returns:
            str or None: The address text, or None if no address was
            found or the service could not be reached.
        """

        try:
            result = self.geocoder.reverse(
                (latitude, longitude),
                exactly_one=True,
                language="en"
            )

        except Exception:
            # Never crash the page because of the map service.
            return None

        if result is None:
            return None

        return result.address