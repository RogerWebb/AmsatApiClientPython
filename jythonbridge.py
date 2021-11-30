# Python Init
import csv, glob, json, os, pickle, sys
from argparse import ArgumentParser
from pprint import pprint
from datetime import datetime

# Java Init
jar_path = os.path.join(os.getcwd(), 'FoxTelem.jar')
sys.path.append(jar_path)

from java.io import File
#from java.time.format import DateTimeFormatter
from org.joda.time.format import DateTimeFormatter
from predict import PositionCalcException
from java.lang import System as JavaSystem
from java.io import PrintStream, OutputStream
from common import Config, FoxSpacecraft, FoxTime, Spacecraft, SatelliteManager, UpdateManager
from telemetry import BitArrayLayout, FramePart, PayloadMaxValues, PayloadMinValues, PayloadRtValues


class FoxTelemJythonBridge:

    def __init__(self, jar_path=None, spacecraft_dir=None, data_dir=None, enable_java_stdout=False):
        # Suppress STDOUT so spurious, unwanted, transmissions don't reach the Fox Telem Bridge Client
        if not enable_java_stdout:
            self.disable_output()

        #self.spacecraft_dir  = spacecraft_dir if spacecraft_dir is not None else os.path.join(os.getcwd(), 'FoxTelem', 'spacecraft')
        self.spacecraft_dir  = "/spacecraft"
        self.data_path       = data_dir if data_dir is not None else os.path.join(os.getcwd(), 'data')
        self.foxdb_path      = os.path.join(self.data_path, 'FOXDB')
        self.serverlogs_path = os.path.join(self.data_path, 'serverlogs')
        self.user_filename   = os.path.join(os.getcwd(), 'userfile.dat')

        self.bridges = {
           'config':     FoxTelemConfigBridge(),
           'spacecraft': FoxTelemSatelliteManagerBridge(SatelliteManager(), UpdateManager(False))
        }

    def enable_output(self):
        JavaSystem.setOut(self._java_stdout)

    def disable_output(self):
        self._java_stdout = JavaSystem.out
        JavaSystem.setOut(PrintStream(NoOutputStream()))

    def get_config(self):
        return self.config.to_json()

    def start(self):
        self.run()

    def emit(self, d):
        s = json.dumps(d) if isinstance(d, dict) else d
        s += "\n"
        sys.stdout.write(s)
        sys.stdout.flush()

    def run(self):
        while True:
            try:
                event = json.loads(sys.stdin.readline()[:-1])
                self.process_event(event)
            except ValueError:
                continue



    def process_event(self, event):
        resource = event['resource'].split('/')
        method   = event['method'] if 'method' in event else 'GET'
        params   = event['params'] if 'params' in event else {}

        # Remove blank initial entry for / prepended routes
        if resource[0] == '':
            resource.pop(0)

        try:
            bridge_name = resource.pop(0)
        except IndexError:
            self.emit({'status': 'error', 'error': 'Invalid Request [missing bridge name]'})

        if bridge_name == 'exit':
            exit()
        elif bridge_name in self.bridges:
            self.emit(self.bridges[bridge_name].process_event(resource, method=method, params=params))
        else:
            self.emit({'status': 'error', 'error': 'No handler for resource'})

    """
    def process_event(self, event):
        cmd = event['cmd']

        if cmd == "get-config":
            self.emit(self.config.dict)
        elif cmd == 'list-spacecraft':
            self.emit("not implemented")
        elif cmd == 'get-spacecraft':
            #self.emit(self.satellite_manager.get_spacecraft(**event['args']))
            self.emit(self.satellite_manager.get_spacecraft_properties(**event['args']))
        elif cmd == 'update-tle':
            self.emit(self.satellite_manager.update_tle())
        else:
            self.emit({"status": "error", "error": "invalid_command"})
    """

# Needed to suppress Java STDOUT
class NoOutputStream(OutputStream):
    def write(self, b, off, len): pass

class FoxTelemConfigBridge:

    def __init__(self):
        Config.homeDirectory = JavaSystem.getProperty("user.home") + File.separator + ".FoxTelem"
        Config.currentDir = JavaSystem.getProperty("user.dir")
        Config.initSatelliteManager()
        Config.initPayloadStore()
        Config.initPassManager()
        Config.initSequence()
        Config.initServerQueue()

    def process_event(self, resource, method='GET', params=None):
        if params is None:
            params = {}

        # /config
        if len(resource) < 1:
            return self.dict

    @property
    def dict(self):
        return self.to_dict()

    def to_dict(self, refresh=False):
        if hasattr(self, '_config_dict'):
            return self._config_dict

        self._config_dict = {}

        for k in Config.__dict__:
            try:
                j = json.dumps(getattr(Config, k))
                self._config_dict[k] = getattr(Config, k)
            except:
                continue

        return self._config_dict

