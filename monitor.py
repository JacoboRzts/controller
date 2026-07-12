#!/usr/bin/env python3
"""
OpenDaylight Flow Monitor - Monitor flow statistics in real-time with Rich UI
Usage: python odl_flow_monitor.py --host 192.168.1.100 --port 8181 --user admin --password admin --table 0 --interval 5
"""

import requests
import time
import argparse
import sys
from datetime import datetime
import signal
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich import box
from rich.text import Text
from rich.align import Align

class ODLFlowMonitor:
    def __init__(self, host, port=8181, user='admin', password='admin', table=0, interval=5):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.auth = (user, password)
        self.table = table
        self.interval = interval
        self.nodes_cache = []
        self.running = True
        self.flow_history = {}
        self.console = Console()
        
        # Configure headers
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # Configure signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, sig, frame):
        """Handle interrupt signals"""
        self.running = False
    
    def get_topology(self):
        """Get topology from OpenDaylight"""
        url = f"{self.base_url}/rests/data/network-topology:network-topology/topology=flow:1"
        try:
            response = requests.get(url, auth=self.auth, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.console.print(f"[red]Error getting topology: {e}[/red]")
            return None
    
    def extract_nodes_from_topology(self, topology_data):
        """Extract all OpenFlow nodes from topology"""
        nodes = []
        try:
            topology = topology_data.get('network-topology:topology', [])
            if not topology:
                return nodes
            
            for topo in topology:
                node_list = topo.get('node', [])
                for node in node_list:
                    node_id = node.get('node-id', '')
                    if node_id.startswith('openflow:'):
                        dpid = node_id.split(':')[1]
                        nodes.append({
                            'dpid': dpid,
                            'node_id': node_id
                        })
        except Exception as e:
            self.console.print(f"[red]Error extracting nodes: {e}[/red]")
        
        return nodes
    
    def get_flow_table(self, dpid):
        """Get flow table statistics for a specific node"""
        url = f"{self.base_url}/rests/data/opendaylight-inventory:nodes/node=openflow:{dpid}/flow-node-inventory:table={self.table}"
        try:
            response = requests.get(url, auth=self.auth, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return None
    
    def is_numeric_flow_id(self, flow_id):
        """Check if flow ID contains only numbers"""
        try:
            int(flow_id)
            return True
        except ValueError:
            return False
    
    def format_bytes(self, bytes_str):
        """Format bytes to human readable representation"""
        try:
            bytes_int = int(bytes_str)
            if bytes_int >= 1024**3:
                return f"{bytes_int/1024**3:.2f} GB"
            elif bytes_int >= 1024**2:
                return f"{bytes_int/1024**2:.2f} MB"
            elif bytes_int >= 1024:
                return f"{bytes_int/1024:.2f} KB"
            else:
                return f"{bytes_int} B"
        except:
            return bytes_str
    
    def format_packets(self, packets_str):
        """Format packets with thousand separators"""
        try:
            packets_int = int(packets_str)
            return f"{packets_int:,}"
        except:
            return packets_str
    
    def calculate_rate(self, current, previous, interval):
        """Calculate rate per second"""
        try:
            if previous is None:
                return "N/A"
            current_val = int(current)
            prev_val = int(previous)
            diff = current_val - prev_val
            if diff < 0:
                return "0"
            rate = diff / interval
            if rate >= 1000000:
                return f"{rate/1000000:.2f}M/s"
            elif rate >= 1000:
                return f"{rate/1000:.2f}K/s"
            else:
                return f"{rate:.0f}/s"
        except:
            return "N/A"
    
    def parse_flow_stats(self, flow_data, dpid):
        """Parse flow statistics from flow data"""
        flows = []
        try:
            tables = flow_data.get('flow-node-inventory:table', [])
            if not tables:
                return flows
            
            for table in tables:
                flow_list = table.get('flow', [])
                for flow in flow_list:
                    flow_id = flow.get('id', 'unknown')
                    
                    # Filter out flows with letters in ID
                    if not self.is_numeric_flow_id(flow_id):
                        continue
                    
                    priority = flow.get('priority', 0)
                    
                    # Extract match information
                    match = flow.get('match', {})
                    match_info = self.extract_match_info(match)
                    
                    # Extract action information
                    instructions = flow.get('instructions', {})
                    action_info = self.extract_action_info(instructions)
                    
                    # Extract statistics
                    stats = flow.get('opendaylight-flow-statistics:flow-statistics', {})
                    packet_count = stats.get('packet-count', '0')
                    byte_count = stats.get('byte-count', '0')
                    duration = stats.get('duration', {})
                    duration_sec = duration.get('second', 0)
                    
                    # Create flow key for history tracking
                    flow_key = f"{dpid}:{flow_id}"
                    
                    # Calculate rates
                    prev_stats = self.flow_history.get(flow_key, {})
                    packet_rate = self.calculate_rate(packet_count, prev_stats.get('packet_count'), self.interval)
                    byte_rate = self.calculate_rate(byte_count, prev_stats.get('byte_count'), self.interval)
                    
                    # Store current stats
                    self.flow_history[flow_key] = {
                        'packet_count': packet_count,
                        'byte_count': byte_count
                    }
                    
                    flows.append({
                        'dpid': dpid,
                        'flow_id': flow_id,
                        'priority': priority,
                        'match': match_info,
                        'action': action_info,
                        'packets': packet_count,
                        'bytes': byte_count,
                        'packet_rate': packet_rate,
                        'byte_rate': byte_rate,
                        'duration': duration_sec
                    })
        except Exception as e:
            pass
        
        return flows
    
    def extract_match_info(self, match):
        """Extract human-readable match information"""
        parts = []
        
        # Ethernet match
        eth_match = match.get('ethernet-match', {})
        if eth_match:
            eth_type = eth_match.get('ethernet-type', {})
            if eth_type:
                eth_type_val = eth_type.get('type', '')
                if eth_type_val:
                    if eth_type_val == 2048:
                        parts.append("IPv4")
                    elif eth_type_val == 2054:
                        parts.append("ARP")
                    elif eth_type_val == 34525:
                        parts.append("IPv6")
                    else:
                        parts.append(f"ETH:{eth_type_val}")
        
        # IP matches
        if 'ipv4-destination' in match:
            parts.append(f"DST:{match['ipv4-destination']}")
        if 'ipv4-source' in match:
            parts.append(f"SRC:{match['ipv4-source']}")
        if 'ipv6-destination' in match:
            parts.append(f"DSTv6:{match['ipv6-destination']}")
        if 'ipv6-source' in match:
            parts.append(f"SRCv6:{match['ipv6-source']}")
        
        # Other matches
        if 'in-port' in match:
            parts.append(f"IN:{match['in-port']}")
        if 'vlan-id' in match:
            parts.append(f"VLAN:{match['vlan-id']}")
        
        return ", ".join(parts) if parts else "Any"
    
    def extract_action_info(self, instructions):
        """Extract human-readable action information"""
        actions = []
        try:
            instruction_list = instructions.get('instruction', [])
            for instr in instruction_list:
                apply_actions = instr.get('apply-actions', {})
                action_list = apply_actions.get('action', [])
                for action in action_list:
                    if 'output-action' in action:
                        output = action['output-action']
                        port = output.get('output-node-connector', 'unknown')
                        if port == 'CONTROLLER':
                            actions.append("CTRL")
                        elif port == 'FLOOD':
                            actions.append("FLOOD")
                        elif port == 'ALL':
                            actions.append("ALL")
                        else:
                            actions.append(f"OUT:{port}")
                    elif 'drop-action' in action:
                        actions.append("DROP")
                    elif 'set-field' in action:
                        actions.append("SET_FIELD")
        except:
            pass
        
        return ", ".join(actions) if actions else "N/A"
    
    def create_flow_table(self, all_flows, total_stats):
        """Create a Rich table with flow statistics"""
        table = Table(
            title=f"Flow Table {self.table} - OpenFlow Flows",
            title_style="bold cyan",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta",
            border_style="bright_blue",
            show_lines=False  # Remove lines between rows
        )
        
        # Add columns
        table.add_column("Node", style="cyan", no_wrap=True)
        table.add_column("Flow", style="green", no_wrap=True)
        table.add_column("Pri", style="yellow", justify="center")
        table.add_column("Match", style="white")
        table.add_column("Action", style="magenta")
        table.add_column("Packets", style="bright_cyan", justify="right")
        table.add_column("Bytes", style="bright_green", justify="right")
        table.add_column("Pkt/s", style="yellow", justify="center")
        table.add_column("B/s", style="yellow", justify="center")
        table.add_column("Uptime", style="dim", justify="right")
        
        # Add rows
        for flow in all_flows:
            table.add_row(
                flow['dpid'],
                flow['flow_id'],
                str(flow['priority']),
                flow['match'][:40] if len(flow['match']) > 40 else flow['match'],
                flow['action'][:20] if len(flow['action']) > 20 else flow['action'],
                self.format_packets(flow['packets']),
                self.format_bytes(flow['bytes']),
                flow['packet_rate'],
                flow['byte_rate'],
                f"{flow['duration']}s"
            )
        
        return table
    
    def create_summary_panel(self, total_stats):
        """Create a summary panel with statistics"""
        summary_text = Text()
        summary_text.append("Total Active Flows: ", style="bold cyan")
        summary_text.append(str(total_stats.get('total_flows', 0)), style="bold white")
        summary_text.append("  |  ")
        summary_text.append("Total Packets: ", style="bold cyan")
        summary_text.append(self.format_packets(total_stats.get('total_packets', 0)), style="bold white")
        summary_text.append("  |  ")
        summary_text.append("Total Bytes: ", style="bold cyan")
        summary_text.append(self.format_bytes(total_stats.get('total_bytes', 0)), style="bold white")
        summary_text.append("\n")
        summary_text.append("Packets Looked Up: ", style="bold cyan")
        summary_text.append(self.format_packets(total_stats.get('packets_looked_up', 0)), style="bold white")
        summary_text.append("  |  ")
        summary_text.append("Packets Matched: ", style="bold cyan")
        summary_text.append(self.format_packets(total_stats.get('packets_matched', 0)), style="bold white")
        
        return Panel(
            summary_text,
            title="Summary Statistics",
            title_align="center",
            border_style="bright_blue",
            padding=(1, 2)
        )
    
    def create_header(self):
        """Create the header panel"""
        header_text = Text()
        header_text.append("ODL Flow Monitor", style="bold orange")
        header_text.append("  |  ")
        header_text.append(f"Table: {self.table}", style="bold cyan")
        header_text.append("  |  ")
        header_text.append(f"Host: {self.host}:{self.port}", style="bold cyan")
        header_text.append("  |  ")
        header_text.append(f"Interval: {self.interval}s", style="bold cyan")
        header_text.append("  |  ")
        header_text.append(f"Nodes: {len(self.nodes_cache)}", style="bold cyan")
        header_text.append("  |  ")
        header_text.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), style="dim")
        
        return Panel(
            Align.center(header_text),
            border_style="bright_blue"
        )
    
    def render(self):
        """Render the complete display"""
        all_flows = []
        total_stats = {
            'total_flows': 0,
            'total_packets': 0,
            'total_bytes': 0,
            'packets_looked_up': 0,
            'packets_matched': 0
        }
        
        for node in self.nodes_cache:
            dpid = node['dpid']
            
            # Get flow table data
            flow_data = self.get_flow_table(dpid)
            if flow_data:
                # Parse flows
                flows = self.parse_flow_stats(flow_data, dpid)
                all_flows.extend(flows)
                
                # Update total statistics
                tables = flow_data.get('flow-node-inventory:table', [])
                for table in tables:
                    table_stats = table.get('opendaylight-flow-table-statistics:flow-table-statistics', {})
                    total_stats['packets_looked_up'] += int(table_stats.get('packets-looked-up', 0))
                    total_stats['packets_matched'] += int(table_stats.get('packets-matched', 0))
                    total_stats['total_flows'] = len(all_flows)
                
                # Accumulate flow statistics
                for flow in flows:
                    total_stats['total_packets'] += int(flow['packets'])
                    total_stats['total_bytes'] += int(flow['bytes'])
        
        # Sort flows
        all_flows.sort(key=lambda x: (x['dpid'], -x['priority']))
        
        # Create display
        header = self.create_header()
        flow_table = self.create_flow_table(all_flows, total_stats)
        summary = self.create_summary_panel(total_stats)
        
        # Return combined renderable
        from rich.console import Group
        return Group(header, flow_table, summary)
    
    def run(self):
        """Run the monitoring loop with Rich Live display"""
        self.console.print("[bold cyan]Getting initial topology...[/bold cyan]")
        
        # Get topology once
        topology = self.get_topology()
        if not topology:
            self.console.print("[red]ERROR: Could not get topology[/red]")
            sys.exit(1)
        
        # Extract nodes
        self.nodes_cache = self.extract_nodes_from_topology(topology)
        if not self.nodes_cache:
            self.console.print("[red]ERROR: No OpenFlow nodes found in topology[/red]")
            sys.exit(1)
        
        self.console.print(f"[green]Found {len(self.nodes_cache)} OpenFlow nodes[/green]")
        self.console.print(f"[green]Monitoring table {self.table} on all nodes...[/green]")
        self.console.print("[yellow]Press Ctrl+C to stop[/yellow]")
        time.sleep(2)
        
        # Use Live display with proper settings
        with Live(
            self.render(),
            refresh_per_second=1,
            screen=True,
            auto_refresh=False  # Manual refresh control
        ) as live:
            while self.running:
                try:
                    # Update the display
                    live.update(self.render(), refresh=True)
                    
                    # Wait for next cycle
                    for _ in range(self.interval):
                        if not self.running:
                            break
                        time.sleep(1)
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    self.console.print(f"[red]Error: {e}[/red]")
                    time.sleep(self.interval)
        
        self.console.print("\n[green]Monitoring finished[/green]")

def main():
    parser = argparse.ArgumentParser(description='OpenDaylight Flow Monitor with Rich UI')
    parser.add_argument('-c', '--controller', default="127.0.0.1", help='ODL host IP address')
    parser.add_argument('--port', type=int, default=8181, help='ODL REST port (default: 8181)')
    parser.add_argument('--user', default='admin', help='Username for authentication (default: admin)')
    parser.add_argument('--password', default='admin', help='Password for authentication (default: admin)')
    parser.add_argument('-t', '--table', type=int, default=0, help='Table ID to monitor (default: 0)')
    parser.add_argument('-i', '--interval', type=int, default=5, help='Update interval in seconds (default: 5)')
    
    args = parser.parse_args()
    
    # Create monitor and run
    monitor = ODLFlowMonitor(
        host=args.controller,
        port=args.port,
        user=args.user,
        password=args.password,
        table=args.table,
        interval=args.interval
    )
    
    monitor.run()

if __name__ == '__main__':
    main()
