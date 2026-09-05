import sys
import os

# Let Python find modules inside src/extract, src/transform, src/load, src/validate
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from extract.extract_users import run_extract
from transform.transform_users import transform_batch
from load.load_warehouse import load_person, load_employment, load_classification
from validate.data_quality import (
    check_no_nulls, check_uniqueness, check_referential_integrity, check_range
)


def run_validation():
    results = [
        check_no_nulls("warehouse.person", "email"),
        check_no_nulls("warehouse.person", "first_name"),
        check_no_nulls("warehouse.employment", "company_name"),
        check_no_nulls("warehouse.classification", "role"),
        check_uniqueness("warehouse.person", "person_id"),
        check_uniqueness("warehouse.person", "email"),
        check_referential_integrity("warehouse.employment", "person_id", "warehouse.person", "person_id"),
        check_referential_integrity("warehouse.classification", "person_id", "warehouse.person", "person_id"),
        check_range("warehouse.person", "age", 0, 120),
    ]
    if not all(results):
        raise RuntimeError("One or more data quality checks failed.")
    print("\nAll data quality checks passed.")


if __name__ == "__main__":
    print("=== EXTRACT ===")
    batch_id = run_extract()

    print("\n=== TRANSFORM ===")
    people, employment, classification = transform_batch(batch_id)

    print("\n=== LOAD ===")
    load_person(people)
    load_employment(employment)
    load_classification(classification)

    print("\n=== VALIDATE ===")
    run_validation()

    print(f"\nPipeline run complete. batch_id={batch_id}")