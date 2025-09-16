import base64, json, requests

class AlisteAPI:
    BASE = "https://subscriptioncloud.alistetechnologies.com/v3"

    def __init__(self, username: str, password: str):
        token = base64.b64encode(f"{username}:{password}".encode()).decode()
        self.hdr = {"Authorization": f"Basic {token}", "Content-Type": "application/json"}

    # ---------- GETTERS ----------
    def houses(self):
        return requests.get(f"{self.BASE}/user/houses", headers=self.hdr).json()

    def rooms(self, house_id: str):
        payload = json.dumps({"houseId": house_id})
        return requests.post(f"{self.BASE}/house/rooms", headers=self.hdr, data=payload).json()

    def appliances(self, room_id: str):
        payload = json.dumps({"roomId": room_id})
        return requests.post(f"{self.BASE}/room/appliancesList", headers=self.hdr, data=payload).json()

    # ---------- COMMAND ----------
    def action(self, device_id: str, switch_id: str, command: str):
        body = json.dumps({"deviceId": device_id, "switchId": switch_id, "command": command, "controllerDetails": {}})
        return requests.post(f"{self.BASE}/device/action", headers=self.hdr, data=body).json()
