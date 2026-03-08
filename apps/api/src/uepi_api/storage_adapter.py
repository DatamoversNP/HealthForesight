"""File storage adapter - supports both local and Azure File Storage"""
import os
from pathlib import Path
from typing import Optional, Union

from uepi_api.config import get_settings

settings = get_settings()


def get_storage_adapter():
    """Get the appropriate storage adapter based on configuration
    
    Returns:
        Either AzureFileStorageAdapter or LocalFileSystemAdapter
    """
    if settings.use_azure_file_storage:
        # Use Azure File Storage
        from uepi_api.storage import AzureFileStorageAdapter, AZURE_FILE_STORAGE_AVAILABLE
        
        if not AZURE_FILE_STORAGE_AVAILABLE:
            raise ImportError(
                "Azure File Storage is enabled but azure-storage-file-share is not installed. "
                "Install it with: pip install azure-storage-file-share"
            )
        
        # Get Azure credentials
        account_name = settings.azure_storage_account_name
        account_key = settings.azure_storage_account_key
        connection_string = settings.azure_storage_connection_string
        share_name = settings.azure_storage_file_share_name
        
        if not account_name:
            raise ValueError(
                "Azure File Storage is enabled but AZURE_STORAGE_ACCOUNT_NAME is not set"
            )
        
        if not (account_key or connection_string):
            raise ValueError(
                "Azure File Storage is enabled but neither AZURE_STORAGE_ACCOUNT_KEY "
                "nor AZURE_STORAGE_CONNECTION_STRING is set"
            )
        
        # Create Azure adapter
        return AzureFileStorageAdapter(
            account_name=account_name,
            account_key=account_key,
            connection_string=connection_string,
            share_name=share_name,
            base_path="",  # Can be configured if needed
        )
    else:
        # Use local file system (default)
        return LocalFileSystemAdapter(base_path=settings.storage_path)


class LocalFileSystemAdapter:
    """Local file system adapter - simple wrapper around Path operations
    
    This provides the same interface as AzureFileStorageAdapter,
    allowing code to work with both local and Azure storage.
    """
    
    def __init__(self, base_path: str = "./data"):
        """Initialize local file system adapter
        
        Args:
            base_path: Base path for local file storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _normalize_path(self, path: Union[str, Path]) -> Path:
        """Normalize path relative to base_path"""
        if isinstance(path, Path):
            path = str(path)
        
        # Remove leading ./ or .\ or /
        path = path.lstrip("./\\")
        
        # Make relative to base_path
        return self.base_path / path
    
    def exists(self, path: Union[str, Path]) -> bool:
        """Check if file or directory exists"""
        normalized_path = self._normalize_path(path)
        return normalized_path.exists()
    
    def read_file(self, path: Union[str, Path]) -> bytes:
        """Read file content as bytes"""
        normalized_path = self._normalize_path(path)
        if not normalized_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return normalized_path.read_bytes()
    
    def read_text(self, path: Union[str, Path], encoding: str = "utf-8") -> str:
        """Read file content as text"""
        normalized_path = self._normalize_path(path)
        if not normalized_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return normalized_path.read_text(encoding=encoding)
    
    def read_json(self, path: Union[str, Path]) -> dict:
        """Read JSON file and parse it"""
        import json
        text = self.read_text(path)
        return json.loads(text)
    
    def write_file(self, path: Union[str, Path], content: Union[bytes, str], encoding: str = "utf-8"):
        """Write content to file"""
        normalized_path = self._normalize_path(path)
        normalized_path.parent.mkdir(parents=True, exist_ok=True)
        
        if isinstance(content, str):
            normalized_path.write_text(content, encoding=encoding)
        else:
            normalized_path.write_bytes(content)
    
    def write_text(self, path: Union[str, Path], content: str, encoding: str = "utf-8"):
        """Write text content to file"""
        self.write_file(path, content.encode(encoding))
    
    def write_json(self, path: Union[str, Path], data: dict, indent: int = 2):
        """Write JSON data to file"""
        import json
        content = json.dumps(data, indent=indent, default=str)
        self.write_text(path, content)
    
    def delete_file(self, path: Union[str, Path]):
        """Delete a file"""
        normalized_path = self._normalize_path(path)
        if normalized_path.exists():
            normalized_path.unlink()
    
    def mkdir(self, path: Union[str, Path], parents: bool = True):
        """Create directory (and parent directories if parents=True)"""
        normalized_path = self._normalize_path(path)
        normalized_path.mkdir(parents=parents, exist_ok=True)
    
    def mkdir_for_file(self, file_path: Union[str, Path]):
        """Create parent directories for a file"""
        normalized_path = self._normalize_path(file_path)
        normalized_path.parent.mkdir(parents=True, exist_ok=True)
    
    def list_files(self, directory: Union[str, Path], pattern: Optional[str] = None) -> list[str]:
        """List files in a directory"""
        normalized_path = self._normalize_path(directory)
        if not normalized_path.exists():
            return []
        
        files = []
        for item in normalized_path.iterdir():
            if item.is_file():
                file_name = item.name
                if pattern:
                    import fnmatch
                    if fnmatch.fnmatch(file_name, pattern):
                        files.append(file_name)
                else:
                    files.append(file_name)
        
        return files
    
    def list_directories(self, directory: Union[str, Path]) -> list[str]:
        """List subdirectories in a directory"""
        normalized_path = self._normalize_path(directory)
        if not normalized_path.exists():
            return []
        
        directories = []
        for item in normalized_path.iterdir():
            if item.is_dir():
                directories.append(item.name)
        
        return directories
    
    def glob(self, pattern: Union[str, Path]) -> list[str]:
        """Find files matching a glob pattern"""
        normalized_pattern = self._normalize_path(pattern)
        
        # Get relative paths from base_path
        base_path_str = str(self.base_path)
        matches = []
        
        for match_path in normalized_pattern.parent.glob(normalized_pattern.name):
            if match_path.is_file():
                # Get relative path from base_path
                rel_path = str(match_path.relative_to(self.base_path))
                matches.append(rel_path.replace("\\", "/"))  # Normalize path separators
        
        return matches
