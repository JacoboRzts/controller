class Match:
    @staticmethod
    def eth(src_ip=None, dst_ip=None , port=None):
        match = {
            "ethernet-match": {
                "ethernet-type": {"type": 2048}
            },
        }
        if port is not None:
            match["in-port"] = port
        if src_ip is not None:
            match["ipv4-source"] = src_ip
        if dst_ip is not None:
            match["ipv4-destination"] = dst_ip
        return match

    @staticmethod
    def arp():
        return {
            "ethernet-match": {
                "ethernet-type": {
                    "type": 2054
                }
            }
        }

    @staticmethod
    def dscp(dscp):
        return {
            "ethernet-match": {
                "ethernet-type": {
                    "type": 2048
                }
            },
            "ip-match": {
                "ip-dscp": dscp
            }
        }
