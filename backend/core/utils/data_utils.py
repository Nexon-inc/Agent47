import json
import csv
import hashlib
import base64
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Union
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class DataUtils:
    def __init__(self):
        self._initialized = False
        
    async def initialize(self):
        """Initialize data utilities"""
        try:
            self._initialized = True
            logger.info("Data utilities initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize data utilities: {e}")
            raise
    
    def sanitize_text(self, text: str, max_length: int = 1000) -> str:
        """Sanitize and clean text input"""
        try:
            if not text:
                return ""
            
            # Remove null bytes and control characters
            cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
            
            # Normalize whitespace
            cleaned = re.sub(r'\s+', ' ', cleaned)
            
            # Remove HTML tags
            cleaned = re.sub(r'<[^>]+>', '', cleaned)
            
            # Remove special characters that might cause issues
            cleaned = re.sub(r'[^\w\s\-.,!?;:()]', '', cleaned)
            
            # Truncate if too long
            if len(cleaned) > max_length:
                cleaned = cleaned[:max_length].rsplit(' ', 1)[0] + "..."
            
            return cleaned.strip()
            
        except Exception as e:
            logger.error(f"Text sanitization failed: {e}")
            return text[:max_length] if text else ""
    
    def validate_email(self, email: str) -> bool:
        """Validate email address format"""
        try:
            if not email:
                return False
            
            # Basic email regex pattern
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return bool(re.match(pattern, email))
            
        except Exception as e:
            logger.error(f"Email validation failed: {e}")
            return False
    
    def validate_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            if not url:
                return False
            
            # Basic URL regex pattern
            pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$'
            return bool(re.match(pattern, url))
            
        except Exception as e:
            logger.error(f"URL validation failed: {e}")
            return False
    
    def generate_hash(self, data: str, algorithm: str = "sha256") -> str:
        """Generate hash of data using specified algorithm"""
        try:
            if algorithm == "md5":
                return hashlib.md5(data.encode()).hexdigest()
            elif algorithm == "sha1":
                return hashlib.sha1(data.encode()).hexdigest()
            elif algorithm == "sha256":
                return hashlib.sha256(data.encode()).hexdigest()
            elif algorithm == "sha512":
                return hashlib.sha512(data.encode()).hexdigest()
            else:
                raise ValueError(f"Unsupported hash algorithm: {algorithm}")
                
        except Exception as e:
            logger.error(f"Hash generation failed: {e}")
            return ""
    
    def encode_base64(self, data: str) -> str:
        """Encode data to base64"""
        try:
            return base64.b64encode(data.encode()).decode()
        except Exception as e:
            logger.error(f"Base64 encoding failed: {e}")
            return ""
    
    def decode_base64(self, encoded_data: str) -> str:
        """Decode base64 data"""
        try:
            return base64.b64decode(encoded_data.encode()).decode()
        except Exception as e:
            logger.error(f"Base64 decoding failed: {e}")
            return ""
    
    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        try:
            if size_bytes == 0:
                return "0 B"
            
            size_names = ["B", "KB", "MB", "GB", "TB"]
            i = 0
            while size_bytes >= 1024 and i < len(size_names) - 1:
                size_bytes /= 1024.0
                i += 1
            
            return f"{size_bytes:.1f} {size_names[i]}"
            
        except Exception as e:
            logger.error(f"File size formatting failed: {e}")
            return "0 B"
    
    def format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        try:
            if seconds < 60:
                return f"{seconds:.1f}s"
            elif seconds < 3600:
                minutes = seconds / 60
                return f"{minutes:.1f}m"
            elif seconds < 86400:
                hours = seconds / 3600
                return f"{hours:.1f}h"
            else:
                days = seconds / 86400
                return f"{days:.1f}d"
                
        except Exception as e:
            logger.error(f"Duration formatting failed: {e}")
            return "0s"
    
    def parse_date_string(self, date_string: str, formats: List[str] = None) -> Optional[datetime]:
        """Parse date string using multiple formats"""
        try:
            if not formats:
                formats = [
                    "%Y-%m-%d",
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%dT%H:%M:%SZ",
                    "%d/%m/%Y",
                    "%m/%d/%Y",
                    "%Y-%m-%d %H:%M:%S.%f"
                ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_string, fmt)
                except ValueError:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Date parsing failed: {e}")
            return None
    
    def format_date(self, date_obj: datetime, format_string: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format datetime object to string"""
        try:
            return date_obj.strftime(format_string)
        except Exception as e:
            logger.error(f"Date formatting failed: {e}")
            return str(date_obj)
    
    def get_relative_time(self, date_obj: datetime) -> str:
        """Get relative time description (e.g., '2 hours ago')"""
        try:
            now = datetime.utcnow()
            diff = now - date_obj
            
            if diff.days > 0:
                if diff.days == 1:
                    return "1 day ago"
                elif diff.days < 7:
                    return f"{diff.days} days ago"
                elif diff.days < 30:
                    weeks = diff.days // 7
                    return f"{weeks} week{'s' if weeks > 1 else ''} ago"
                elif diff.days < 365:
                    months = diff.days // 30
                    return f"{months} month{'s' if months > 1 else ''} ago"
                else:
                    years = diff.days // 365
                    return f"{years} year{'s' if years > 1 else ''} ago"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours} hour{'s' if hours > 1 else ''} ago"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            else:
                return "just now"
                
        except Exception as e:
            logger.error(f"Relative time calculation failed: {e}")
            return "unknown time"
    
    def convert_to_json(self, data: Any, ensure_ascii: bool = False, indent: int = 2) -> str:
        """Convert data to JSON string with error handling"""
        try:
            return json.dumps(data, ensure_ascii=ensure_ascii, indent=indent, default=str)
        except Exception as e:
            logger.error(f"JSON conversion failed: {e}")
            return "{}"
    
    def parse_json(self, json_string: str) -> Optional[Any]:
        """Parse JSON string with error handling"""
        try:
            return json.loads(json_string)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            return None
        except Exception as e:
            logger.error(f"JSON parsing error: {e}")
            return None
    
    def csv_to_dict(self, csv_content: str, delimiter: str = ",") -> List[Dict[str, str]]:
        """Convert CSV content to list of dictionaries"""
        try:
            if not csv_content.strip():
                return []
            
            lines = csv_content.strip().split('\n')
            if len(lines) < 2:
                return []
            
            reader = csv.DictReader(lines, delimiter=delimiter)
            return list(reader)
            
        except Exception as e:
            logger.error(f"CSV to dict conversion failed: {e}")
            return []
    
    def dict_to_csv(self, data: List[Dict[str, Any]], fieldnames: List[str] = None) -> str:
        """Convert list of dictionaries to CSV string"""
        try:
            if not data:
                return ""
            
            if not fieldnames:
                fieldnames = list(data[0].keys())
            
            output = []
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
            
            return ''.join(output)
            
        except Exception as e:
            logger.error(f"Dict to CSV conversion failed: {e}")
            return ""
    
    def merge_dicts(self, *dicts: Dict[str, Any], overwrite: bool = True) -> Dict[str, Any]:
        """Merge multiple dictionaries"""
        try:
            result = {}
            
            for d in dicts:
                if not isinstance(d, dict):
                    continue
                
                for key, value in d.items():
                    if key not in result or overwrite:
                        result[key] = value
                    elif isinstance(result[key], dict) and isinstance(value, dict):
                        result[key] = self.merge_dicts(result[key], value, overwrite=overwrite)
                    elif isinstance(result[key], list) and isinstance(value, list):
                        result[key].extend(value)
            
            return result
            
        except Exception as e:
            logger.error(f"Dictionary merge failed: {e}")
            return {}
    
    def flatten_dict(self, data: Dict[str, Any], parent_key: str = "", separator: str = ".") -> Dict[str, Any]:
        """Flatten nested dictionary"""
        try:
            items = []
            
            for key, value in data.items():
                new_key = f"{parent_key}{separator}{key}" if parent_key else key
                
                if isinstance(value, dict):
                    items.extend(self.flatten_dict(value, new_key, separator).items())
                else:
                    items.append((new_key, value))
            
            return dict(items)
            
        except Exception as e:
            logger.error(f"Dictionary flattening failed: {e}")
            return data
    
    def chunk_list(self, data: List[Any], chunk_size: int) -> List[List[Any]]:
        """Split list into chunks of specified size"""
        try:
            if chunk_size <= 0:
                return [data]
            
            return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
            
        except Exception as e:
            logger.error(f"List chunking failed: {e}")
            return [data]
    
    def remove_duplicates(self, data: List[Any], key_func: callable = None) -> List[Any]:
        """Remove duplicates from list while preserving order"""
        try:
            if not data:
                return []
            
            seen = set()
            result = []
            
            for item in data:
                if key_func:
                    key = key_func(item)
                else:
                    key = item
                
                if key not in seen:
                    seen.add(key)
                    result.append(item)
            
            return result
            
        except Exception as e:
            logger.error(f"Duplicate removal failed: {e}")
            return data
    
    def safe_get(self, data: Dict[str, Any], path: str, default: Any = None) -> Any:
        """Safely get nested dictionary value using dot notation"""
        try:
            keys = path.split('.')
            current = data
            
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return default
            
            return current
            
        except Exception as e:
            logger.error(f"Safe get failed: {e}")
            return default
    
    def mask_sensitive_data(self, data: str, mask_char: str = "*") -> str:
        """Mask sensitive data like emails, phone numbers, and credit cards"""
        try:
            # Mask email addresses
            data = re.sub(r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', 
                         r'\1***@\2', data)
            
            # Mask phone numbers
            data = re.sub(r'(\d{3})[-.\s]?(\d{3})[-.\s]?(\d{4})', 
                         r'\1-***-\4', data)
            
            # Mask credit card numbers
            data = re.sub(r'(\d{4})[-.\s]?(\d{4})[-.\s]?(\d{4})[-.\s]?(\d{4})', 
                         r'\1-****-****-\4', data)
            
            return data
            
        except Exception as e:
            logger.error(f"Data masking failed: {e}")
            return data
    
    def generate_uuid(self) -> str:
        """Generate a unique identifier"""
        try:
            import uuid
            return str(uuid.uuid4())
        except Exception as e:
            logger.error(f"UUID generation failed: {e}")
            return str(hash(str(datetime.utcnow())))
    
    def health_check(self) -> bool:
        """Check data utilities health"""
        try:
            if not self._initialized:
                return False
            
            # Test basic functionality
            test_text = "Test text with <html>tags</html> and special chars: @#$%"
            sanitized = self.sanitize_text(test_text)
            
            if not sanitized or sanitized == test_text:
                return False
            
            # Test email validation
            if not self.validate_email("test@example.com"):
                return False
            
            # Test hash generation
            test_hash = self.generate_hash("test")
            if not test_hash:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Data utilities health check failed: {e}")
            return False

data_utils = DataUtils()

async def get_data_utils() -> DataUtils:
    return data_utils

async def init_data_utils():
    await data_utils.initialize()
