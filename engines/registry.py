import csv
import os


REGISTRY_FILE = "data/registry.csv"


def get_person(navigator_id):
    """
    Zoek een persoon op basis van Navigator ID.
    Geeft een dictionary terug als de ID bestaat.
    Geeft None terug als de ID niet bestaat.
    """

    if not os.path.isfile(REGISTRY_FILE):
        raise FileNotFoundError(f"Registry file niet gevonden: {REGISTRY_FILE}")

    with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            if row["navigator_id"].strip() == navigator_id.strip():
                return row

    return None