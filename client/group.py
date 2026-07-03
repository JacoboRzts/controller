class Group: 
    def __new__(cls, id, name, type, buckets, barrier=False):
        return {
            "group-id": id,
            "group-name": name,
            "group-type": type,
            "barrier": barrier,
            "buckets": {
                "bucket": buckets,
            }
        }
