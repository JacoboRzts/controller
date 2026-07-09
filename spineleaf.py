from client import Action, Client, Flow, Instruction, Match
import vars
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-c' ,'--controller', default='127.0.0.1', help='ODL Controller IP address (default is localhost)')
parser.add_argument('-t' ,'--table', type=int, default=100, help='Table to upload flows (default: 100)')
parser.add_argument('-s' ,'--save', action='store_true', help="Save the flows into a file.")
args = parser.parse_args()

nodes = vars.NODES
names = vars.NAMES
table = args.table

arps = nodes[1:]
spines = nodes[0:2]
leafs = nodes[2:]
hosts = [1, 2, 3]
subnets = hosts
ports = [2, 3]

c = Client(ip=args.controller, default_table=args.table)

# ARP Flows
for dpid in arps:
    c.setFlow(
        dpid,
        Flow(
            f"{names[dpid]}00",
            "ARP",
            table,
            100,
            Match.arp(),
            [
                Instruction.apply([
                    Action.output("FLOOD")
                ])
            ]
        ),
    )

# Spine leaf distribution flows
for dpid in spines:
    for subnet in subnets:
        c.setFlow(
            dpid,
            Flow(
                f"{names[dpid]}{subnet}0",
                f"L{subnet}",
                table,
                100,
                Match.eth(dst_ip=f"10.0.{subnet}.0/24"),
                [
                    Instruction.apply([
                        Action.output(str(subnet + 1)),
                    ])
                ]
            ),
        )

# Leaf distribution
for dpid in leafs:
    # Leaf -> spine distribution flows
    this = int(names[dpid]) - 2
    nextport = 0
    for subnet in subnets:
        if subnet == this:
            continue
        c.setFlow(
            dpid,
            Flow(
                f"{names[dpid]}{subnet}0",
                f"S{ports[nextport]-1}-L{subnet}",
                table,
                90,
                Match.eth(dst_ip=f"10.0.{subnet}.0/24"),
                [
                    Instruction.apply([
                        Action.output(ports[nextport]),
                    ])
                ]
            )
        )
        nextport = (nextport + 1) % 2
    # Leaf -> host distribution flows
    for host in hosts:
        c.setFlow(
            dpid,
            Flow(
                f"{names[dpid]}0{host}",
                f"H{int(names[dpid]) + host}",
                table,
                100,
                Match.eth(dst_ip=f"10.0.{int(names[dpid])-2}.{host}/32"),
                [
                    Instruction.apply([
                        Action.output((host) + 12)
                    ])
                ]
            ),
        )

# Add and extra host (H10) as a test host.
dpid = nodes[-1]
host = 4
c.setFlow(
    dpid,
    Flow(
        f"{names[dpid]}0{host}",
        f"H{host}",
        table,
        100,
        Match.eth(dst_ip=f"10.0.{int(names[dpid])-2}.{host}/32"),
        [
            Instruction.apply([
                Action.output((host) + 12)
            ])
        ]
    )
)
