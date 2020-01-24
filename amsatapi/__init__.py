import requests
from pprint import pprint

class AmsatApiClient:

    def __init__(self):
        self.base_url = "https://amsat.org"
        self.status_url = self.base_url + "/status/api/v1/sat_info.php"
        self.track_url = self.base_url + "/track/api/v1/passes.php"

    # amsat.org/status/api/v1/sat_info.php?name=AO-91&hours=24
    def get_sat_status(self, sat_name, hours=96):
        params = {
            'name': sat_name,
            'hours': hours
        }
        return requests.get(self.status_url, params=params).json()

    # www.amsat.org/track/api/v1/passes.php?location=JN42&object=ISS
    def get_sat_passes(self, location, sat_name):
        params = {
            'location': location, 
            'object': sat_name
        }
        return requests.get(self.track_url, params=params).json()

