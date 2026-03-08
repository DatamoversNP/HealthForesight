"""Azure File Storage adapter - simple file system replacement"""
import os
import json
from pathlib import Path
from typing import Optional, List, BinaryIO, Union, TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from azure.storage.fileshare import ShareFileClient, ShareDirectoryClient, ShareClient

try:
    from azure.storage.fileshare import ShareFileClient, ShareDirectoryClient, ShareClient
    from azure.core.exceptions import ResourceNotFoundError, HttpResponseError
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    ShareFileClient = None
    ShareDirectoryClient = None
    ShareClient = None
    ResourceNotFoundError = Exception
    HttpResponseError = Exception


class AzureFileStorageAdapter:
    """Azure File Storage adapter - simple replacement for local file system
    
    This adapter provides a Path-like interface for Azure File Share,
    allowing existing file-based storage code to work with Azure without changes.
    """
    
    def __init__(
        self,
        account_name: str,
        account_key: Optional[str] = None,
        connection_string: Optional[str] = None,
        share_name: str = "healthforesight-data",
        base_path: str = "",
    ):
        """Initialize Azure File Storage adapter
        
        Args:
            account_name: Azure Storage account name
            account_key: Azure Storage account key (if not using connection string)
            connection_string: Azure Storage connection string (alternative to account_key)
            share_name: Name of the Azure File Share
            base_path: Base path within the share (default: root of share)
        """
        if not AZURE_AVAILABLE:
            raise ImportError(
                "azure-storage-file-share is not installed. "
                "Install it with: pip install azure-storage-file-share"
            )
        
        self.account_name = account_name
        self.share_name = share_name
        self.base_path = base_path.strip("/")  # Remove leading/trailing slashes
        
        # Initialize ShareClient
        if connection_string:
            self.share_client = ShareClient.from_connection_string(
                connection_string, share_name=share_name
            )
        elif account_key:
            account_url = f"https://{account_name}.file.core.windows.net"
            self.share_client = ShareClient(
                account_url=account_url,
                share_name=share_name,
                credential=account_key
            )
        else:
            raise ValueError("Either account_key or connection_string must be provided")
        
        # Create share if it doesn't exist
        try:
            self.share_client.get_share_properties()
        except ResourceNotFoundError:
            try:
                self.share_client.create_share()
            except HttpResponseError as e:
                # Share might have been created by another process
                if e.status_code != 409:  # 409 = Conflict (share already exists)
                    raise
    
    def _normalize_path(self, path: Union[str, Path]) -> str:
        """Normalize path to Azure File Share format
        
        Args:
            path: Local path (e.g., "./data/policies/policy-123.json" or "policies/policy-123.json")
            
        Returns:
            Normalized path for Azure (e.g., "policies/policy-123.json")
        """
        # Convert Path to string
        if isinstance(path, Path):
            path = str(path)
        
        # Remove leading ./ or .\ or /
        path = path.lstrip("./\\")
        
        # If base_path is set, prepend it
        if self.base_path:
            if path:
                return f"{self.base_path}/{path}".replace("//", "/")
            return self.base_path
        
        return path
    
    def _get_file_client(self, file_path: str) -> "ShareFileClient":
        """Get ShareFileClient for a file path"""
        normalized_path = self._normalize_path(file_path)
        return self.share_client.get_file_client(normalized_path)
    
    def _get_directory_client(self, dir_path: str) -> "ShareDirectoryClient":
        """Get ShareDirectoryClient for a directory path"""
        normalized_path = self._normalize_path(dir_path)
        return self.share_client.get_directory_client(normalized_path)
    
    def exists(self, path: Union[str, Path]) -> bool:
        """Check if file or directory exists"""
        try:
            normalized_path = self._normalize_path(path)
            # Try as file first
            file_client = self.share_client.get_file_client(normalized_path)
            try:
                file_client.get_file_properties()
                return True
            except ResourceNotFoundError:
                # Try as directory
                dir_client = self.share_client.get_directory_client(normalized_path)
                try:
                    dir_client.get_directory_properties()
                    return True
                except ResourceNotFoundError:
                    return False
        except Exception:
            return False
    
    def read_file(self, path: Union[str, Path]) -> bytes:
        """Read file content as bytes"""
        try:
            file_client = self._get_file_client(path)
            download = file_client.download_file()
            return download.readall()
        except ResourceNotFoundError:
            raise FileNotFoundError(f"File not found: {path}")
    
    def read_text(self, path: Union[str, Path], encoding: str = "utf-8") -> str:
        """Read file content as text"""
        content = self.read_file(path)
        return content.decode(encoding)
    
    def read_json(self, path: Union[str, Path]) -> dict:
        """Read JSON file and parse it"""
        text = self.read_text(path)
        return json.loads(text)
    
    def write_file(self, path: Union[str, Path], content: Union[bytes, str], encoding: str = "utf-8"):
        """Write content to file"""
        # Ensure directory exists
        self.mkdir_for_file(path)
        
        # Convert string to bytes if needed
        if isinstance(content, str):
            content = content.encode(encoding)
        
        file_client = self._get_file_client(path)
        file_client.upload_file(content)
    
    def write_text(self, path: Union[str, Path], content: str, encoding: str = "utf-8"):
        """Write text content to file"""
        self.write_file(path, content.encode(encoding))
    
    def write_json(self, path: Union[str, Path], data: dict, indent: int = 2):
        """Write JSON data to file"""
        content = json.dumps(data, indent=indent, default=str)
        self.write_text(path, content)
    
    def delete_file(self, path: Union[str, Path]):
        """Delete a file"""
        try:
            file_client = self._get_file_client(path)
            file_client.delete_file()
        except ResourceNotFoundError:
            # File doesn't exist, that's okay
            pass
    
    def mkdir(self, path: Union[str, Path], parents: bool = True):
        """Create directory (and parent directories if parents=True)"""
        normalized_path = self._normalize_path(path)
        
        if not normalized_path:
            return  # Root directory
        
        # Create parent directories if needed
        if parents:
            parts = normalized_path.split("/")
            for i in range(1, len(parts) + 1):
                parent_path = "/".join(parts[:i])
                try:
                    dir_client = self.share_client.get_directory_client(parent_path)
                    dir_client.create_directory()
                except HttpResponseError as e:
                    if e.status_code != 409:  # 409 = Already exists
                        raise
        else:
            # Create only this directory
            dir_client = self.share_client.get_directory_client(normalized_path)
            try:
                dir_client.create_directory()
            except HttpResponseError as e:
                if e.status_code != 409:  # 409 = Already exists
                    raise
    
    def mkdir_for_file(self, file_path: Union[str, Path]):
        """Create parent directories for a file"""
        normalized_path = self._normalize_path(file_path)
        if "/" in normalized_path:
            parent_dir = "/".join(normalized_path.split("/")[:-1])
            if parent_dir:
                self.mkdir(parent_dir, parents=True)
    
    def list_files(self, directory: Union[str, Path], pattern: Optional[str] = None) -> List[str]:
        """List files in a directory
        
        Args:
            directory: Directory path
            pattern: Optional pattern to filter files (e.g., "*.json")
            
        Returns:
            List of file names (relative to directory)
        """
        normalized_path = self._normalize_path(directory)
        
        try:
            dir_client = self.share_client.get_directory_client(normalized_path)
            files_and_dirs = dir_client.list_directories_and_files()
            
            files = []
            for item in files_and_dirs:
                if not item.is_directory:
                    file_name = item.name
                    if pattern:
                        # Simple pattern matching (supports * wildcard)
                        import fnmatch
                        if fnmatch.fnmatch(file_name, pattern):
                            files.append(file_name)
                    else:
                        files.append(file_name)
            
            return files
        except ResourceNotFoundError:
            return []
    
    def list_directories(self, directory: Union[str, Path]) -> List[str]:
        """List subdirectories in a directory"""
        normalized_path = self._normalize_path(directory)
        
        try:
            dir_client = self.share_client.get_directory_client(normalized_path)
            files_and_dirs = dir_client.list_directories_and_files()
            
            directories = []
            for item in files_and_dirs:
                if item.is_directory:
                    directories.append(item.name)
            
            return directories
        except ResourceNotFoundError:
            return []
    
    def glob(self, pattern: Union[str, Path]) -> List[str]:
        """Find files matching a glob pattern
        
        Args:
            pattern: Glob pattern (e.g., "policies/*.json")
            
        Returns:
            List of matching file paths
        """
        # Simple glob implementation for Azure File Share
        normalized_pattern = self._normalize_path(pattern)
        
        # Split pattern into directory and filename pattern
        if "/" in normalized_pattern:
            parts = normalized_pattern.rsplit("/", 1)
            directory = parts[0]
            file_pattern = parts[1] if len(parts) > 1 else "*"
        else:
            directory = ""
            file_pattern = normalized_pattern
        
        # List files in directory
        files = self.list_files(directory, pattern=file_pattern)
        
        # Build full paths
        if directory:
            return [f"{directory}/{f}" for f in files]
        return files