class FoxTelemSatelliteManagerBridge:

    def __init__(self, satellite_manager, update_manager):
        self.satellite_manager = satellite_manager
        self.update_manager    = update_manager

        # Folders had to be copied from private method gui.MainWindow.getFoxServerDir()
        self.server_dirs = [None, "ao85", "radfxsat", "fox1c", "fox1d", "fox1e", "husky"]

    def process_event(self, resource, method='GET', params=None):
        if params is None:
            params = {}

        # /spacecraft
        if len(resource) < 1:
            return self.list_spacecraft()

        # /spacecraft/tle-update
        if resource[0] == 'tle-update':
            return self.tle_update()

        # /spacecraft/1
        # /spacecraft/AO-91
        spacecraft = self.get_spacecraft(resource.pop(0))

        if spacecraft is None:
            return {'status': 'error', 'error': 'Spacecraft not found'}

        try:
            action = resource.pop(0)
        except IndexError:
            action = None

        if action is None:
            # Return Properties for Spacecraft
            return self.get_spacecraft_properties(spacecraft)
        elif action == 'foxdb-download':
            return {'status': 'error', 'error': 'not-implemented'}
        elif action == 'position':
            # /spacecraft/4/position
            if 'resets' not in params or 'uptime' not in params:
                return {'status': 'error', 'error': 'MISSING_PARAM'}

            return self.get_position(spacecraft, int(params['resets']), int(params['uptime']))
        elif action == 't0-table':
            # /spacecraft/4/t0-table
            return self.get_t0_table(spacecraft)
        elif action == 'utctime':
            # /spacecraft/4/utctime
            if 'resets' not in params or 'uptime' not in params:
                return {'status': 'error', 'error': 'MISSING_PARAM'}

            return self.get_utctime(spacecraft, int(params['resets']), int(params['uptime']))
        else:
            return {'status': 'error', 'error': 'Unknown Action'}

    def get_all_spacecraft(self):
        return self.satellite_manager.getSpacecraftList()

    def init_spacecraft(self, spacecraft):
        self.update_manager.updateT0(spacecraft)

    def get_spacecraft(self, spacecraft_resource):
        if isinstance(spacecraft_resource, int) or spacecraft_resource.isnumeric():
            # /spacecraft/1

            spacecraft = self.satellite_manager.getSpacecraft(int(spacecraft_resource))
        else:
            # /spacecraft/AO-91
            spacecraft = self.satellite_manager.getSpacecraftByKepsName(spacecraft_resource)

            # Finally, check by Display Name
            if spacecraft is None:
                spacecraft = self.satellite_manager.getSpacecraftByDisplayName(spacecraft_resource)

        if spacecraft is not None:
            self.init_spacecraft(spacecraft)

        return spacecraft

    def get_spacecraft_properties(self, spacecraft):
        props = {pname: spacecraft.properties.getProperty(pname) for pname in spacecraft.properties.stringPropertyNames()}
        props['server_dir'] = self.server_dirs[int(props['foxId'])]
        props['foxdb_url'] = "/".join([Config.webSiteUrl, props['server_dir'], 'FOXDB.tar.gz'])

        return props

    def get_position(self, spacecraft, reset, uptime):
        satpos = spacecraft.getSatellitePosition(reset, uptime)

        return {
            'latitude':  satpos.getLatitude(),
            'longitude': satpos.getLongitude()
        }

    def get_utctime(self, spacecraft, reset, uptime):
        return {'status': 'ok', 'utctime': spacecraft.getUtcDateTimeForReset(reset, uptime).getMillis()}

    def get_t0_table(self, spacecraft):
        table = spacecraft.getT0TableData()

        if table is None:
            return {'status': 'error', 'error': 'NO_DATA'}

        #TODO dict comprehension, likely
        return table

    def download_server_data(self, spacecraft):
        return None

    def update_tle(self):
        self.satellite_manager.fetchTLEFile()

        return {"status": "ok"}

if __name__ == "__main__":
    ap = ArgumentParser()

    ap.add_argument('--jar-path')
    ap.add_argument('--start-service', action="store_true")
    ap.add_argument('-e', '--event')
    ap.add_argument('--java-stdout', action="store_true") # Turn on Java System Stdout for Debugging

    args = ap.parse_args()

    bridge = FoxTelemJythonBridge(jar_path=args.jar_path, enable_java_stdout=args.java_stdout)

    if args.start_service:
        bridge.start()
    elif args.event is not None:
        bridge.process_event(json.loads(args.event))
    else:
        print("Nothing to do...")

exit()

