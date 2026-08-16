"""Global fixtures for combustion integration."""
# Fixtures allow you to replace functions with a Mock object. You can perform
# many options via the Mock to reflect a particular behavior from the original
# function that you want to see without going through the function's actual logic.
# Fixtures can either be passed into tests as parameters, or if autouse=True, they
# will automatically be used across all tests.
#
# Fixtures that are defined in conftest.py are available across all tests. You can also
# define fixtures within a particular test file to scope them locally.
#
# pytest_homeassistant_custom_component provides some fixtures that are provided by
# Home Assistant core. You can find those fixture definitions here:
# https://github.com/MatthewFlamm/pytest-homeassistant-custom-component/blob/master/pytest_homeassistant_custom_component/common.py
#
# See here for more info: https://docs.pytest.org/en/latest/fixture.html (note that
# pytest includes fixtures OOB which you can use as defined on this page)

from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

pytest_plugins = "pytest_homeassistant_custom_component"

@pytest.fixture(autouse=True, scope="session")
def _mock_bt_history():
    """Stub BlueZ history: it calls into dbus_fast, absent on non-Linux dev boxes."""
    with patch("bluetooth_adapters.systems.linux.LinuxAdapters.history", {}):
        yield

@pytest.fixture(autouse=True)
def _mock_ha_scanner(mock_bleak_scanner_start):
    """Make the mocked HaScanner reach the binding bluetooth's setup actually uses.

    homeassistant.components.bluetooth does `from habluetooth import HaScanner`, a
    separate binding from `habluetooth.scanner.HaScanner`, which is what
    pytest_homeassistant_custom_component's `mock_bleak_scanner_start` fixture
    patches. Left unpatched, `enable_bluetooth`'s own "bluetooth" config entry
    setup constructs a real HaScanner -> BleakScanner, which selects a backend
    via the *unpatched* stdlib `platform.system()` (mock_bluetooth_adapters only
    patches `bluetooth_adapters.systems.platform`, a distinct reference) and
    reaches for dbus_fast, absent on non-Linux dev boxes. The resulting
    ConfigEntryNotReady is swallowed by config_entries, but BaseHaScanner already
    scheduled its expiry timer in HaScanner.async_setup(), so it lingers past
    teardown and fails pytest_homeassistant_custom_component's verify_cleanup.
    """
    import habluetooth.scanner as bluetooth_scanner  # noqa: PLC0415

    with patch("homeassistant.components.bluetooth.HaScanner", bluetooth_scanner.HaScanner):
        yield

@pytest.fixture(autouse=True)
def mock_bluetooth(_mock_bt_history, mock_bluetooth_adapters, _mock_ha_scanner, enable_bluetooth):
    """Auto mock bluetooth."""

# This fixture enables loading custom integrations in all tests.
# Remove to enable selective use of this fixture
@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Auto enable custom integrations."""
    yield


# This fixture is used to prevent HomeAssistant from attempting to create and dismiss persistent
# notifications. These calls would fail without this fixture since the persistent_notification
# integration is never loaded during a test.
@pytest.fixture(name="skip_notifications", autouse=True)
def skip_notifications_fixture():
    """Skip notification calls."""
    with patch("homeassistant.components.persistent_notification.async_create"), patch(
        "homeassistant.components.persistent_notification.async_dismiss"
    ):
        yield

@pytest.fixture()
def mock_config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Create a mock config entry and add it to hass."""
    entry = MockConfigEntry(title=None)
    entry.add_to_hass(hass)
    return entry
