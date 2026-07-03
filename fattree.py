from client import Action, Client, Flow, Instruction, Match
import vars

nodes = list(vars.NODES)
core = nodes[0]
aggrs = nodes[1:3]
edges = nodes[3:]
n_host = 4      # Number of host by edge sw

table = vars.ODL_TABLE
c = Client(
    ip=vars.ODL_HOST,
    default_table=vars.ODL_TABLE
)
ins = Instruction()
act = Action()

# Install the ARP
for i, dpid in enumerate(nodes):
    ins.reset()
    act.reset()
    c.setFlow(dpid, Flow(f"{i}000", "arp", table, 100, Match.arp(),[ins.apply([act.output("NORMAL")])]))

# Install the core distribution on S1
for i in range(1, 3):
    ins.reset()
    act.reset()
    c.setFlow(core,
        Flow(
            id=f"10{i}",
            name=f"core-distribution-{i}",
            table=table,
            priority=100,
            match=Match.eth(dst_ip=f"10.0.{i}.0/24"),
            instructions=[
                ins.apply([
                    act.output(f"{i+1}")
                 ])
            ]
        )
    )

ins.reset()
act.reset()

c.setFlow(aggrs[0], Flow("201", "aggr1-to-edge1", table, 100,
    Match.eth(dst_ip="10.0.1.0/24"),
    [ ins.apply([ act.output("3") ]) ]
))

ins.reset()
act.reset()

c.setFlow(aggrs[0], Flow("202", "aggr1-to-core", table, 100,
    Match.eth(dst_ip="10.0.2.0/24"),
    [ ins.apply([ act.output("2") ]) ]
))

ins.reset()
act.reset()

c.setFlow(aggrs[1], Flow("301", "aggr2-to-core", table, 100,
    Match.eth(dst_ip="10.0.1.0/24"),
    [ ins.apply([ act.output("2") ]) ]
))

ins.reset()
act.reset()

c.setFlow(aggrs[1], Flow("302", "aggr2-to-edge2", table, 100,
    Match.eth(dst_ip="10.0.2.0/24"),
    [ ins.apply([ act.output("3") ]) ]
))

ins.reset()
act.reset()

# Edge Flows
for i, edge in enumerate(edges, start=1):
    # Edge distribution, flows are not in the same switch
    c.setFlow(edge, Flow(f"{i}00", f"edge{i}-to-aggr", table, 90,
        Match.eth(dst_ip="10.0.0.0/16"),
        [ ins.apply([ act.output(2) ]) ]
    ))
    ins.reset()
    act.reset()
    # host distrubution
    for host in range(1, n_host+1):
        ins.reset()
        act.reset()
        c.setFlow(edge, Flow(f"{i}0{host}", f"{i}-to-host{host}", table, 100,
            Match.eth(dst_ip=f"10.0.{i}.{host}/32"),
            [ ins.apply([ act.output(host + 12) ]) ]
        ))

for host in range(5, 7):
    ins.reset()
    act.reset()
    c.setFlow(edges[-1], Flow(f"50{host}", f"host-{host}", table, 100,
        Match.eth(dst_ip=f"10.0.2.{host}/32"),
        [ ins.apply([ act.output(host + 12) ]) ]
    ))
