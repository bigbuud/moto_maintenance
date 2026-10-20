"""Constanten voor Moto Onderhoud."""

from homeassistant.const import Platform

DOMAIN = "moto_onderhoud"

PLATFORMS = [Platform.SENSOR, Platform.NUMBER, Platform.TEXT, Platform.BUTTON]

STORAGE_VERSION = 1

CONF_ODOMETER = "odometer"
CONF_NOTIFY_SERVICE = "notify_service"
CONF_WARN_KM = "warn_km"
CONF_WARN_DAYS = "warn_days"

DEFAULT_WARN_KM = 300
DEFAULT_WARN_DAYS = 14

STATUS_OK = "ok"
STATUS_SOON = "binnenkort"
STATUS_OVERDUE = "achterstallig"
STATUS_UNKNOWN = "onbekend"
STATUSES = [STATUS_OK, STATUS_SOON, STATUS_OVERDUE, STATUS_UNKNOWN]

EVENT_TASK_DUE = f"{DOMAIN}_task_due"

# key, naam, interval km, interval maanden, icoon
# Voorbeeldwaarden: controleer het onderhoudsboekje van je motor.
DEFAULT_TASKS: list[tuple[str, str, int, int, str]] = [
    ("olie", "Olie vervangen", 6000, 12, "mdi:oil"),
    ("oliefilter", "Oliefilter vervangen", 6000, 12, "mdi:filter-cog"),
    ("ketting_bijstellen", "Ketting bijstellen", 1000, 3, "mdi:link-variant"),
    ("ketting_smeren", "Ketting insmeren", 500, 2, "mdi:spray"),
    ("luchtfilter", "Luchtfilter", 12000, 24, "mdi:air-filter"),
    ("bougies", "Bougies", 12000, 24, "mdi:flash"),
    ("groot_onderhoud", "Groot onderhoud (dealer)", 12000, 12, "mdi:wrench-cog"),
]
