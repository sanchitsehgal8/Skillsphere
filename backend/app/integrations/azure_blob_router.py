from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.auth import get_current_user
from app.integrations.azure_blob import azure_blob_storage


router = APIRouter(prefix="/azure-blob", tags=["azure-blob"])


def _owner_id(user: dict) -> str:
    owner = str(user.get("id") or user.get("sub") or user.get("user_id") or "").strip()
    if not owner:
        raise HTTPException(status_code=401, detail="Invalid auth token payload")
    return owner


@router.get("/health")
async def health() -> dict[str, object]:
    return {
        "success": True,
        "data": {
            "configured": bool(
                azure_blob_storage.config.connection_string or azure_blob_storage.config.account_url
            ),
            "container": azure_blob_storage.config.container_name,
        },
    }


@router.post("/upload/{category}/{item_id}")
async def upload_blob(
    category: str,
    item_id: str,
    file: UploadFile = File(...),
    user=Depends(get_current_user),
) -> dict[str, object]:
    owner_id = _owner_id(user)
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        return azure_blob_storage.upload_bytes(
            category=category,
            owner_id=owner_id,
            item_id=item_id,
            data=raw,
            original_filename=file.filename,
            content_type=file.content_type,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete("/delete/{category}/{item_id}")
async def delete_blob(
    category: str,
    item_id: str,
    blob_name: str,
    user=Depends(get_current_user),
) -> dict[str, object]:
    owner_id = _owner_id(user)
    expected_prefix = f"{category}/{owner_id}/{item_id}/"
    if not blob_name.startswith(expected_prefix):
        raise HTTPException(status_code=400, detail="Blob name does not match the current user scope.")

    try:
        deleted = azure_blob_storage.delete_blob(blob_name)
        return {"success": True, "data": {"deleted": deleted, "blob_name": blob_name}}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
