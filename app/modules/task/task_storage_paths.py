from bson import ObjectId


class TaskStoragePaths:
    def __init__(self, client_name: str):
        self.client_name = client_name

    @property
    def root(self) -> str:
        return f"multi-tenant/client/{self.client_name}/tasks"

    def async_task(self, task_id: ObjectId) -> str:
        return f"{self.root}/async/{str(task_id)}"