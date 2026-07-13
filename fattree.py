from client import Action, Client, Flow, Instruction, Match
import vars
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-c' ,'--controller', default='127.0.0.1', help='ODL Controller IP address (default is localhost)')
parser.add_argument('-t' ,'--table', type=int, default=100, help='Table to upload flows (default: 100)')
parser.add_argument('-s' ,'--save', action='store_true', help="Save the flows into a file.")
args = parser.parse_args()

nodes = list(vars.NODES)
core = nodes[0]
aggrs = nodes[1:3]
edges = nodes[3:]
n_host = 4      # Number of host by edge sw

table = args.table
c = Client(
    ip=args.controller,
    default_table=args.table
)

# Install the ARP
for i, dpid in enumerate(nodes):
    c.setFlow(dpid, Flow(f"{i}00", "arp", table, 100, Match.arp(),[Instruction.apply([Action.output("FLOOD")])]))

# Install the core distribution on S1
for i in range(1, 3):
    c.setFlow(core,
        Flow(
            id=f"10{i}",
            name=f"core-distribution-{i}",
            table=table,
            priority=100,
            match=Match.eth(dst_ip=f"10.0.{i}.0/24"),
            instructions=[
                Instruction.apply([
                    Action.output(f"{i+1}")
                 ])
            ]
        )
    )

c.setFlow(aggrs[0], Flow("240", "edge1", table, 100,
    Match.eth(dst_ip="10.0.1.0/24"),
    [ Instruction.apply([ Action.output("3") ]) ]
))

c.setFlow(aggrs[0], Flow("210", "core", table, 100,
    Match.eth(dst_ip="10.0.2.0/24"),
    [ Instruction.apply([ Action.output("2") ]) ]
))

c.setFlow(aggrs[1], Flow("350", "edge2", table, 100,
    Match.eth(dst_ip="10.0.2.0/24"),
    [ Instruction.apply([ Action.output("3") ]) ]
))

c.setFlow(aggrs[1], Flow("310", "core", table, 100,
    Match.eth(dst_ip="10.0.1.0/24"),
    [ Instruction.apply([ Action.output("2") ]) ]
))


# Edge Flows
for i, edge in enumerate(edges, start=1):
    # Edge distribution, flows are not in the same switch
    c.setFlow(edge, Flow(f"{i + 4}00", "aggr", table, 90,
        Match.eth(dst_ip="10.0.0.0/16"),
        [ Instruction.apply([ Action.output(2) ]) ]
    ))
    # host distrubution
    for host in range(1, n_host+1):
        c.setFlow(edge, Flow(f"{i + 4}0{host}", f"host{host}", table, 100,
            Match.eth(dst_ip=f"10.0.{i}.{host}/32"),
            [ Instruction.apply([ Action.output(host + 12) ]) ]
        ))

for host in range(5, 7):
    c.setFlow(edges[-1], Flow(f"50{host}", f"host-{host}", table, 100,
        Match.eth(dst_ip=f"10.0.2.{host}/32"),
        [ Instruction.apply([ Action.output(host + 12) ]) ]
    ))
