from models.hardware_store import HardwareStore
from controllers.base_controller import BaseService


class StoreService(BaseService):
    """
    Handles database operations for browsing hardware stores.

    This service communicates with the Supabase 'hardware_stores' and
    'store_listings' tables.

    What it is responsible for:
        - Building the hardware directory: every main store together
          with its branches.
        - Getting the products of ONE store location only.

    Why this class exists:
        MarketplaceService answers "which stores sell THIS product?".
        StoreService answers the opposite question: "what does THIS
        store sell?". Keeping them apart keeps each class simple, and
        the pages never talk to Supabase directly.

    Relationship with other classes:
        - A child of BaseService, which gives it the Supabase
          connection (self.supabase).
        - Creates HardwareStore objects (models/hardware_store.py).
        - The Hardware Stores page shows the results, and adding to the
          cart is done by CartService.

    OOP concepts used:
        - Inheritance: the Supabase connection comes from BaseService.
        - Encapsulation and abstraction: the page asks for "the
          directory" or "a store's products" and never sees queries.
        - Composition: the service builds and returns HardwareStore
          objects.
    """

    def __init__(self):
        """
        Creates a StoreService. The Supabase connection is set up by
        the parent class, BaseService.
        """
        super().__init__()

    def get_hardware_directory(self):
        """
        Builds the list of hardware stores shown on the directory page.

        Every MAIN store becomes one entry. Its branches are grouped
        inside that entry, so a hardware with branches is shown once.

        Each entry is a dictionary with:
            main (HardwareStore): The main store.
            branches (list): HardwareStore objects, sorted by name.
            locations (list): The main store first, then its branches.
            average_rating (float or None): Average rating of all
                locations that have a rating.

        Returns:
            list: One entry per main store, sorted by name.
        """

        response = (
            self.supabase
            .table("hardware_stores")
            .select("*")
            .eq("is_active", True)
            .order("store_name")
            .execute()
        )

        stores = [HardwareStore.from_row(row) for row in response.data]

        # Group the branches under their main store.
        branches_by_parent = {}

        for store in stores:
            if store.is_branch():
                branches_by_parent.setdefault(
                    store.parent_store_id, []
                ).append(store)

        directory = []

        for store in stores:

            if store.is_branch():
                continue

            branches = sorted(
                branches_by_parent.get(store.store_id, []),
                key=lambda branch: branch.get_branch_label()
            )

            locations = [store] + branches

            directory.append({
                "main": store,
                "branches": branches,
                "locations": locations,
                "average_rating": self.calculate_average_rating(locations)
            })

        return directory

    def calculate_average_rating(self, locations):
        """
        Calculates the average rating of several locations.

        Locations without a rating are ignored.

        Args:
            locations (list): HardwareStore objects.

        Returns:
            float or None: The average, or None if nobody has a rating.
        """

        ratings = [
            location.rating
            for location in locations
            if location.rating is not None
        ]

        if not ratings:
            return None

        return sum(ratings) / len(ratings)

    def get_store_products(self, store_id, search_term=""):
        """
        Gets the products that ONE store location sells, and only that
        store's products.

        Sold-out products are included, because Konztruq is also a
        price-checking application. They are placed at the end of the
        list. A listing is only left out when the store disabled it.

        Each product is a dictionary with:
            listing_id, product_name, description, category, unit,
            weight_kg, price, stock

        Args:
            store_id: ID of the store location.
            search_term (str, optional): Only products whose name
                contains this text are returned.

        Returns:
            list: The store's products.
        """

        response = (
            self.supabase
            .table("store_listings")
            .select(
                "listing_id, store_id, price, stock_quantity, is_available, "
                "products(product_name, description, category, unit, weight_kg)"
            )
            .eq("store_id", store_id)
            .eq("is_available", True)
            .execute()
        )

        search_term = (search_term or "").strip().lower()

        products = []

        for row in response.data:

            product = row.get("products")

            # A product the database no longer shows is skipped.
            if not product:
                continue

            name = product["product_name"]

            if search_term and search_term not in name.lower():
                continue

            weight = product.get("weight_kg")

            products.append({
                "listing_id": row["listing_id"],
                "product_name": name,
                "description": product.get("description"),
                "category": product.get("category"),
                "unit": product.get("unit"),
                "weight_kg": float(weight) if weight is not None else None,
                "price": float(row["price"]),
                "stock": int(row["stock_quantity"])
            })

        # Available products first, sold-out ones last, then by name.
        products.sort(
            key=lambda item: (item["stock"] <= 0, item["product_name"])
        )

        return products