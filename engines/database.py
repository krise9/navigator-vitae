import csv
import os
from datetime import datetime


def save_response(navigator_id, result, filename="data/responses.csv"):
    file_exists = os.path.isfile(filename)

    row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "navigator_id": navigator_id,
        "module": "behavior",
        "version": "v0.1",
        "type": result["type"],
        "E": result["scores"]["E"],
        "I": result["scores"]["I"],
        "S": result["scores"]["S"],
        "N": result["scores"]["N"],
        "T": result["scores"]["T"],
        "F": result["scores"]["F"],
        "J": result["scores"]["J"],
        "P": result["scores"]["P"],
        "I_E": result["axis_positions"]["I_E"],
        "S_N": result["axis_positions"]["S_N"],
        "T_F": result["axis_positions"]["T_F"],
        "J_P": result["axis_positions"]["J_P"],
    }

    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)