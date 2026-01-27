from scheduler.gcal import list_events, create_event
import datetime

def test_auth_and_list():
    print("Testing GCal Auth & List...")
    try:
        events = list_events(limit=5)
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            print(f"{start} - {event['summary']}")
            
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_auth_and_list()
