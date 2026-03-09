"""
Tests for the settings repository and /network/settings API endpoints.

Covers:
- get_all returns defaults when database is empty
- get_all merges stored values over defaults
- upsert_all inserts new keys
- upsert_all updates existing keys
- GET /network/settings returns full settings dict
- PUT /network/settings persists and returns updated values
- Auto-derive logic (50% / 20% of contracted speed)
"""

import pytest
from repositories import settings_repository as repo
from conftest import make_setting


# ── Repository unit tests ──────────────────────────────────────────────────────

class TestSettingsRepository:

    def test_get_all_returns_defaults_when_empty(self, db):
        result = repo.get_all(db)
        assert result["subscriber_provider"] == "Drei Austria GmbH"
        assert result["contracted_download_mbps"] == "150.0"
        assert result["download_degraded_mbps"] == "75.0"
        assert result["download_critical_mbps"] == "30.0"

    def test_get_all_contains_all_expected_keys(self, db):
        result = repo.get_all(db)
        expected_keys = {
            "subscriber_name", "subscriber_address", "subscriber_account_number",
            "subscriber_email", "subscriber_phone", "subscriber_plan",
            "subscriber_provider", "contracted_download_mbps", "contracted_upload_mbps",
            "download_degraded_mbps", "download_critical_mbps",
            "upload_degraded_mbps", "upload_critical_mbps",
        }
        assert expected_keys.issubset(result.keys())

    def test_stored_value_overrides_default(self, db):
        make_setting(db, "subscriber_name", "Veselin Todorov")
        result = repo.get_all(db)
        assert result["subscriber_name"] == "Veselin Todorov"

    def test_unset_keys_still_return_defaults(self, db):
        make_setting(db, "subscriber_name", "Veselin Todorov")
        result = repo.get_all(db)
        # Only subscriber_name was set; others should still be defaults
        assert result["subscriber_provider"] == "Drei Austria GmbH"

    def test_get_single_key_returns_value(self, db):
        make_setting(db, "subscriber_email", "test@example.com")
        assert repo.get(db, "subscriber_email") == "test@example.com"

    def test_get_missing_key_returns_default(self, db):
        assert repo.get(db, "download_degraded_mbps") == "75.0"

    def test_get_completely_unknown_key_returns_none(self, db):
        assert repo.get(db, "nonexistent_key") is None

    def test_upsert_all_inserts_new_values(self, db):
        from models.settings import Setting
        repo.upsert_all(db, {"subscriber_name": "Test User"})
        row = db.query(Setting).filter(Setting.key == "subscriber_name").first()
        assert row is not None
        assert row.value == "Test User"

    def test_upsert_all_updates_existing_value(self, db):
        make_setting(db, "subscriber_name", "Old Name")
        repo.upsert_all(db, {"subscriber_name": "New Name"})
        result = repo.get(db, "subscriber_name")
        assert result == "New Name"

    def test_upsert_all_partial_update_does_not_wipe_other_keys(self, db):
        make_setting(db, "subscriber_name", "Veselin")
        make_setting(db, "subscriber_email", "v@example.com")
        repo.upsert_all(db, {"subscriber_name": "Updated"})
        assert repo.get(db, "subscriber_email") == "v@example.com"

    def test_upsert_all_returns_full_settings_dict(self, db):
        result = repo.upsert_all(db, {"subscriber_name": "Veselin"})
        assert "download_degraded_mbps" in result
        assert result["subscriber_name"] == "Veselin"

    def test_numeric_values_stored_as_strings(self, db):
        repo.upsert_all(db, {"contracted_download_mbps": 200.0})
        result = repo.get(db, "contracted_download_mbps")
        assert result == "200.0"


# ── API endpoint tests ─────────────────────────────────────────────────────────

class TestSettingsEndpoints:

    def test_get_settings_returns_200(self, client):
        response = client.get("/network/settings")
        assert response.status_code == 200

    def test_get_settings_returns_all_keys(self, client):
        data = client.get("/network/settings").json()
        assert "subscriber_name" in data
        assert "download_degraded_mbps" in data
        assert "contracted_download_mbps" in data

    def test_get_settings_defaults_on_empty_db(self, client):
        data = client.get("/network/settings").json()
        assert data["subscriber_provider"] == "Drei Austria GmbH"
        assert data["download_degraded_mbps"] == "75.0"

    def test_put_settings_returns_200(self, client):
        response = client.put("/network/settings", json={"subscriber_name": "Veselin"})
        assert response.status_code == 200

    def test_put_settings_persists_value(self, client):
        client.put("/network/settings", json={"subscriber_name": "Veselin Todorov"})
        data = client.get("/network/settings").json()
        assert data["subscriber_name"] == "Veselin Todorov"

    def test_put_settings_partial_update(self, client):
        client.put("/network/settings", json={
            "subscriber_name": "Veselin",
            "subscriber_email": "v@example.com",
        })
        client.put("/network/settings", json={"subscriber_name": "Updated"})
        data = client.get("/network/settings").json()
        assert data["subscriber_name"] == "Updated"
        assert data["subscriber_email"] == "v@example.com"

    def test_put_settings_returns_full_dict(self, client):
        data = client.put("/network/settings", json={"subscriber_name": "X"}).json()
        assert "download_degraded_mbps" in data
        assert "contracted_download_mbps" in data

    def test_threshold_auto_derive_50_pct(self, client):
        """50% of contracted download should equal degraded threshold."""
        client.put("/network/settings", json={
            "contracted_download_mbps": "200.0",
            "download_degraded_mbps": "100.0",   # 50% of 200
            "download_critical_mbps": "40.0",    # 20% of 200
        })
        data = client.get("/network/settings").json()
        assert float(data["download_degraded_mbps"]) == pytest.approx(100.0)
        assert float(data["download_critical_mbps"]) == pytest.approx(40.0)