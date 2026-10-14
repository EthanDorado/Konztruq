"""
Konztruq - one-time helper that applies small, safe text edits.

Run it from the project folder, with the virtual environment on:

    python apply_edits.py inheritance
    python apply_edits.py hardware

What it does:
    - Checks every file before changing it.
    - Makes a backup copy (.bak) of every file it changes.
    - Changes a file ONLY if all of its edits can be applied.
    - Is safe to run twice: edits that are already done are skipped.

You can delete this file and the .bak files when everything works.
"""

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def edit_file(relative_path, replacements):
    """
    Applies text replacements to ONE file.

    Args:
        relative_path (str): Path of the file inside the project.
        replacements (list): (old_text, new_text) pairs.

    Returns:
        bool: True if the file is now correct (changed or already done).
    """

    path = ROOT / relative_path

    if not path.exists():
        print(f"  MISSING       {relative_path}")
        return False

    new_text = path.read_text(encoding="utf-8")
    changed = False

    for old, new in replacements:

        if old in new_text:
            new_text = new_text.replace(old, new)
            changed = True

        elif new in new_text:
            continue  # this edit was already done

        else:
            print(f"  NOT FOUND     {relative_path}: {old!r}")
            return False

    if not changed:
        print(f"  already done  {relative_path}")
        return True

    shutil.copy(path, path.with_name(path.name + ".bak"))
    path.write_text(new_text, encoding="utf-8")
    print(f"  UPDATED       {relative_path}")
    return True


# ============================================================
# MODE 1: the four database services inherit from BaseService
# ============================================================

SERVICE_CLASSES = {
    "services/cart_service.py": "CartService",
    "services/marketplace_service.py": "MarketplaceService",
    "services/order_service.py": "OrderService",
    "services/delivery_service.py": "DeliveryService",
}


def apply_inheritance():
    """Makes the four database services children of BaseService."""

    print("Making the four database services inherit from BaseService:")

    if not (ROOT / "services" / "base_service.py").exists():
        print("  MISSING       services/base_service.py - create it first")
        return False

    success = True

    for relative_path, class_name in SERVICE_CLASSES.items():

        edits = [
            (
                "from database.supabase_client import get_supabase_client",
                "from services.base_service import BaseService"
            ),
            (
                f"class {class_name}:",
                f"class {class_name}(BaseService):"
            ),
            (
                "self.supabase = get_supabase_client()",
                "super().__init__()"
            ),
        ]

        success = edit_file(relative_path, edits) and success

    return success


# ============================================================
# MODE 2: prepare the project for the Hardware Stores tab
# ============================================================

LINK_EDIT = ('page_link("app.py"', 'page_link("pages/0_Materials.py"')
PIN_EDIT = ('color="orange"', 'color="darkblue"')
WORDING_EDIT = ("untick", "deselect")

HARDWARE_EDITS = {
    "pages/1_Cart.py": [LINK_EDIT],
    "pages/2_Checkout.py": [LINK_EDIT],
    "pages/3_My_Orders.py": [LINK_EDIT],
    "pages/4_Book_Delivery.py": [LINK_EDIT, PIN_EDIT],
    "services/delivery_service.py": [WORDING_EDIT],
}


def apply_hardware_prep():
    """
    Moves the marketplace page so it becomes "Materials", points all
    links to it, makes the map pin dark blue, and fixes one word.
    """

    print("Preparing the project for the Hardware Stores tab:")

    required = [
        "Hardware_Stores.py",
        "models/hardware_store.py",
        "services/store_service.py",
        "services/base_service.py",
    ]

    missing = [name for name in required if not (ROOT / name).exists()]

    if missing:
        for name in missing:
            print(f"  MISSING       {name} - create it first")
        return False

    success = True

    old_main = ROOT / "app.py"
    new_page = ROOT / "pages" / "0_Materials.py"

    if new_page.exists():
        print("  already done  pages/0_Materials.py exists")

    elif old_main.exists():
        shutil.copy(old_main, ROOT / "app.py.bak")
        shutil.move(str(old_main), str(new_page))
        print("  MOVED         app.py -> pages/0_Materials.py")

    else:
        print("  MISSING       app.py")
        success = False

    for relative_path, edits in HARDWARE_EDITS.items():
        success = edit_file(relative_path, edits) and success

    return success


# ============================================================
# MAIN
# ============================================================

def main():
    """Reads the mode from the command and runs it."""

    mode = sys.argv[1] if len(sys.argv) > 1 else ""

    if mode == "inheritance":
        success = apply_inheritance()

    elif mode == "hardware":
        success = apply_hardware_prep()

    else:
        print("Use one of these commands:")
        print("  python apply_edits.py inheritance")
        print("  python apply_edits.py hardware")
        return

    print()

    if success:
        print("DONE - everything is in place.")
    else:
        print(
            "STOPPED - send me the MISSING / NOT FOUND lines above. "
            "Files marked that way were not changed."
        )


main()