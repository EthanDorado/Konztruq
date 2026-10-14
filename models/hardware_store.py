class HardwareStore:
    """
    Represents ONE hardware store location: a main store or one of
    its branches.

    Why this class exists:
        The Hardware Stores page needs to show the same facts for every
        location (name, address, phone numbers, rating) and needs to know
        whether a location is a branch. Keeping those facts and rules in
        one class means every page shows them the same way.

    How branches work:
        A branch is just another row in the 'hardware_stores' table
        whose parent_store_id points to its main store. A main store has
        no parent. Each location (main or branch) has its own address,
        phone number, rating, and products.

    Relationship with other classes:
        - StoreService reads rows from the 'hardware_stores' table and
          turns each row into a HardwareStore object.
        - The Hardware Stores page asks these objects how to display
          themselves.

    Attributes:
        store_id: Unique ID of this location.
        store_name (str): Full name, for example
            "ABC Construction Depot - Toril Branch".
        address (str): Street address of this location.
        phone_number (str or None): Mobile or main phone number.
        landline_number (str or None): Landline number, if the store has one.
        rating (float or None): Rating from 0 to 5, or None if unrated.
        parent_store_id: ID of the main store, or None for a main store.
        branch_name (str or None): Branch name, for example "Toril Branch".
        is_active (bool): Whether customers can see this location.

    OOP concepts used:
        - Class and object: each database row becomes one object.
        - Encapsulation: the rules for showing a rating, contact lines,
          and branch label live inside the class.
        - Class method: from_row() builds an object from a database row.
        - Static method: format_rating() needs no object data.
    """

    def __init__(
        self,
        store_id,
        store_name,
        address,
        phone_number=None,
        landline_number=None,
        rating=None,
        parent_store_id=None,
        branch_name=None,
        is_active=True
    ):
        """
        Creates a HardwareStore object.

        Args:
            store_id: Unique ID of the location.
            store_name (str): Name of the location.
            address (str): Street address.
            phone_number (str, optional): Phone number.
            landline_number (str, optional): Landline number.
            rating (float, optional): Rating from 0 to 5.
            parent_store_id (optional): ID of the main store (branches only).
            branch_name (str, optional): Name of the branch.
            is_active (bool, optional): Whether it can be shown.
        """

        self.store_id = store_id
        self.store_name = store_name
        self.address = address or ""
        self.phone_number = phone_number
        self.landline_number = landline_number
        self.rating = float(rating) if rating is not None else None
        self.parent_store_id = parent_store_id
        self.branch_name = branch_name
        self.is_active = is_active

    @classmethod
    def from_row(cls, row):
        """
        Builds a HardwareStore from one row of the 'hardware_stores' table.

        Args:
            row (dict): A row returned by Supabase.

        Returns:
            HardwareStore: The matching object.
        """

        return cls(
            store_id=row["store_id"],
            store_name=row["store_name"],
            address=row.get("address"),
            phone_number=row.get("phone_number"),
            landline_number=row.get("landline_number"),
            rating=row.get("rating"),
            parent_store_id=row.get("parent_store_id"),
            branch_name=row.get("branch_name"),
            is_active=row.get("is_active", True)
        )

    def is_branch(self):
        """
        Checks whether this location is a branch of another store.

        Returns:
            bool: True for a branch, False for a main store.
        """

        return self.parent_store_id is not None

    def get_branch_label(self):
        """
        Returns the name to show when choosing a branch.

        A main store has no branch name, so it is shown as
        "Main Branch".
        """

        return self.branch_name or "Main Branch"

    def get_contact_lines(self):
        """
        Returns the contact details this location has, one per line.

        Returns:
            list: Lines such as "📞 0917-100-1001". A line is only
            included when the store has that number.
        """

        lines = []

        if self.phone_number:
            lines.append(f"📞 {self.phone_number}")

        if self.landline_number:
            lines.append(f"☎ {self.landline_number}")

        return lines

    def get_rating_text(self):
        """
        Returns this location's rating as text, for example "★ 4.5".
        """

        return HardwareStore.format_rating(self.rating)

    @staticmethod
    def format_rating(value):
        """
        Turns a rating number into text.

        This is a static method because it does not need any object
        data, so it can also format an average rating.

        Args:
            value (float or None): A rating from 0 to 5.

        Returns:
            str: "★ 4.5", or "No ratings yet" when there is no rating.
        """

        if value is None:
            return "No ratings yet"

        return f"★ {value:.1f}"