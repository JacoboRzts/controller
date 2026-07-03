class Bucket:
    def __new__(cls, id, actions):
        return {
            "bucket-id": id,
            "action": actions
        }
    
    @staticmethod
    def ff(id, watch_type, watch_value, actions):
        return {
            "bucket-id": id,
            f"watch_{watch_type}": watch_value,
            "action": actions
        }
    
    @staticmethod
    def select(id, weigth, actions):
        return {
            "bucket-id": id,
            "weight": weigth,
            "action": actions
        }
