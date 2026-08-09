from __future__ import annotations

import mimetypes
import os
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Optional

try:
    from azure.identity import DefaultAzureCredential
    from azure.storage.blob import BlobServiceClient, ContentSettings
except ImportError as exc:  # pragma: no cover - optional integration dependency
    raise RuntimeError(
        "Azure Blob support requires the optional azure-storage-blob and azure-identity packages."
    ) from exc


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    cleaned = cleaned.strip(".-_")
    return cleaned or "item"


@dataclass(frozen=True)
class AzureBlobConfig:
    connection_string: str = _env("AZURE_STORAGE_CONNECTION_STRING")
    account_url: str = _env("AZURE_STORAGE_ACCOUNT_URL")
    container_name: str = _env("AZURE_STORAGE_CONTAINER_NAME", "skillsphere")


class AzureBlobStorage:
    def __init__(self, config: Optional[AzureBlobConfig] = None) -> None:
        self.config = config or AzureBlobConfig()
        self._client: Optional[BlobServiceClient] = None

    def _client_or_raise(self) -> BlobServiceClient:
        if self._client is not None:
            return self._client

        if self.config.connection_string:
            self._client = BlobServiceClient.from_connection_string(self.config.connection_string)
            return self._client

        if self.config.account_url:
            self._client = BlobServiceClient(
                account_url=self.config.account_url,
                credential=DefaultAzureCredential(),
            )
            return self._client

        raise RuntimeError(
            "Azure Blob is not configured. Set AZURE_STORAGE_CONNECTION_STRING or AZURE_STORAGE_ACCOUNT_URL."
        )

    def container_client(self, container_name: Optional[str] = None):
        name = container_name or self.config.container_name
        return self._client_or_raise().get_container_client(name)

    def ensure_container(self, container_name: Optional[str] = None) -> str:
        name = container_name or self.config.container_name
        client = self.container_client(name)
        try:
            client.create_container()
        except Exception:
            pass
        return name

    def blob_path(
        self,
        category: str,
        owner_id: str,
        item_id: str,
        original_filename: Optional[str] = None,
    ) -> str:
        parts = [
            _slug(category),
            _slug(owner_id),
            _slug(item_id),
        ]
        if original_filename:
            parts.append(_slug(PurePosixPath(original_filename).name))
        return str(PurePosixPath(*parts))

    def upload_bytes(
        self,
        *,
        category: str,
        owner_id: str,
        item_id: str,
        data: bytes,
        original_filename: Optional[str] = None,
        content_type: Optional[str] = None,
        container_name: Optional[str] = None,
        overwrite: bool = True,
        metadata: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        if not data:
            raise ValueError("Cannot upload an empty payload to Azure Blob Storage.")

        container = self.ensure_container(container_name)
        blob_name = self.blob_path(category, owner_id, item_id, original_filename)
        blob = self.container_client(container).get_blob_client(blob_name)

        final_content_type = content_type or mimetypes.guess_type(original_filename or "")[0] or "application/octet-stream"
        blob.upload_blob(
            data,
            overwrite=overwrite,
            metadata=metadata,
            content_settings=ContentSettings(content_type=final_content_type),
        )

        return {
            "container": container,
            "blob_name": blob_name,
            "url": blob.url,
            "content_type": final_content_type,
        }

    def download_bytes(self, blob_name: str, container_name: Optional[str] = None) -> bytes:
        blob = self.container_client(container_name).get_blob_client(blob_name)
        return blob.download_blob().readall()

    def delete_blob(self, blob_name: str, container_name: Optional[str] = None) -> bool:
        blob = self.container_client(container_name).get_blob_client(blob_name)
        blob.delete_blob(delete_snapshots="include")
        return True


azure_blob_storage = AzureBlobStorage()
