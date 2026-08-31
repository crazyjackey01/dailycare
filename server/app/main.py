from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

from app.mock_data import past_records, today_record, consecutive_abnormal_days
from app.analyzer import analyze_pattern, generate_rule_based_message
from app.ollama_client import build_prompt, ask_ollama


app = FastAPI(title="DailyCare API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


beacon_events = []
sensor_events = []


BEACON_ZONE_MAP = {
    "BED_01": "bedroom",
    "KITCHEN_01": "kitchen",
    "DOOR_01": "frontDoor",
    "BATH_01": "bathroom",
    "LIVING_01": "livingRoom",
}


class BeaconEvent(BaseModel):
    beaconId: str
    rssi: int
    timestamp: str | None = None


class SensorEvent(BaseModel):
    sensorId: str
    zone: str
    eventType: str
    value: float | int | None = None
    timestamp: str | None = None


@app.get("/")
def root():
    return {"message": "DailyCare backend is running"}


def build_today_record_from_beacons(events):
    today = {
        "date": datetime.now().date().isoformat(),
        "kitchen": 0,
        "frontDoor": 0,
        "bedroom": 0,
        "bathroom": 0,
        "livingRoom": 0,
    }

    if len(events) < 2:
        return None

    sorted_events = sorted(
        events,
        key=lambda e: datetime.fromisoformat(e["timestamp"]),
    )

    for i in range(len(sorted_events) - 1):
        current_event = sorted_events[i]
        next_event = sorted_events[i + 1]

        current_zone = current_event.get("zone")

        if current_zone not in today:
            continue

        current_time = datetime.fromisoformat(current_event["timestamp"])
        next_time = datetime.fromisoformat(next_event["timestamp"])

        duration_minutes = (next_time - current_time).total_seconds() / 60

        if duration_minutes <= 0:
            continue

        duration_minutes = min(duration_minutes, 30)
        today[current_zone] += round(duration_minutes, 2)

    return today


def build_today_record_from_sensors(events):
    today = {
        "date": datetime.now().date().isoformat(),
        "kitchen": 0,
        "frontDoor": 0,
        "bedroom": 0,
        "bathroom": 0,
        "livingRoom": 0,
    }

    if not events:
        return None

    for event in events:
        zone = event.get("zone")
        event_type = event.get("eventType")

        if zone not in today:
            continue

        if event_type == "presence" and zone == "bedroom":
            today[zone] += 5

        elif event_type == "motion":
            today[zone] += 5

        elif event_type in ["meal", "door", "bathroom"]:
            today[zone] += 10

    return today


@app.get("/summary")
def get_summary(use_ollama: bool = False):
    sensor_today_record = build_today_record_from_sensors(sensor_events)
    beacon_today_record = build_today_record_from_beacons(beacon_events)

    if sensor_today_record:
        active_today_record = sensor_today_record
        data_source = "sensor"
    elif beacon_today_record:
        active_today_record = beacon_today_record
        data_source = "beacon"
    else:
        active_today_record = today_record
        data_source = "mock"

    result = analyze_pattern(
        today=active_today_record,
        past_records=past_records,
        consecutive_abnormal_days=consecutive_abnormal_days,
    )

    rule_message = generate_rule_based_message(result)

    ollama_message = None
    message_mode = "rule-based"
    final_message = rule_message

    if use_ollama:
        try:
            prompt = build_prompt(result)
            ollama_message = ask_ollama(prompt)

            if ollama_message:
                final_message = ollama_message
                message_mode = "ollama"

        except Exception:
            ollama_message = None
            message_mode = "rule-based"
            final_message = rule_message

    return {
        "analysis": result,
        "dataSource": data_source,
        "activeTodayRecord": active_today_record,
        "messageMode": message_mode,
        "message": final_message,
        "ruleBasedMessage": rule_message,
        "ollamaMessage": ollama_message,
    }


@app.post("/beacon")
def receive_beacon(event: BeaconEvent):
    zone = BEACON_ZONE_MAP.get(event.beaconId, "unknown")

    saved_event = {
        "beaconId": event.beaconId,
        "zone": zone,
        "rssi": event.rssi,
        "timestamp": event.timestamp or datetime.now().isoformat(),
    }

    beacon_events.append(saved_event)

    return {
        "status": "saved",
        "event": saved_event,
    }


@app.get("/beacon/events")
def get_beacon_events():
    return {
        "count": len(beacon_events),
        "events": beacon_events[-50:],
    }


@app.post("/sensor")
def receive_sensor(event: SensorEvent):
    saved_event = {
        "sensorId": event.sensorId,
        "zone": event.zone,
        "eventType": event.eventType,
        "value": event.value,
        "timestamp": event.timestamp or datetime.now().isoformat(),
    }

    sensor_events.append(saved_event)

    return {
        "status": "saved",
        "event": saved_event,
    }


@app.get("/sensor/events")
def get_sensor_events():
    return {
        "count": len(sensor_events),
        "events": sensor_events[-50:],
    }


@app.delete("/sensor/events")
def clear_sensor_events():
    sensor_events.clear()

    return {
        "status": "cleared",
        "count": 0,
    }


@app.delete("/beacon/events")
def clear_beacon_events():
    beacon_events.clear()

    return {
        "status": "cleared",
        "count": 0,
    }
