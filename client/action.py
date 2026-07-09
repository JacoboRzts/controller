class Action:
    @staticmethod
    def output(port, order=0):
        return {
            "order": order,
            "output-action": {
                "output-node-connector": port,
            }
        }

    @staticmethod
    def group(group, order=0):
        return {
            "order": order,
            "group-action": {
                "group-id": group
            }
        }

    @staticmethod
    def drop(order=0):
        return {
            "order": order,
            "drop-action": {}
        }

    @staticmethod
    def dec_ttl(order=0):
        return {
          "order": order,
          "dec-nw-ttl": {}
        }

    @staticmethod
    def dec_ttl_mpls(order=0):
        return {
          "order": order,
          "dec-mpls-ttl": {}
        }

    @staticmethod
    def meter(meter, order=0):
        return {
            "order": order,
            "meter-action": {
                "meter-id": meter,
            },
        }
