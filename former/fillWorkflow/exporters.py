import json
import csv


def export_json(data, filename):
    """Export data to JSON file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def export_csv(data, filename):
    """Export data to CSV file."""
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "question", "type", "options"])
        for q in data:
            writer.writerow([
                q["id"],
                q["question"],
                q["type"],
                "; ".join(q["options"])
            ])
