"""
Konztruq - polish helper.

Run it from the project folder, with the virtual environment on:

    python polish.py

What it does:
    1. Creates .streamlit/config.toml so the whole app uses the
       Konztruq colors (buttons, checkboxes and radio buttons become
       Cerulean blue instead of Streamlit's default red).
    2. Changes the link text "Go to the Marketplace" to
       "Go to Materials" on four pages, to match the renamed tab.

Safe to run twice. It makes a .bak backup of every page it changes.
"""

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent

CONFIG_TEXT = """[theme]
base = "light"
primaryColor = "#007BA7"
backgroundColor = "#F4F9FB"
secondaryBackgroundColor = "#FFFFFF"
textColor = "#111111"

[client]
toolbarMode = "minimal"
"""

PAGES = [
    "pages/1_Cart.py",
    "pages/2_Checkout.py",
    "pages/3_My_Orders.py",
    "pages/4_Book_Delivery.py",
]

LABEL_EDIT = (
    'label="Go to the Marketplace"',
    'label="Go to Materials"'
)


def create_theme():
    """
    Creates the Streamlit settings file with the Konztruq colors.

    An existing settings file is never overwritten.

    Returns:
        bool: True when the settings file is in place.
    """

    folder = ROOT / ".streamlit"
    config = folder / "config.toml"

    if config.exists():
        print("  already there  .streamlit/config.toml (left unchanged)")
        return True

    folder.mkdir(exist_ok=True)
    config.write_text(CONFIG_TEXT, encoding="utf-8")
    print("  CREATED        .streamlit/config.toml")
    return True


def edit_file(relative_path, replacements):
    """
    Applies text replacements to ONE file.

    The file is changed only if every edit fits, and a .bak backup
    is made first.

    Args:
        relative_path (str): Path of the file inside the project.
        replacements (list): (old_text, new_text) pairs.

    Returns:
        bool: True if the file is now correct (changed or already done).
    """

    path = ROOT / relative_path

    if not path.exists():
        print(f"  MISSING        {relative_path}")
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
            print(f"  NOT FOUND      {relative_path}: {old!r}")
            return False

    if not changed:
        print(f"  already done   {relative_path}")
        return True

    shutil.copy(path, path.with_name(path.name + ".bak"))
    path.write_text(new_text, encoding="utf-8")
    print(f"  UPDATED        {relative_path}")
    return True


def main():
    """Runs both polish steps and reports the result."""

    print("Applying the Konztruq polish:")

    success = create_theme()

    for page in PAGES:
        success = edit_file(page, [LABEL_EDIT]) and success

    print()

    if success:
        print("DONE - restart Streamlit to see the new colors.")
    else:
        print(
            "STOPPED - send me the MISSING / NOT FOUND lines above. "
            "Files marked that way were not changed."
        )


main()