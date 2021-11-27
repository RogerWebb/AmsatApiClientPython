import logging, os, json, requests, shutil, subprocess
import pickle
from argparse import ArgumentParser
from pprint import pprint

class FoxTelemBridge:

    def __init__(self, script=None, debug=False):
        self.debug = debug

        # Ensure Jython is installed and exit if not
        self.jython_check()

        self.script = script if script is not None else os.path.join(os.getcwd(), 'jythonbridge.py')

        self.p = p = subprocess.Popen([self.jython_path, self.script, '--start-service'], stdout=subprocess.PIPE, stdin=subprocess.PIPE)

    def jython_check(self):
        self.jython_path = shutil.which("jython")

        if self.jython_path is None:
            raise Exception("Jython not installed.  Please install Jython to proceed.  (https://www.jython.org/installation)")

    def _call(self, resource, method='GET', params=None):
        event = {
            'resource': resource,
            'method':   method
        }

        if params is not None and isinstance(params, dict):
            event['params'] = params

        event_s = json.dumps(event) + "\n"

        if self.debug:
            print("FoxTelemBridge: {}".format(event_s))

        self.p.stdin.write(event_s.encode('utf-8'))
        self.p.stdin.flush()

        response = self.p.stdout.readline().decode('utf-8')[:-1]

        return json.loads(response)

    def get_config(self):
        return self._call('/config')

    def get_spacecraft_properties(self, id=None, name=None):
        if id is None and name is None:
            raise ValueError("Must pass id or name")

        return self._call("/spacecraft/{}".format(id if id is not None else name))

    def get_spacecraft_utctime(self, id=None, name=None):
        if id is None and name is None:
            raise ValueError("Must pass id or name")

        return self._call("/spacecraft/{}/utctime".format(id if id is not None else name))


