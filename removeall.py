from client import Client
import vars
import argparse

nodes = vars.NODES
names = vars.NAMES

parser = argparse.ArgumentParser(description='OpenDaylight Flow Monitor with Rich UI')
parser.add_argument('--host', default='127.0.0.1', required=True, help='ODL host IP address (default is localhost)')
parser.add_argument('--table', type=int, default=0, help='Table ID to monitor (default: 0)')
parser.add_argument('--save', action='store_true', help="Save the flows into a file.")
args = parser.parse_args()

c = Client(ip=args.host, default_table=args.table)
for dpid in nodes:
    c.deleteFlows(dpid)
