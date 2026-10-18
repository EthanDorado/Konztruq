from database.supabase_client import get_supabase_client


class BaseService:
    """
    Parent class of every service that talks to the Supabase database.

    Why this class exists:
        MarketplaceService, CartService, OrderService and
        DeliveryService all need the same thing: a connection to
        Supabase. Before, each class created that connection by itself
        with the same line of code. Now the connection is created ONCE,
        here, and every service gets it by inheriting from this class.

    Relationship with other classes:
        - MarketplaceService, CartService, OrderService and
          DeliveryService are CHILD classes. They call
          super().__init__(), so this class sets up self.supabase
          for them.
        - LocationService does not inherit from this class, because it
          talks to OpenStreetMap and not to Supabase.

    Attributes:
        supabase: The Supabase connection. Every child class uses it
            through self.supabase.

    OOP concepts used:
        - Inheritance: the children reuse the code of their parent
          instead of copying it. If the way the connection is made ever
          changes, it is changed in ONE place.
        - Encapsulation: how the connection is made is hidden here. The
          children only use self.supabase.
    """

    def __init__(self):
        """
        Creates the Supabase connection shared by all child services.
        """
        self.supabase = get_supabase_client()