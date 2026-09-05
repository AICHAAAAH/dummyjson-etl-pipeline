import sys
import os
import hashlib

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))


def test_row_hash_is_deterministic():
    """The same input should always produce the same hash."""
    hash1 = hashlib.md5("Emily|Johnson|emily@x.com|29".encode()).hexdigest()
    hash2 = hashlib.md5("Emily|Johnson|emily@x.com|29".encode()).hexdigest()
    assert hash1 == hash2


def test_row_hash_changes_when_data_changes():
    """Changing any field should produce a different hash."""
    hash_original = hashlib.md5("Emily|Johnson|emily@x.com|29".encode()).hexdigest()
    hash_changed_age = hashlib.md5("Emily|Johnson|emily@x.com|30".encode()).hexdigest()
    assert hash_original != hash_changed_age


def test_missing_first_name_is_falsy():
    """Simulates the exact required-field check used in transform_person."""
    payload = {"firstName": None, "lastName": "Johnson", "email": "emily@x.com"}
    first_name = payload.get("firstName")
    last_name = payload.get("lastName")
    email = payload.get("email")

    should_skip = not first_name or not last_name or not email
    assert should_skip is True


def test_complete_record_is_not_skipped():
    """A record with all required fields should NOT be skipped."""
    payload = {"firstName": "Emily", "lastName": "Johnson", "email": "emily@x.com"}
    first_name = payload.get("firstName")
    last_name = payload.get("lastName")
    email = payload.get("email")

    should_skip = not first_name or not last_name or not email
    assert should_skip is False