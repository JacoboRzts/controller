class Instruction:
    def apply(self, actions, order=0):
        return {
            "order": order,
            "apply-actions": {
                "action": actions
            }
        }

    def meter(self, meter_id, order=0):
        return {
            "order": order,
            "meter": {
                "meter-id": meter_id
            }
        }

    def table(self, table_id, order=0):
        return {
            "order": order,
            "go-to-table": {
                "table_id": table_id
            }
        }
