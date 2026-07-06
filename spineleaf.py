from client import Action, Client, Flow, Instruction, Match
import vars
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--host', default='127.0.0.1', help='ODL host IP address (default is localhost)')
parser.add_argument('--table', type=int, default=0, help='Table ID to monitor (default: 0)')
parser.add_argument('--save', action='store_true', help="Save the flows into a file.")
args = parser.parse_args()

nodes = vars.NODES
names = vars.NAMES
table = args.table

arps = nodes[1:]
spines = nodes[0:2]
leafs = nodes[2:]
hosts = [1, 2, 3]
subnets = hosts

c = Client(ip=args.host, default_table=args.table)
ins = Instruction()
act = Action()

# Add all the ARP flows into Switches 2 to 5
for dpid in arps:
    c.setFlow(
        dpid,
        Flow(
            f"{names[dpid]}000",
            "ARP",
            table,
            100,
            Match.arp(),
            [
                ins.apply([act.output("NORMAL")])
            ]
        )
    )

# Spine leaf distribution
for dpid in spines:
    for subnet in subnets:
        c.setFlow(
            dpid,
            Flow(
                f"{names[dpid]}0{subnet}",
                f"L{subnet}",
                table,
                100,
                Match.eth(dst_ip=f"10.0.{subnet}.0/24"),
                [
                    ins.apply([
                        act.output(str(subnet + 1)),
                    ])
                ]
            )
        )

# Leaf distribution
for dpid in leafs:
    # leaf spine distribution
    this = int(names[dpid]) - 2
    ports = [2, 3]
    subnets = [1, 2, 3]
    nextport = 0
    for subnet in subnets:
        if subnet == this:
            continue
        c.setFlow(
            dpid,
            Flow(
                f"{names[dpid]}000{subnet}",
                f"S{subnet}",
                table,
                90,
                Match.eth(dst_ip=f"10.0.{subnet}.0/24"),
                [
                    ins.apply([
                        act.output(ports[nextport]),
                    ])
                ]
            ),
            True
        )
        nextport += 1
        nextport %= 2
    # leaf host distribution
    for host in hosts:
        c.setFlow(
            dpid,
            Flow(
                f"{names[dpid]}00{host}",
                f"H{host}",
                table,
                100,
                Match.eth(dst_ip=f"10.0.{int(names[dpid])-2}.{host}/32"),
                [
                    ins.apply([
                        act.output((host) + 12)
                    ])
                ]
            )
        )
dpid = nodes[-1]
host = 4
c.setFlow(
    dpid,
    Flow(
        f"{names[dpid]}00{host}",
        f"H{host}",
        table,
        100,
        Match.eth(dst_ip=f"10.0.{int(names[dpid])-2}.{host}/32"),
        [
            ins.apply([
                act.output((host) + 12)
            ])
        ]
    )
)
