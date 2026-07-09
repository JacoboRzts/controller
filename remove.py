from client import Client
import argparse
from rich import print

parser = argparse.ArgumentParser(description='Remove all the flows from the controller')
parser.add_argument('-c' ,'--controller', default='127.0.0.1', help='ODL Controller IP address, localhost by default.')
parser.add_argument('-v' ,'--verbose', action='store_true', help="Show more information about the flows removed, false by default.")
args = parser.parse_args()

# Función para obtener el color según el código de estado
def get_status_color(status_code):
    if status_code in [200, 201]:
        return "green"
    elif status_code == 204:
        return "yellow"
    elif status_code >= 400:
        return "red"
    else:
        return "white"

c = Client(ip=args.controller)

try:
    topology = c.getTopology()
    nodes = c.getNodesDPID(topology)
    total_nodes = len(nodes)
    total_flows_deleted = 0
    deleted_flows_info = []
    for node in nodes:
        flows = c.getAllFlows(node)
        node_flows_deleted = 0
        for flow in flows:
            id = flow.get('id')
            table = flow.get('table_id')
            if 'TABLE' not in id:
                # Eliminar el flow
                status_code = c.deleteFlow(node, id, table)
                total_flows_deleted += 1
                node_flows_deleted += 1
                if args.verbose:
                    # Guardar información para mostrar después
                    deleted_flows_info.append({
                        'status': status_code,
                        'dpid': node,
                        'table': table,
                        'id': id
                    })
    if args.verbose:
        if deleted_flows_info:
            print(f"\n[bold] {'CODE':<5} {'DPID':<16} TAB ID")
            for info in deleted_flows_info:
                status = info['status']
                color = get_status_color(status)
                print(f"[{color}] [{status}] {info['dpid']:<16} {str(info['table']).zfill(3)} {info['id']}")
            print()
        else:
            print(f"\n[yellow] {total_flows_deleted} flows deleted in {total_nodes} nodes.\n")
    else:
        print(f"\n[green] {total_flows_deleted} flows deleted in {total_nodes} nodes.\n")
except Exception as e:
    print(f"[bold red]Error:[/bold red] {str(e)}")
