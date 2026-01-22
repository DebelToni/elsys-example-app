import os
import random
import uuid
from io import BytesIO

from locust import HttpUser, between, task


class FileStorageUser(HttpUser):
    """
    Simulates concurrent clients interacting with the File Storage API.
    Covers upload, download, listing, health, and metrics endpoints.
    """

    wait_time = between(0.3, 1.2)

    def on_start(self):
        self.created_files: list[str] = []
        # Ensure at least one file exists for download tests.
        self._upload_random_file(prefix="seed")

    def _upload_random_file(self, prefix: str = "locust"):
        filename = f"{prefix}-{uuid.uuid4().hex}.bin"
        file_obj = BytesIO(os.urandom(random.randint(512, 2048)))
        file_obj.seek(0)
        files = {"file": (filename, file_obj, "application/octet-stream")}

        with self.client.post(
            "/files",
            files=files,
            name="/files [POST]",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                self.created_files.append(filename)
                # Keep a rolling window of known files to avoid unbounded
                # growth.
                if len(self.created_files) > 32:
                    self.created_files.pop(0)
            else:
                response.failure(f"Upload failed: {response.text}")

    @task(3)
    def upload_file(self):
        self._upload_random_file()

    @task(2)
    def download_file(self):
        if not self.created_files:
            # If all downloads failed earlier, seed a new file.
            self._upload_random_file(prefix="fallback")
            return

        filename = random.choice(self.created_files)
        self.client.get(f"/files/{filename}", name="/files/{filename}")

    @task(2)
    def list_files(self):
        response = self.client.get("/files")
        if response.status_code == 200:
            # Merge known files with server response to maximize successful
            # downloads.
            server_files = response.json().get("files", [])
            combined = set(self.created_files)
            combined.update(server_files)
            self.created_files = list(combined)[:32]

    @task(1)
    def get_health(self):
        self.client.get("/health")

    @task(1)
    def get_metrics(self):
        self.client.get("/metrics")

    @task(1)
    def view_root(self):
        self.client.get("/")
