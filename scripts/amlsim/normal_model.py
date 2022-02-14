class NormalModel:
    def __init__(self, id, type, node_ids, main_id):
        self.id = id 
        self.type = type
        self.node_ids = node_ids or set()
        self.main_id = main_id


    def add_account(self, id):
        self.node_ids.add(id)


    def is_main(self, node_id):
        return node_id == self.main_id


    def remove_node_ids(self, node_ids):
        self.node_ids = self.node_ids - node_ids


    def node_ids_without_main(self):
        return self.node_ids - { self.main_id }


