from transform.transform_users import (
    _md5,
    build_person,
    build_employment,
    build_classification,
)


def test_same_person_data_produces_same_hash():
    payload = {
        "firstName": "Emily",
        "lastName": "Johnson",
        "email": "emily.johnson@example.com",
        "age": 29,
    }

    person_1 = build_person(1, payload)
    person_2 = build_person(1, payload)

    assert person_1["row_hash"] == person_2["row_hash"]


def test_changed_person_data_produces_different_hash():
    payload_1 = {
        "firstName": "Emily",
        "lastName": "Johnson",
        "email": "emily.johnson@example.com",
        "age": 29,
    }

    payload_2 = {
        "firstName": "Emily",
        "lastName": "Johnson",
        "email": "emily.johnson@example.com",
        "age": 30,
    }

    person_1 = build_person(1, payload_1)
    person_2 = build_person(1, payload_2)

    assert person_1["row_hash"] != person_2["row_hash"]


def test_age_change_changes_person_hash():
    payload_1 = {
        "firstName": "Emily",
        "lastName": "Johnson",
        "email": "emily.johnson@example.com",
        "age": 29,
    }

    payload_2 = {
        "firstName": "Emily",
        "lastName": "Johnson",
        "email": "emily.johnson@example.com",
        "age": 30,
    }

    person_1 = build_person(1, payload_1)
    person_2 = build_person(1, payload_2)

    assert person_1["row_hash"] != person_2["row_hash"]


def test_age_change_does_not_change_employment_hash():
    payload_1 = {
        "firstName": "Emily",
        "lastName": "Johnson",
        "email": "emily.johnson@example.com",
        "age": 29,
        "company": {
            "name": "Acme Corp",
            "department": "Engineering",
            "title": "Engineer",
        },
    }

    payload_2 = {
        "firstName": "Emily",
        "lastName": "Johnson",
        "email": "emily.johnson@example.com",
        "age": 30,
        "company": {
            "name": "Acme Corp",
            "department": "Engineering",
            "title": "Engineer",
        },
    }

    employment_1 = build_employment(1, payload_1)
    employment_2 = build_employment(1, payload_2)

    assert employment_1["row_hash"] == employment_2["row_hash"]


def test_age_change_does_not_change_classification_hash():
    payload_1 = {
        "firstName": "Emily",
        "lastName": "Johnson",
        "email": "emily.johnson@example.com",
        "age": 29,
        "role": "Admin",
        "company": {
            "department": "Engineering",
        },
    }

    payload_2 = {
        "firstName": "Emily",
        "lastName": "Johnson",
        "email": "emily.johnson@example.com",
        "age": 30,
        "role": "Admin",
        "company": {
            "department": "Engineering",
        },
    }

    classification_1 = build_classification(1, payload_1)
    classification_2 = build_classification(1, payload_2)

    assert classification_1["row_hash"] == classification_2["row_hash"]


def test_person_hash_matches_expected_md5_algorithm():
    payload = {
        "firstName": "Emily",
        "lastName": "Johnson",
        "email": "emily.johnson@example.com",
        "age": 29,
    }

    person = build_person(1, payload)

    expected_hash = _md5(
        "Emily|Johnson|emily.johnson@example.com|29"
    )

    assert person["row_hash"] == expected_hash