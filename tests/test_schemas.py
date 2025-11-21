# tests/test_schemas.py
import pytest
from datetime import date, time

from app.schemas.one_time_session import OneTimeSessionCreate, OneTimeSessionUpdate
from app.schemas.override import OverrideModify


def test_one_time_session_invalid_datetime_range():
    """Test that end before start is rejected"""
    with pytest.raises(ValueError, match="End datetime must be after start"):
        OneTimeSessionCreate(
            title="Invalid Session",
            notes=None,
            start_date=date(2025, 12, 1),
            start_time=time(15, 0),
            end_date=date(2025, 12, 1),
            end_time=time(14, 0),  # Before start!
        )


def test_one_time_session_same_datetime_rejected():
    """Test that start == end is rejected"""
    with pytest.raises(ValueError, match="End datetime must be after start"):
        OneTimeSessionCreate(
            title="Zero Duration",
            notes=None,
            start_date=date(2025, 12, 1),
            start_time=time(15, 0),
            end_date=date(2025, 12, 1),
            end_time=time(15, 0),  # Same as start!
        )


def test_one_time_update_partial_datetime_rejected():
    """Test that partial datetime update is rejected"""
    with pytest.raises(ValueError, match="Must provide all datetime fields"):
        OneTimeSessionUpdate(
            start_date=date(2025, 12, 1),
            # Missing start_time, end_date, end_time
        )


def test_override_modify_requires_changes():
    """Test that modify override needs at least one change"""
    with pytest.raises(ValueError, match="Must provide at least one modification"):
        OverrideModify(
            occurrence_date=date(2025, 12, 1),
            # No modifications!
        )


def test_override_modify_invalid_time_range():
    """Test that modified times must be valid"""
    with pytest.raises(ValueError, match="modified_end_time must be after modified_start_time"):
        OverrideModify(
            occurrence_date=date(2025, 12, 1),
            modified_start_time=time(15, 0),
            modified_end_time=time(14, 0),  # Before start!
            # No modified_end_date, so same-day validation applies
        )


def test_override_modify_overnight_allowed():
    """Test that overnight modification is allowed with end_date"""
    # Should NOT raise
    override = OverrideModify(
        occurrence_date=date(2025, 12, 1),
        modified_start_time=time(22, 0),
        modified_end_time=time(6, 0),  # Before start, but...
        modified_end_date=date(2025, 12, 2),  # ...next day!
    )
    assert override.modified_end_date == date(2025, 12, 2)
