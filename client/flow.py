class Flow:
    def __new__(cls, id, name: str, table:int, priority:int,  match: dict, instructions: list[dict]):
        """Create an flow dictionary.
        Args: 
            id (str): Flow id to be created
            name (str): Flow name, optional.
            table (int): Table ID to load the flow
            priority (int): Priority of the flow to be executed (high number represent high priority).
            match (dict): A dictionary with the match flow parameters.
            instructions (list[dict]): A list of instructions. 
        """
        return {
            "id": id,
            "table_id": table,
            "flow-name": name,
            "priority": priority,
            "match": match,
            "instructions": {
                "instruction": instructions
            }
        }
