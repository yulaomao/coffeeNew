import hashlib
from typing import Union, BinaryIO
from pathlib import Path

def md5_hash(data: Union[str, bytes, Path, BinaryIO]) -> str:
    """Calculate MD5 hash of data"""
    hasher = hashlib.md5()
    
    if isinstance(data, str):
        hasher.update(data.encode('utf-8'))
    elif isinstance(data, bytes):
        hasher.update(data)
    elif isinstance(data, Path):
        with open(data, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
    else:  # BinaryIO
        for chunk in iter(lambda: data.read(4096), b""):
            hasher.update(chunk)
    
    return hasher.hexdigest()

def sha256_hash(data: Union[str, bytes, Path, BinaryIO]) -> str:
    """Calculate SHA256 hash of data"""
    hasher = hashlib.sha256()
    
    if isinstance(data, str):
        hasher.update(data.encode('utf-8'))
    elif isinstance(data, bytes):
        hasher.update(data)
    elif isinstance(data, Path):
        with open(data, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
    else:  # BinaryIO
        for chunk in iter(lambda: data.read(4096), b""):
            hasher.update(chunk)
    
    return hasher.hexdigest()

def verify_file_hash(file_path: Path, expected_hash: str, hash_type: str = "md5") -> bool:
    """Verify file hash matches expected value"""
    try:
        if hash_type.lower() == "md5":
            actual_hash = md5_hash(file_path)
        elif hash_type.lower() == "sha256":
            actual_hash = sha256_hash(file_path)
        else:
            raise ValueError(f"Unsupported hash type: {hash_type}")
        
        return actual_hash.lower() == expected_hash.lower()
    except Exception:
        return False