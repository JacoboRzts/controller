from client import Client
import argparse
from rich import print

parser = argparse.ArgumentParser(description='OpenDaylight Flow Monitor with Rich UI')
parser.add_argument('-c' ,'--controller', default='127.0.0.1', help='ODL Controller IP address, localhost by default.')
parser.add_argument('-s', '--save', action='store_true', help="Save the flows into a file.")
args = parser.parse_args()

c = Client(ip=args.controller)

try:
    topology = c.getTopology()
    nodes = c.getNodesDPID(topology)
    for node in nodes:
        flows = c.getAllFlows(node)
        groups = c.getAllGroups(node)
        meters = c.getAllMeters(node)
        print(f"[bold]{node}", end='  ')
        print(f'[blue] {len(flows)} flows [green] {len(groups)} groups [orange] {len(meters)} meters')
        if args.save:
            for flow in flows:
                c.saveFlow(flow, flow['id'], f"flow/{node}")
except Exception as e:
    print(f"[bold red]Error:[/bold red] {str(e)}")
