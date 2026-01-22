from storage_config import StorageConfig


def test_storage_config_is_singleton():
    first = StorageConfig()
    second = StorageConfig()

    assert first is second
    assert first.storage_dir == second.storage_dir
