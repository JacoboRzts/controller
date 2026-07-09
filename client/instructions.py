class Instruction:
    @staticmethod
    def apply(actions, order=0):
        return {
            "order": order,
            "apply-actions": {
                "action": actions
            }
        }

    @staticmethod
    def meter(meter_id, order=0):
        return {
            "order": order,
            "meter": {
                "meter-id": meter_id
            }
        }

    @staticmethod
    def table(table_id, order=0):
        return {
            "order": order,
            "go-to-table": {
                "table_id": table_id
            }
        }
