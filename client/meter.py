class Meter:
    def __new__(cls):
        return {
            "flow-node-inventory:meter": [
                {
                "meter-id": 1,
                "barrier": False,
                "meter-name": "meter-uplink-spine1",
                "flags": "meter-kbps meter-burst meter-stats",
                "meter-band-headers": {
                    "meter-band-header": [
                    {
                        "band-id": 0,
                        "band-rate": 500000,
                        "band-burst-size": 5000,
                        "meter-band-types": {
                        "flags": "ofpmbt-dscp-remark"
                        },
                        "drop-rate": 500000,
                        "drop-burst-size": 5000
                    }
                    ]
                }
                }
            ]
        }
