from transform.transform_users import (
    build_person,
    build_employment,
    build_classification,
)


def test_build_person_normalizes_data():
    payload = {
        "firstName": "  John  ",
        "lastName": "  Doe ",
        "email": " JOHN@EXAMPLE.COM ",
        "age": 30,
    }

    result = build_person(1, payload)

    assert result is not None
    assert result["person_id"] == 1
    assert result["first_name"] == "John"
    assert result["last_name"] == "Doe"
    assert result["email"] == "john@example.com"


def test_build_person_missing_required_field():
    payload = {
        "firstName": "John",
        "lastName": "",
        "email": "john@example.com",
        "age": 30,
    }

    result = build_person(1, payload)

    assert result is None


def test_person_hash_is_deterministic():
    payload = {
        "firstName": "John",
        "lastName": "Doe",
        "email": "john@example.com",
        "age": 30,
    }

    result_1 = build_person(1, payload)
    result_2 = build_person(1, payload)

    assert result_1["row_hash"] == result_2["row_hash"]


def test_person_hash_changes_when_age_changes():
    payload_1 = {
        "firstName": "John",
        "lastName": "Doe",
        "email": "john@example.com",
        "age": 30,
    }

    payload_2 = {
        "firstName": "John",
        "lastName": "Doe",
        "email": "john@example.com",
        "age": 31,
    }

    result_1 = build_person(1, payload_1)
    result_2 = build_person(1, payload_2)

    assert result_1["row_hash"] != result_2["row_hash"]


def test_build_employment_extracts_company():
    payload = {
        "company": {
            "name": "Acme Corp",
            "department": "Engineering",
            "title": "Software Engineer",
        }
    }

    result = build_employment(1, payload)

    assert result is not None
    assert result["person_id"] == 1
    assert result["company_name"] == "Acme Corp"
    assert result["department"] == "Engineering"
    assert result["title"] == "Software Engineer"


def test_build_employment_missing_company():
    payload = {
        "company": {}
    }

    result = build_employment(1, payload)

    assert result is None


def test_build_classification_normalizes_role():
    payload = {
        "role": "  ADMIN  ",
        "company": {
            "department": "IT"
        }
    }

    result = build_classification(1, payload)

    assert result is not None
    assert result["role"] == "admin"
    assert result["department"] == "IT"


def test_build_classification_missing_role():
    payload = {
        "role": "",
        "company": {
            "department": "IT"
        }
    }

    result = build_classification(1, payload)

    assert result is None