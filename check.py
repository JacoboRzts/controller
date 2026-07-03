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

print(f"{'DPID':<16} {'TAB':<3} {'ID':<14} {'Name':<32}")
print("-"*64)
for dpid in nodes:
    flows = c.getFlows(dpid)
    if flows is not None:
        c.printFlows(dpid, flows)
        print("-"*64)
        if args.save:
            for flow in flows:
                name = flow.get("flow-name", "noname")
                c.saveFlow(flow, name, f"flows/{names[dpid]}")
    else:
        print(f"{dpid} is empty")
