"""Tests for Settings and Kill Switch API endpoints."""


def test_get_settings(client, auth_headers):
    """Test getting system settings."""
    res = client.get("/api/settings", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "killSwitch" in data
    assert data["killSwitch"] is False


def test_toggle_kill_switch(client, auth_headers):
    """Test enabling and disabling the emergency kill switch."""
    # Enable kill switch
    res1 = client.post(
        "/api/settings/kill-switch",
        json={"killSwitch": True},
        headers=auth_headers,
    )
    assert res1.status_code == 200
    assert res1.json()["killSwitch"] is True

    # Verify persisted in get_settings
    res2 = client.get("/api/settings", headers=auth_headers)
    assert res2.status_code == 200
    assert res2.json()["killSwitch"] is True

    # Disable kill switch
    res3 = client.post(
        "/api/settings/kill-switch",
        json={"killSwitch": False},
        headers=auth_headers,
    )
    assert res3.status_code == 200
    assert res3.json()["killSwitch"] is False
