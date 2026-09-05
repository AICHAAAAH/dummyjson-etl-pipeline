import sys
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

sys.path.append("/opt/airflow/src")

from extract.extract_users import run_extract
from transform.transform_users import transform_batch
from load.load_warehouse import load_person, load_employment, load_classification
from validate.data_quality import (
    check_no_nulls, check_uniqueness, check_referential_integrity, check_range
)


def extract_task(**context):
    batch_id = run_extract()
    context["ti"].xcom_push(key="batch_id", value=batch_id)


def transform_load_task(**context):
    batch_id = context["ti"].xcom_pull(key="batch_id", task_ids="extract")
    people, employment, classification = transform_batch(batch_id)
    load_person(people)
    load_employment(employment)
    load_classification(classification)


def validate_task(**context):
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


default_args = {
    "owner": "aicha",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="dummyjson_etl_pipeline",
    description="Person/Employment/Classification ingestion from DummyJSON API",
    default_args=default_args,
    schedule_interval="0 2 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["etl", "portfolio"],
) as dag:

    extract = PythonOperator(task_id="extract", python_callable=extract_task)
    transform_load = PythonOperator(task_id="transform_load", python_callable=transform_load_task)
    validate = PythonOperator(task_id="validate", python_callable=validate_task)

    extract >> transform_load >> validate