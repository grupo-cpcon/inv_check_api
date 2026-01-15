from bson import ObjectId


class ItemStoragePaths:
    def __init__(self, client_name: str, item_id: ObjectId):
        self.client_name = client_name
        self.item_id = item_id
    
    @property
    def root(self) -> str:
        return f"multi-tenant/client/{self.client_name}/inventory-checks/{str(self.item_id)}"

    @property
    def images(self) -> str:
        return f"{self.root}/images"