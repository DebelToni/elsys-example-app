from pathlib import Path


class StorageConfig:
    _instance = None

    def __new__(cls, storage_dir="storage"):
        if cls._instance is None:
            instance = super().__new__(cls)
            instance.storage_dir = Path(storage_dir)
            instance.storage_dir.mkdir(exist_ok=True)
            cls._instance = instance
        return cls._instance
