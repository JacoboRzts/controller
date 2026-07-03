class Action:
    def output(self, port, order=0):
        return {
            "order": order,
            "output-action": {
                "output-node-connector": port,
            }
        }

    def group(self, group, order=0):
        return {
            "order": order,
            "group-action": {
                "group-id": group
            }
        }

    def drop(self, order=0):
        return {
            "order": order,
            "drop-action": {}
        }

    def dec_ttl(self, order=0):
        return {
          "order": order,
          "dec-nw-ttl": {}
        }

    def dec_ttl_mpls(self, order=0):
        return {
          "order": order,
          "dec-mpls-ttl": {}
        }
