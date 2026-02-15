import requests
from django.conf import settings

def create_daily_room():
    """
    Create a new room on Daily.co and return the room URL.
    """
    api_key = settings.DAILY_API_KEY
    if not api_key:
        raise ValueError("DAILY_API_KEY is not set in settings")

    url = "https://api.daily.co/v1/rooms"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "properties": {
            "enable_chat": True,
            "enable_screenshare": True,
            "enable_recording": "cloud"
        }
    }

    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        room_data = response.json()
        return room_data.get('url')
    else:
        raise Exception(f"Failed to create Daily room: {response.status_code} - {response.text}")


def get_room_recordings(room_url):
    """
    Get recordings for a specific room.
    """
    api_key = settings.DAILY_API_KEY
    if not api_key:
        return []

    # Extract room name from URL
    room_name = room_url.split('/')[-1] if room_url else None
    if not room_name:
        return []

    url = f"https://api.daily.co/v1/recordings?room_name={room_name}"
    headers = {
        "Authorization": f"Bearer {api_key}",
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data.get('data', [])
        else:
            return []
    except:
        return []