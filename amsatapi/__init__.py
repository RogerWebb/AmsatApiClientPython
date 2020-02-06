from argparse import ArgumentParser
from io import StringIO
import requests
from pprint import pprint

""""
The AmsatApiClient object provides a thin interface to the resources on the 
amsat.org site and API.
"""
class AmsatApiClient:

    def __init__(self):
        self.base_url = "https://amsat.org"
        self.status_url = self.base_url + "/status/api/v1/sat_info.php"
        self.tle_url    = self.base_url + "/tle/current/nasabare.txt"
        self.track_url  = self.base_url + "/track/api/v1/passes.php"

        self._tle = None

    @property
    def tle(self):
        if self._tle is not None:
            return self._tle

        self._tle = self.fetch_tle_dict()

        return self._tle

    def fetch_tle_file(self):
        return requests.get(self.tle_url).content.decode('utf-8')

    def fetch_tle_dict(self):
        fp = StringIO(self.fetch_tle_file())

        tle_d = {}
        while(fp.readable()):
            name = fp.readline().rstrip("\n")
            tle = [fp.readline().rstrip("\n"), fp.readline().rstrip("\n")]

            if name is None or len(name) < 1:
                break

            tle_d[name] = tle

        return tle_d

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

    def _download_file(self, uri, output_filename):
        with open(output_filename, 'wb') as out_fp:
            r = requests.get("{}{}".format(self.base_url, uri))

            out_fp.write(r.content)

    # https://www.amsat.org/tlm/fox1d/FOXDB.tar.gz
    def download_telemetry_database(self, sat_name, output_filename="FOXDB.tar.gz"):
        uri = "/tlm/{}/FOXDB.tar.gz".format(sat_name)

        self._download_file(uri, output_filename)

    # https://www.amsat.org/tlm/fox1d/serverlogs.tar.gz
    def download_telemetry_serverlogs(self, sat_name, output_filename="serverlogs.tar.gz"):
        uri = "/tlm/{}/serverlogs.tar.gz".format(sat_name)

        self._download_file(uri, output_filename)

def parse_args():
    ap = ArgumentParser()

    subparsers = ap.add_subparsers(dest='operation')

    status_p = subparsers.add_parser('status')

    status_p.add_argument('-n', '--name', required=True, help="The name of the satellite must match the string shown on amsat.org/status , i.e AO-91 works, but AO-92 does not ... use AO-92_L/v or AO-92_U/v instead.")
    status_p.add_argument('--hours', default=96, help="The hours parameter is optional, if you omit it you will get the last 96 hours of reports.") # Unable to use -h because of conflict with help arg.

    passes_p = subparsers.add_parser('passes')

    passes_p.add_argument('-l', '--location', help="Select a name from the list returned from above and use a Maidenhead grid square to specify the location.")
    passes_p.add_argument('-o', '--object', help="Sames as 'name' in status operation.")

    download_db_p = subparsers.add_parser('download-telemetry-database')

    download_db_p.add_argument('-n', '--name', required=True, help="Sat Name as in 'fox1d' for /tlm/fox1d/FOXDB.tar.gz")
    download_db_p.add_argument('-o', '--output', default="FOXDB.tar.gz", help="Output Filename")

    download_sl_p = subparsers.add_parser('download-telemetry-serverlogs')

    download_sl_p.add_argument('-n', '--name', required=True, help="Sat Name as in 'fox1d' for /tlm/fox1d/FOXDB.tar.gz")
    download_sl_p.add_argument('-o', '--output', default="serverlogs.tar.gz", help="Output Filename")

    tle_p = subparsers.add_parser('tle')

    tle_p.add_argument('-n', '--name', help="Satellite Name from TLE Line 0")
    tle_p.add_argument('-o', '--output', help="Output Filename (Default Prints to stdout)")

    return ap.parse_args()

def main():
    args = parse_args()

    amsat = AmsatApiClient()

    if args.operation == 'status':
        pprint(amsat.get_sat_status(args.name, hours=args.hours))
    elif args.operation == "passes":
        pprint(amsat.get_sat_passes(args.location, args.object))
    elif args.operation == "download-telemetry-database":
        amsat.download_telemetry_database(args.name, output_filename=args.output)
    elif args.operation == "download-telemetry-serverlogs":
        amsat.download_telemetry_serverlogs(args.name, output_filename=args.output)
    elif args.operation == "tle":
        if args.name is not None:
            tle_elem = amsat.tle[args.name]
            print(args.name)
            print("\n".join(tle_elem))
        else:
            print(amsat.fetch_tle_file())
    else:
        print("Invalid Operation")

