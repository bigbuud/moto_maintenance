"""Gegevens, berekeningen en meldingen voor Moto Onderhoud."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    CONF_NOTIFY_SERVICE,
    CONF_ODOMETER,
    CONF_WARN_DAYS,
    CONF_WARN_KM,
    DEFAULT_TASKS,
    DEFAULT_WARN_DAYS,
    DEFAULT_WARN_KM,
    DOMAIN,
    EVENT_TASK_DUE,
    STATUS_OK,
    STATUS_OVERDUE,
    STATUS_SOON,
    STATUS_UNKNOWN,
    STORAGE_VERSION,
)

_LOGGER = logging.getLogger(__name__)

DAYS_PER_MONTH = 30.4375


@dataclass
class Task:
    """Een onderhoudstaak."""

    key: str
    name: str
    icon: str
    interval_km: int
    interval_months: int
    last_km: float = 0.0
    last_date: str | None = None
    note: str = ""


@dataclass
class TaskState:
    """Berekende toestand van een taak."""

    status: str
    km_remaining: float | None
    days_remaining: int | None


class MotoManager:
    """Beheert kilometerstand, taken, opslag en meldingen van één motor."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._store: Store = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}"
        )
        self.odometer: float = float(entry.data.get(CONF_ODOMETER, 0) or 0)
        self.tasks: dict[str, Task] = {}
        self._last_status: dict[str, str] = {}
        self._unsubs: list = []

    # ---------- opties ----------
    @property
    def signal(self) -> str:
        return f"{DOMAIN}_update_{self.entry.entry_id}"

    @property
    def warn_km(self) -> float:
        return float(self.entry.options.get(CONF_WARN_KM, DEFAULT_WARN_KM))

    @property
    def warn_days(self) -> int:
        return int(self.entry.options.get(CONF_WARN_DAYS, DEFAULT_WARN_DAYS))

    @property
    def notify_service(self) -> str:
        return (self.entry.options.get(CONF_NOTIFY_SERVICE) or "").strip()

    # ---------- opslag ----------
    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        if "odometer" in data:
            self.odometer = float(data["odometer"])
        saved = data.get("tasks", {})
        for key, name, km, months, icon in DEFAULT_TASKS:
            s = saved.get(key, {})
            self.tasks[key] = Task(
                key=key,
                name=name,
                icon=icon,
                interval_km=int(s.get("interval_km", km)),
                interval_months=int(s.get("interval_months", months)),
                last_km=float(s.get("last_km", 0)),
                last_date=s.get("last_date"),
                note=str(s.get("note", "")),
            )
        self._last_status = {k: self.state(t).status for k, t in self.tasks.items()}

    def _data_to_save(self) -> dict[str, Any]:
        return {
            "odometer": self.odometer,
            "tasks": {
                k: {
                    "interval_km": t.interval_km,
                    "interval_months": t.interval_months,
                    "last_km": t.last_km,
                    "last_date": t.last_date,
                    "note": t.note,
                }
                for k, t in self.tasks.items()
            },
        }

    async def async_flush(self) -> None:
        await self._store.async_save(self._data_to_save())

    # ---------- levenscyclus ----------
    @callback
    def async_start(self) -> None:
        self._unsubs.append(
            async_track_time_change(
                self.hass, self._daily_refresh, hour=0, minute=5, second=0
            )
        )
        self._unsubs.append(
            async_track_time_change(
                self.hass, self._daily_reminder, hour=9, minute=0, second=0
            )
        )

    @callback
    def async_stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()

    # ---------- berekening ----------
    def state(self, task: Task) -> TaskState:
        if not task.last_date:
            return TaskState(STATUS_UNKNOWN, None, None)

        km_rem: float | None = None
        if task.interval_km > 0:
            km_rem = task.last_km + task.interval_km - self.odometer

        days_rem: int | None = None
        if task.interval_months > 0:
            try:
                last = date.fromisoformat(task.last_date)
            except ValueError:
                return TaskState(STATUS_UNKNOWN, None, None)
            due = last + timedelta(days=round(task.interval_months * DAYS_PER_MONTH))
            days_rem = (due - dt_util.now().date()).days

        overdue = (km_rem is not None and km_rem <= 0) or (
            days_rem is not None and days_rem <= 0
        )
        soon = (km_rem is not None and km_rem <= self.warn_km) or (
            days_rem is not None and days_rem <= self.warn_days
        )
        if overdue:
            status = STATUS_OVERDUE
        elif soon:
            status = STATUS_SOON
        else:
            status = STATUS_OK
        return TaskState(status, km_rem, days_rem)

    # ---------- wijzigingen ----------
    @callback
    def _changed(self) -> None:
        self._store.async_delay_save(self._data_to_save, 1)
        self._check_transitions()
        async_dispatcher_send(self.hass, self.signal)

    @callback
    def set_odometer(self, value: float) -> None:
        self.odometer = float(value)
        self._changed()

    @callback
    def set_interval_km(self, key: str, value: float) -> None:
        self.tasks[key].interval_km = int(value)
        self._changed()

    @callback
    def set_interval_months(self, key: str, value: float) -> None:
        self.tasks[key].interval_months = int(value)
        self._changed()

    @callback
    def set_note(self, key: str, value: str) -> None:
        self.tasks[key].note = value
        self._changed()

    @callback
    def register(
        self,
        key: str,
        km: float | None = None,
        when: date | None = None,
        note: str | None = None,
    ) -> None:
        """Registreer uitgevoerd onderhoud."""
        task = self.tasks[key]
        km_val = float(km) if km is not None else self.odometer
        if km_val > self.odometer:
            self.odometer = km_val
        task.last_km = km_val
        task.last_date = (when or dt_util.now().date()).isoformat()
        if note is not None:
            task.note = note
        self._changed()

    # ---------- meldingen ----------
    @callback
    def _daily_refresh(self, _now: datetime) -> None:
        self._changed()

    @callback
    def _daily_reminder(self, _now: datetime) -> None:
        overdue = [
            t.name
            for t in self.tasks.values()
            if self.state(t).status == STATUS_OVERDUE
        ]
        if overdue:
            self.hass.async_create_task(
                self._async_notify("Moto onderhoud achterstallig", ", ".join(overdue))
            )

    @callback
    def _check_transitions(self) -> None:
        for key, task in self.tasks.items():
            st = self.state(task)
            previous = self._last_status.get(key)
            self._last_status[key] = st.status
            if st.status == previous or st.status not in (STATUS_SOON, STATUS_OVERDUE):
                continue
            km = None if st.km_remaining is None else round(st.km_remaining)
            self.hass.bus.async_fire(
                EVENT_TASK_DUE,
                {
                    "entry_id": self.entry.entry_id,
                    "motor": self.entry.title,
                    "task": key,
                    "name": task.name,
                    "status": st.status,
                    "km_remaining": km,
                    "days_remaining": st.days_remaining,
                },
            )
            parts = []
            if km is not None:
                parts.append(f"{km} km")
            if st.days_remaining is not None:
                parts.append(f"{st.days_remaining} dagen")
            detail = f" ({', '.join(parts)})" if parts else ""
            self.hass.async_create_task(
                self._async_notify(
                    f"Moto onderhoud: {self.entry.title}",
                    f"{task.name} is {st.status}{detail}",
                )
            )

    async def _async_notify(self, title: str, message: str) -> None:
        service = self.notify_service.removeprefix("notify.")
        if not service:
            return
        if not self.hass.services.has_service("notify", service):
            _LOGGER.warning("Notify-service notify.%s bestaat niet", service)
            return
        try:
            await self.hass.services.async_call(
                "notify", service, {"title": title, "message": message}
            )
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Melding versturen via notify.%s mislukt", service)
