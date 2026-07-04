class Client:
    import requests
    import json
    from pathlib import Path

    def __init__(self, ip="127.0.0.1", port=8181, default_table=0, auth=("admin","admin"), content_type="json"):
        self.ip = ip
        self.port = port
        self.auth = auth
        self.default_table = default_table
        self.url = f"http://{ip}:{port}/rests/data"
        self._rfc = {
            "nodes": f"{self.url}/opendaylight-inventory:nodes",
            "topology": f"{self.url}/network-topology:network-topology"
        }
        self.headers = {
            "Content-Type": f"application/{content_type}",
            "Accept": f"application/{content_type}"
        }

    def test(self):
        try:
            self.requests.get(
                self._rfc["topology"], 
                auth=self.auth, 
                headers=self.headers
            )
            print("The ODL controller is succesfully conected")
        except Exception as e:
            print(f"Error on connection: {e}")

    # -----------------------------------------------------------------------------------------------
    # Toplology 
    # -----------------------------------------------------------------------------------------------
    def getTopology(self):
        try:
            response = self.requests.get(
                self._rfc["topology"],
                auth=self.auth,
                headers=self.headers
            )
            return response.json()
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def getNodesDPID(self, data):
        dpids = []
        topology = data.get('network-topology:network-topology').get('topology')
        for topo in topology:
            nodes = topo.get('node', [])
            for node in nodes:
                node_id = node.get('node-id').replace('openflow:', '')
                if node_id:
                    dpids.append(node_id)
        return dpids

    # -----------------------------------------------------------------------------------------------
    # Nodes
    # -----------------------------------------------------------------------------------------------
    def getNodes(self):
        try:
            dpid = 3
            endpoint = f"{self._rfc["nodes"]}/node=openflow:{dpid}/flow-node-inventory:group=1?content=nonconfig"
            print(endpoint)
            responese = self.requests.get(
                endpoint,
                auth=self.auth,
                headers=self.headers
            )
            return responese.json()
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def getNode(self, dpid):
        try:
            response = self.requests.get(
                f"{self._rfc["nodes"]}/node=openflow:{dpid}?content=nonconfig",
                auth=self.auth,
                headers=self.headers
            )
            return response.json()
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def showNode(self, dpid):
        node = self.getNode(dpid)
        if node is not None:
            print(node) 
            # id = node["opendaylight-inventory:node"][0]["id"].split(':')[1]
            # print(node["opendaylight-inventory:node"][0]["flow-node-inventory:table"])


    # -----------------------------------------------------------------------------------------------
    # Flows
    # -----------------------------------------------------------------------------------------------
    def setFlow(self, dpid, flow, save=False):
        id = flow["id"]
        table = flow["table_id"]
        data = { "flow-node-inventory:flow": [flow] }
        response = self.requests.put(
            f"{self._rfc["nodes"]}/node=openflow:{dpid}/flow-node-inventory:table={table}/flow={id}",
            auth=self.auth,
            headers=self.headers,
            data=self.json.dumps(data)
        )

        if save:
            self.saveFlow(flow, id, path="saved")
        print(f"[{response.status_code}] DPID: {dpid} FLOW ID: {flow["id"]} FLOW NAME: {flow["flow-name"]}")

    def getFlow(self, dpid, flow_id, table=None):
        table = table or self.default_table
        response = self.requests.get(
            f"{self._rfc["nodes"]}/node=openflow:{dpid}/flow-node-inventory:table={table}/flow={flow_id}",
            auth=self.auth,
            headers=self.headers
        )
        print(f"[{response.status_code} ]DPID:{dpid} FLOW:{flow_id}")
        return response.json()

    def deleteFlow(self, dpid, id, table=None):
        """Delete a specific flow in a given node and table.
        Args: 
            dpid: DataPathID of the node.
            id: Flow id to be deleted.
            table: Table ID where the flow is.
        """
        table = table or self.default_table 
        response = self.requests.delete(
            f"{self._rfc["nodes"]}/node=openflow:{dpid}/flow-node-inventory:table={table}/flow={id}",
            auth=self.auth,
            headers=self.headers
        )
        print(f"[{response.status_code}] DPID:{dpid} FLOW:{id}")

    def getFlows(self, dpid, table=None):
        """ Get all the flow from an specific table on an specific node.
        Args: 
            dpid (int): DataPathID is the node identifier.
            table (int): Table ID, if is not specified uses the Client default table.
        Returns:
            list[dict]: An array of all the flows finded in the specific table and node.
        """
        table = table or self.default_table
        try:
            response = self.requests.get(
                f"{self._rfc["nodes"]}/node=openflow:{dpid}/flow-node-inventory:table={table}",
                auth=self.auth,
                headers=self.headers
            )
            data = response.json()
            table = data.get("flow-node-inventory:table", [])
            return table[0].get("flow") if table else None
        except Exception as e:
            print(f"Error: {e}")
            return None

    def deleteFlows(self, dpid, table=None):
        """Delete all the flows in a given node and table
        Args:
            dpid: DataPathID of the node.
            table: Table ID where the flows are.
        """
        table = table or self.default_table
        response = self.requests.delete(
            f"{self._rfc["nodes"]}/node=openflow:{dpid}/flow-node-inventory:table={table}",
            auth=self.auth,
            headers=self.headers
        )
        print(f"[{response.status_code}] DPID:{dpid} TABLE:{table}")


    def printFlows(self, dpid, flows, table=None):
        table = table or self.default_table
        for flow in flows:
            name = flow.get("flow-name", "-")
            print(f"{dpid:<16} {str(table).zfill(3)} {flow['id']:<14} {name:<32}")

    def saveFlow(self, flow: dict, name: str, path: str = ".") -> Path:
        """Guarda un flow en un archivo JSON.
        Args:
            flow: flow dict.
            name: filename without extension.
            path: Filepath.
        Returns:
            Path where the file was saved.
        Raises:
            OSError: Si no se puede escribir en el directorio.
        """
        dest = self.Path(path) / f"{name}.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(dest, "w", encoding="utf-8") as f:
                self.json.dump(flow, f, ensure_ascii=False, indent=2)
        except OSError as e:
            raise OSError(f"The flow cant be saved on '{dest}': {e}") from e
        return dest

    # -----------------------------------------------------------------------------------------------
    # Groups
    # -----------------------------------------------------------------------------------------------
    def setGroup(self, dpid, group, save=False):
        id = group["group-id"]
        data = { "flow-node-inventory:group": [group] }
        response = self.requests.put(
            f"{self.url}/opendaylight-inventory:nodes/node=openflow:{dpid}/flow-node-inventory:group={id}",
            auth=self.auth,
            headers=self.headers,
            data=self.json.dumps(data)
        )
        print(f"[{response.status_code}] DPID:{dpid} GROUP ID:{group["group-id"]}")
        if save:
            name = f"saved/{dpid}_{id}.json"
            with open(name, "w") as file:
                self.json.dump(data, file)
