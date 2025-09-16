import requests

class AlisteAPI:
    def __init__(self, username: str, password: str):
        self.base_url = "https://subscriptioncloud.alistetechnologies.com/v3"
        self.auth_header = self._create_auth_header(username, password)
    
    def _create_auth_header(self, username, password):
        import base64
        user_pass = f"{username}:{password}"
        encoded = base64.b64encode(user_pass.encode()).decode()
        return {"Authorization": f"Basic {encoded}"}
    
    def get_house_id(self):
        url = f"{self.base_url}/user/houses"
        response = requests.get(url, headers=self.auth_header)
        response.raise_for_status()
        return response.json()
    
    def get_rooms(self, house_id: str):
        url = f"{self.base_url}/house/rooms"
        payload = {"houseId": house_id}
        headers = {"Content-Type": "application/json", **self.auth_header}
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def get_appliances(self, room_id: str):
        url = f"{self.base_url}/room/appliancesList"
        payload = {"roomId": room_id}
        headers = {"Content-Type": "application/json", **self.auth_header}
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def execute_action(self, device_id: str, switch_id: str, command: str, controller_type="", controller_id="", controller_details=None):
        if controller_details is None:
            controller_details = {}
        url = f"{self.base_url}/device/action"
        payload = {
            "deviceId": device_id,
            "switchId": switch_id,
            "command": command,
            "controllerType": controller_type,
            "controllerId": controller_id,
            "controllerDetails": controller_details,
        }
        headers = {"Content-Type": "application/json", **self.auth_header}
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
