import json
import os
from datetime import date, datetime, timedelta, timezone
from google.cloud import bigquery

PROJECT = "apa-data-410213"
YEAR = 2026

WEEKS = [
    {"label": "Aug 1–7",  "start": f"{YEAR}-08-01", "end": f"{YEAR}-08-07"},
    {"label": "Aug 8–14", "start": f"{YEAR}-08-08", "end": f"{YEAR}-08-14"},
    {"label": "Aug 15–21","start": f"{YEAR}-08-15", "end": f"{YEAR}-08-21"},
    {"label": "Aug 22–28","start": f"{YEAR}-08-22", "end": f"{YEAR}-08-28"},
    {"label": "Aug 29–31","start": f"{YEAR}-08-29", "end": f"{YEAR}-08-31"},
]

CRESCENDO_DATES = [f"{YEAR}-08-27", f"{YEAR}-08-28", f"{YEAR}-08-29"]


def normalize_species(s):
    if not s:
        return "Other"
    s = s.strip()
    if s == "Dog":
        return "Dog"
    if s == "Cat":
        return "Cat"
    return "Other"


def run():
    client = bigquery.Client(project=PROJECT)

    query = f"""
    SELECT
      DATE(o.outcomeDate) AS outcome_date,
      a.species,
      COUNT(*) AS adoptions
    FROM `{PROJECT}.shelterluv.Outcomes` o
    JOIN `{PROJECT}.shelterluv.Animals` a
      ON o.animalInternalID = a.animalInternalID
    WHERE o.outcomeType = 'Outcome.Adoption'
      AND DATE(o.outcomeDate) BETWEEN '{YEAR}-08-01' AND '{YEAR}-08-31'
      AND (o.outcomeSubType NOT LIKE '%NCSPAC%' OR o.outcomeSubType IS NULL)
    GROUP BY 1, 2
    ORDER BY 1
    """

    rows = list(client.query(query).result())

    # Build daily lookup: {date_str: {species: count}}
    daily = {}
    for row in rows:
        d = str(row.outcome_date)
        sp = normalize_species(row.species)
        if d not in daily:
            daily[d] = {"Dog": 0, "Cat": 0, "Other": 0}
        daily[d][sp] += row.adoptions

    # Build weekly totals
    weeks_out = []
    for week in WEEKS:
        start = date.fromisoformat(week["start"])
        end = date.fromisoformat(week["end"])
        dogs, cats, other = 0, 0, 0
        current = start
        while current <= end:
            day_data = daily.get(str(current), {})
            dogs += day_data.get("Dog", 0)
            cats += day_data.get("Cat", 0)
            other += day_data.get("Other", 0)
            current += timedelta(days=1)
        weeks_out.append({
            "label": week["label"],
            "start": week["start"],
            "end": week["end"],
            "total": dogs + cats + other,
            "dogs": dogs,
            "cats": cats,
            "other": other,
        })

    # Crescendo dates
    crescendo = {}
    for d in CRESCENDO_DATES:
        day_data = daily.get(d, {})
        dogs = day_data.get("Dog", 0)
        cats = day_data.get("Cat", 0)
        other = day_data.get("Other", 0)
        crescendo[d] = {"total": dogs + cats + other, "dogs": dogs, "cats": cats, "other": other}

    total_dogs = sum(w["dogs"] for w in weeks_out)
    total_cats = sum(w["cats"] for w in weeks_out)
    total_other = sum(w["other"] for w in weeks_out)

    output = {
        "lastUpdated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "eventYear": YEAR,
        "weeks": weeks_out,
        "crescendo": crescendo,
        "totals": {
            "total": total_dogs + total_cats + total_other,
            "dogs": total_dogs,
            "cats": total_cats,
            "other": total_other,
        },
    }

    os.makedirs("data", exist_ok=True)
    with open("data/adoptions.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"Done. Total adoptions: {output['totals']['total']}")


if __name__ == "__main__":
    run()
