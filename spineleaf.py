from client import Action, Client, Flow, Instruction, Match
import vars
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--host', default='127.0.0.1', required=True, help='ODL host IP address (default is localhost)')
parser.add_argument('--table', type=int, default=0, help='Table ID to monitor (default: 0)')
parser.add_argument('--save', action='store_true', help="Save the flows into a file.")
args = parser.parse_args()

nodes = vars.NODES
names = vars.NAMES
table = args.table
save = args.save

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
            f"{names[dpid]}00",
            "ARP",
            table,
            100,
            Match.arp(),
            [
                ins.apply([act.output("NORMAL")])
            ]
        ),
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
            ),
            save
        )

# Leaf distribution
for dpid in leafs:
    # leaf spine distribution
    c.setFlow(
        dpid=dpid,
        flow=Flow(
            f"{names[dpid]*3}",
            "S-balanced",
            table,
            90,
            Match.eth(dst_ip="10.0.0.0/16"),
            [
                ins.meter(1),
                ins.table(101, 1)
            ]
        ),
        
    )
    # # Priority path
    c.setFlow(
        dpid=dpid,
        flow=Flow(
            f"{names[dpid]}01",
            "S-balanced-path-A",
            101, # table
            100, # priority
            Match.dscp(10),
            [
                ins.apply([
                    act.output(2)
                ])
            ]
        ),
        
    )
    # Seconday path
    c.setFlow(
        dpid=dpid,
        flow=Flow(
            f"{names[dpid]}02",
            "S-balanced-path-B",
            101, # table
            100, # priority
            Match.dscp(12),
            [
                ins.apply([
                    act.output(3)
                ])
            ]
        ),
    )
        # Seconday path
    c.setFlow(
        dpid=dpid,
        flow=Flow(
            f"{names[dpid]}03",
            "S-balanced-path-B-2",
            101, # table
            100, # priority
            Match.eth(dst_ip="10.0.0.0/16"),
            [
                ins.apply([
                    act.output(3)
                ])
            ]
        ),
    )
    # leaf host distribution
    for host in hosts:
        c.setFlow(
            dpid,
            Flow(
                f"{names[dpid]}0{host}",
                f"H{host}",
                table,
                100,
                Match.eth(dst_ip=f"10.0.{int(names[dpid])-2}.{host}/32"),
                [
                    ins.apply([
                        act.output((host) + 12)
                    ])
                ]
            ),
            save
        )
