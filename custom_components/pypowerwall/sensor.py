from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfPower, UnitOfTime, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PowerwallCoordinator


@dataclass(frozen=True, kw_only=True)
class PowerwallSensorEntityDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], float | str | None]


def _agg(meter: str, field: str) -> Callable[[dict[str, Any]], float | None]:
    def fn(data: dict[str, Any]) -> float | None:
        agg = data.get("aggregates")
        if not agg:
            return None
        return agg.get(meter, {}).get(field)

    return fn


def _agg_wh_to_kwh(meter: str, field: str) -> Callable[[dict[str, Any]], float | None]:
    """Return Wh field converted to kWh. The gateway API returns cumulative energy in Wh."""
    def fn(data: dict[str, Any]) -> float | None:
        agg = data.get("aggregates")
        if not agg:
            return None
        raw = agg.get(meter, {}).get(field)
        if raw is None:
            return None
        return raw / 1000

    return fn


SENSOR_DESCRIPTIONS: tuple[PowerwallSensorEntityDescription, ...] = (
    # ── Power sensors (W, measurement) ──────────────────────────────────────
    PowerwallSensorEntityDescription(
        key="grid_power",
        name="Grid Power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=_agg("site", "instant_power"),
    ),
    PowerwallSensorEntityDescription(
        key="solar_power",
        name="Solar Power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=_agg("solar", "instant_power"),
    ),
    PowerwallSensorEntityDescription(
        key="battery_power",
        name="Battery Power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=_agg("battery", "instant_power"),
    ),
    PowerwallSensorEntityDescription(
        key="home_power",
        name="Home Consumption",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=_agg("load", "instant_power"),
    ),
    # ── Energy sensors (kWh, total_increasing) ── for HA Energy Dashboard ──
    # Gateway returns cumulative energy in Wh; _agg_wh_to_kwh divides by 1000.
    PowerwallSensorEntityDescription(
        key="grid_energy_imported",
        name="Grid Energy Imported",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=_agg_wh_to_kwh("site", "energy_imported"),
    ),
    PowerwallSensorEntityDescription(
        key="grid_energy_exported",
        name="Grid Energy Exported",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=_agg_wh_to_kwh("site", "energy_exported"),
    ),
    PowerwallSensorEntityDescription(
        key="solar_energy_generated",
        name="Solar Energy Generated",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=_agg_wh_to_kwh("solar", "energy_exported"),
    ),
    PowerwallSensorEntityDescription(
        key="battery_energy_charged",
        name="Battery Energy Charged",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=_agg_wh_to_kwh("battery", "energy_imported"),
    ),
    PowerwallSensorEntityDescription(
        key="battery_energy_discharged",
        name="Battery Energy Discharged",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=_agg_wh_to_kwh("battery", "energy_exported"),
    ),
    PowerwallSensorEntityDescription(
        key="home_energy_consumed",
        name="Home Energy Consumed",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=_agg_wh_to_kwh("load", "energy_imported"),
    ),
    # ── Other sensors ────────────────────────────────────────────────────────
    PowerwallSensorEntityDescription(
        key="battery_level",
        name="Battery Level",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda d: d.get("level"),
    ),
    PowerwallSensorEntityDescription(
        key="grid_status",
        name="Grid Status",
        device_class=None,
        state_class=None,
        native_unit_of_measurement=None,
        value_fn=lambda d: d.get("grid_status"),
    ),
    PowerwallSensorEntityDescription(
        key="backup_time_remaining",
        name="Backup Time Remaining",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.HOURS,
        value_fn=lambda d: d.get("time_remaining"),
    ),
    PowerwallSensorEntityDescription(
        key="battery_reserve",
        name="Battery Reserve",
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda d: d.get("reserve"),
    ),
    PowerwallSensorEntityDescription(
        key="battery_mode",
        name="Battery Mode",
        device_class=None,
        state_class=None,
        native_unit_of_measurement=None,
        value_fn=lambda d: d.get("mode"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PowerwallCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        PowerwallSensor(coordinator, description) for description in SENSOR_DESCRIPTIONS
    )


class PowerwallSensor(CoordinatorEntity[PowerwallCoordinator], SensorEntity):
    entity_description: PowerwallSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PowerwallCoordinator,
        description: PowerwallSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"

    @property
    def native_value(self) -> float | str | None:
        return self.entity_description.value_fn(self.coordinator.data)
