"""Detect and parse different file formats"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
import polars as pl


class FormatDetector:
    """Detect file format and parse accordingly"""
    
    @staticmethod
    def detect_format(file_path: str | Path) -> str:
        """Detect file format from extension or content"""
        path = Path(file_path)
        ext = path.suffix.lower()
        
        format_map = {
            '.csv': 'csv',
            '.json': 'json',
            '.parquet': 'parquet',
            '.xlsx': 'excel',
            '.xls': 'excel',
            '.tsv': 'tsv',
        }
        
        if ext in format_map:
            return format_map[ext]
        
        # Try to detect from content
        try:
            with open(path, 'rb') as f:
                header = f.read(100)
                if header.startswith(b'{') or header.startswith(b'['):
                    return 'json'
                elif header.startswith(b'PK'):
                    return 'excel'  # Excel files are ZIP archives
        except Exception:
            pass
        
        return 'csv'  # Default to CSV
    
    @staticmethod
    def parse_file(file_path: str | Path, format: Optional[str] = None) -> pd.DataFrame:
        """Parse file into pandas DataFrame"""
        path = Path(file_path)
        format = format or FormatDetector.detect_format(path)
        
        try:
            if format == 'csv' or format == 'tsv':
                sep = '\t' if format == 'tsv' else ','
                # Try different encodings
                for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
                    try:
                        return pd.read_csv(path, sep=sep, encoding=encoding, low_memory=False)
                    except UnicodeDecodeError:
                        continue
                raise ValueError(f"Could not decode file with any supported encoding")
            
            elif format == 'json':
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Handle different JSON structures
                if isinstance(data, list):
                    return pd.DataFrame(data)
                elif isinstance(data, dict):
                    # Check if it's a nested structure
                    if 'data' in data:
                        return pd.DataFrame(data['data'])
                    elif 'records' in data:
                        return pd.DataFrame(data['records'])
                    else:
                        # Try to find array-like structure
                        for key, value in data.items():
                            if isinstance(value, list) and len(value) > 0:
                                return pd.DataFrame(value)
                        # Single record
                        return pd.DataFrame([data])
                else:
                    raise ValueError(f"Unsupported JSON structure: {type(data)}")
            
            elif format == 'parquet':
                return pd.read_parquet(path)
            
            elif format == 'excel':
                # Read first sheet
                return pd.read_excel(path, sheet_name=0, engine='openpyxl')
            
            else:
                raise ValueError(f"Unsupported format: {format}")
        
        except Exception as e:
            raise ValueError(f"Failed to parse {format} file: {str(e)}")
    
    @staticmethod
    def get_sample_rows(file_path: str | Path, format: Optional[str] = None, n: int = 5) -> List[Dict[str, Any]]:
        """Get sample rows from file for schema detection"""
        df = FormatDetector.parse_file(file_path, format)
        return df.head(n).to_dict('records')

