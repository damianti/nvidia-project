import os
import tarfile
import zipfile
from fastapi import HTTPException


def _is_within_directory(directory: str, target: str) -> bool:
    directory = os.path.realpath(directory)
    target = os.path.realpath(target)
    return os.path.commonpath([directory]) == os.path.commonpath([directory, target])


def safe_extract_tar(tar_path: str, dest_dir: str) -> None:
    with tarfile.open(tar_path, "r:*") as tar:
        for member in tar.getmembers():
            target_path = os.path.join(dest_dir, member.name)
            if not _is_within_directory(dest_dir, target_path):
                raise HTTPException(status_code=400, detail="Invalid tar: unsafe path")
        tar.extractall(dest_dir)


def safe_extract_zip(zip_path: str, dest_dir: str) -> None:
    with zipfile.ZipFile(zip_path) as z:
        for name in z.namelist():
            target_path = os.path.join(dest_dir, name)
            if not _is_within_directory(dest_dir, target_path):
                raise HTTPException(status_code=400, detail="Invalid zip: unsafe path")
        z.extractall(dest_dir)
