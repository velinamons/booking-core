import pytest


@pytest.mark.asyncio
class TestCalendarEndpoints:
    """Test calendar API endpoints"""

    async def test_get_calendar_empty(self, client):
        """Test getting empty calendar"""
        response = await client.get(
            "/api/v1/calendar/sessions", params={"start_date": "2025-12-01", "end_date": "2025-12-07"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["sessions"] == []

    async def test_get_calendar_with_sessions(self, client, sample_one_time_session_data):
        """Test getting calendar with sessions"""
        # Create session
        await client.post("/api/v1/sessions/one-time", json=sample_one_time_session_data)

        # Get calendar
        response = await client.get(
            "/api/v1/calendar/sessions", params={"start_date": "2025-11-24", "end_date": "2025-11-30"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert len(data["sessions"]) == 1
        assert data["sessions"][0]["title"] == "Team Meeting"

    async def test_calendar_validation_invalid_range(self, client):
        """Test that end_date < start_date is rejected"""
        response = await client.get(
            "/api/v1/calendar/sessions",
            params={
                "start_date": "2025-12-31",
                "end_date": "2025-12-01",  # Before start!
            },
        )

        # Should return 422 validation error
        assert response.status_code == 422

    async def test_calendar_recurring_with_override(self, client, sample_recurring_session_data):
        """Integration test: recurring session with cancel and modify"""
        # Create recurring session
        response = await client.post("/api/v1/sessions/recurring", json=sample_recurring_session_data)
        session_id = response.json()["id"]

        # Cancel one instance
        await client.post(
            f"/api/v1/sessions/recurring/{session_id}/overrides/cancel", json={"occurrence_date": "2025-12-01"}
        )

        # Modify another instance
        await client.post(
            f"/api/v1/sessions/recurring/{session_id}/overrides/modify",
            json={"occurrence_date": "2025-12-08", "modified_start_time": "10:00:00", "modified_end_time": "11:00:00"},
        )

        # Get calendar for December
        response = await client.get(
            "/api/v1/calendar/sessions", params={"start_date": "2025-11-24", "end_date": "2025-12-31"}
        )

        data = response.json()
        sessions = data["sessions"]

        # Find modified instance
        modified = next(s for s in sessions if s["start_date"] == "2025-12-08")
        assert modified["start_time"] == "10:00:00"
        assert modified["is_modified"] is True

        # Verify cancelled instance NOT present
        cancelled_dates = [s["start_date"] for s in sessions]
        assert "2025-12-01" not in cancelled_dates
