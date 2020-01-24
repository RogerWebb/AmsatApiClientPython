from argparse import ArgumentParser
from . import AmsatApiClient
from pprint import pprint

def parse_args():
    ap = ArgumentParser()

    subparsers = ap.add_subparsers(dest='operation')

    status_p = subparsers.add_parser('status')

    status_p.add_argument('-n', '--name', required=True, help="The name of the satellite must match the string shown on amsat.org/status , i.e AO-91 works, but AO-92 does not ... use AO-92_L/v or AO-92_U/v instead.")
    status_p.add_argument('--hours', default=96, help="The hours parameter is optional, if you omit it you will get the last 96 hours of reports.") # Unable to use -h because of conflict with help arg.

    passes_p = subparsers.add_parser('passes')

    passes_p.add_argument('-l', '--location', help="Select a name from the list returned from above and use a Maidenhead grid square to specify the location.")
    passes_p.add_argument('-o', '--object', help="Sames as 'name' in status operation.")

    return ap.parse_args()

if __name__ == "__main__":
    args = parse_args()

    amsat = AmsatApiClient()

    if args.operation == 'status':
        pprint(amsat.get_sat_status(args.name, hours=args.hours))
    elif args.operation == "passes":
        pprint(amsat.get_sat_passes(args.location, args.object))
    else:
        print("Invalid Operation")
