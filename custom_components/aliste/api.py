import requests
from datetime import datetime, timedelta

class AlisteAPI:
    def __init__(self, username: str, password: str):
        self.base_url = "https://subscriptioncloud.alistetechnologies.com/v3"
        self.auth_header = self._create_auth_header(username, password)
        self.token_renew_url = "https://9qqqknyk98.execute-api.ap-south-1.amazonaws.com/default/updateEkeyPeriod"
    
    def _create_auth_header(self, username, password):
        import base64
        user_pass = f"{username}:{password}"
        encoded = base64.b64encode(user_pass.encode()).decode()
        return {"Authorization": f"Basic {encoded}"}
    
    def renew_token(self, key_id: int, start_date: datetime = None, end_date: datetime = None):
        if start_date is None:
            start_date = datetime.utcnow()
        if end_date is None:
            end_date = start_date + timedelta(days=360)
        
        payload = {
            "keyId": key_id,
            "startDate": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "endDate": end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        
        headers = {
            "Content-Type": "application/json",
            **self.auth_header
        }
        
        response = requests.post(self.token_renew_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    
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
            "command": command,  # should be string values like "0", "25", "50", "75", "100"
            "controllerType": controller_type,
            "controllerId": controller_id,
            "controllerDetails": controller_details
        }
        headers = {"Content-Type": "application/json", **self.auth_header}
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