class AmsatTelemetryParser:

    def __init__(self, spacecraft):
        self.spacecraft = spacecraft

    def get_utc_timestamp(self, reset, uptime):
        return self.spacecraft.getUtcDateTimeForReset(reset, uptime).getMillis()

    def get_satellite_position(self, reset, uptime):
        try:
            return self.spacecraft.getSatellitePosition(reset, uptime)
        except PositionCalcException:
            return None

class AmsatTelemetryDataMigrator:

    def __init__(self, spacecraft_dir=None, data_dir=None):
        #self.spacecraft_dir  = spacecraft_dir if spacecraft_dir is not None else os.path.join(os.getcwd(), 'FoxTelem', 'spacecraft')
        self.spacecraft_dir  = "/spacecraft"
        self.data_path       = data_dir if data_dir is not None else os.path.join(os.getcwd(), 'data')
        self.foxdb_path      = os.path.join(self.data_path, 'FOXDB')
        self.serverlogs_path = os.path.join(self.data_path, 'serverlogs')
        self.user_filename   = os.path.join(os.getcwd(), 'userfile.dat')

        print("Spacecraft Dir: " + self.spacecraft_dir)
        self.satellite_manager = SatelliteManager()
        print("Updating TLE...")
        self.satellite_manager.fetchTLEFile()
        print("Init [OK]")

        self.spacecraft = {}

    def load_spacecraft(self, name, refresh=False):
        return self.satellite_manager.getSpacecraftByKepsName(name)

    def get_serverlog_fieldnames(self, layout):
        return ['captureDate', 'id', 'resets', 'uptime', 'type'] + [s for s in layout.fieldName] 

    def get_serverlog_filename(self, fox, layout):
        name = "{}{}{}.log".format(fox.series, fox.foxId, getattr(fox, "{}_LAYOUT".format(layout)))

        return os.path.join(self.serverlogs_path, name)

    def get_payload_object(self, layout_name, layout):
        if layout_name == "REAL_TIME":
            return PayloadRtValues(layout)
        elif layout_name == "MIN":
            return PayloadMinValues(layout)
        elif layout_name == "MAX":
            return PayloadMaxValues(layout)
        else:
            raise ValueError("Layout Name {} does not exist or is not yet supported by the tool.".format(layout_name))

    """
    Process Serverlog File
    fox - FoxSpacecraft Object
    layout_name - "REAL_TIME", "MIN" or "MAX"
    """
    def process_serverlog(self, fox, layout_name):
        if layout_name not in ["REAL_TIME", "MIN", "MAX"]:
            raise ValueError("Layout Name {} does not exist or is not yet supported by the tool.".format(layout_name))

        layout = fox.getLayoutByName(getattr(Spacecraft, "{}_LAYOUT".format(layout_name)))

        data_filename = self.get_serverlog_filename(fox, layout_name)

        data_fp = open(data_filename, 'r')
        reader = csv.DictReader(data_fp, fieldnames=self.get_serverlog_fieldnames(layout))

        for row in reader:
            payload = self.get_payload_object(layout_name, layout)

            row['captureDate'] = datetime.strptime(row['captureDate'], "%Y%m%d%H%M%S")

            for field in layout.fieldName:
                #TODO Other Status, Message, On/Off, etc messages aren't yet decoded.  Other functions appear to do this.
                #row[field] = payload.convertRawValue(field, int(row[field]), layout.getConversionByName(field), fox)
                row[field] = payload.getStringValue(field, fox)

            yield row

        data_fp.close()

    def process_serverlog_to_csv(self, fox, layout_name, output_filename):
        output_fp = open(output_filename, 'w')
        layout = fox.getLayoutByName(getattr(Spacecraft, "{}_LAYOUT".format(layout_name)))
        writer = csv.DictWriter(output_fp, fieldnames=self.get_serverlog_fieldnames(layout))
        writer.writeheader()

        for row in self.process_serverlog(fox, layout_name):
            writer.writerow(row)

        output_fp.close()


if __name__ == "__main__":
    ap = ArgumentParser()

    subparsers = ap.add_subparsers(dest='command')

    config_p = subparsers.add_parser('write-config')

    config_p.add_argument('output', default='foxtelem.config.json')

    """
    ap.add_argument('spacecraft', help="Spacecraft Name (ie. FOX1D)")
    ap.add_argument('-l', '--layout', help="REAL_TIME, MIN or MAX")
    ap.add_argument('-o', '--output', help="Output Filename")
    ap.add_argument('--data-path')
    """

    args = ap.parse_args()

    if args.command == "write-config":
        FoxTelemConfigWriter().write(args.output)

    """
    mig = AmsatTelemetryDataMigrator(data_dir=args.data_path)

    fox = mig.load_spacecraft(args.spacecraft)

    mig.process_serverlog_to_csv(fox, args.layout, args.output)
    """
