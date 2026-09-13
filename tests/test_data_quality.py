import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from validate.data_quality import (
    check_no_nulls,
    check_uniqueness,
    check_referential_integrity,
    check_range,
)


class FakeResult:
    def __init__(self, value):
        self.value = value

    def scalar(self):
        return self.value


class FakeConnection:
    def __init__(self, value):
        self.value = value

    def execute(self, *args, **kwargs):
        return FakeResult(self.value)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass


class FakeEngine:
    def __init__(self, value):
        self.value = value

    def connect(self):
        return FakeConnection(self.value)


def test_no_nulls_passes_when_no_nulls_exist(monkeypatch):
    monkeypatch.setattr(
        "validate.data_quality.engine",
        FakeEngine(0),
    )

    assert check_no_nulls("warehouse.person", "email") is True


def test_no_nulls_fails_when_nulls_exist(monkeypatch):
    monkeypatch.setattr(
        "validate.data_quality.engine",
        FakeEngine(2),
    )

    assert check_no_nulls("warehouse.person", "email") is False


def test_uniqueness_passes_when_no_duplicates_exist(monkeypatch):
    monkeypatch.setattr(
        "validate.data_quality.engine",
        FakeEngine(0),
    )

    assert check_uniqueness("warehouse.person", "email") is True


def test_uniqueness_fails_when_duplicates_exist(monkeypatch):
    monkeypatch.setattr(
        "validate.data_quality.engine",
        FakeEngine(1),
    )

    assert check_uniqueness("warehouse.person", "email") is False


def test_referential_integrity_passes_when_no_orphans_exist(monkeypatch):
    monkeypatch.setattr(
        "validate.data_quality.engine",
        FakeEngine(0),
    )

    assert check_referential_integrity(
        "warehouse.employment",
        "person_id",
        "warehouse.person",
        "person_id",
    ) is True


def test_referential_integrity_fails_when_orphans_exist(monkeypatch):
    monkeypatch.setattr(
        "validate.data_quality.engine",
        FakeEngine(1),
    )

    assert check_referential_integrity(
        "warehouse.employment",
        "person_id",
        "warehouse.person",
        "person_id",
    ) is False


def test_range_check_passes_when_all_values_are_valid(monkeypatch):
    monkeypatch.setattr(
        "validate.data_quality.engine",
        FakeEngine(0),
    )

    assert check_range(
        "warehouse.person",
        "age",
        0,
        120,
    ) is True


def test_range_check_fails_when_invalid_values_exist(monkeypatch):
    monkeypatch.setattr(
        "validate.data_quality.engine",
        FakeEngine(1),
    )

    assert check_range(
        "warehouse.person",
        "age",
        0,
        120,
    ) is False