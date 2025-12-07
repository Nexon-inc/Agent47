import re
import uuid
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime, date
from email_validator import validate_email, EmailNotValidError
from pydantic import BaseModel, ValidationError, validator
import logging

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom validation error for the Agent47 system."""
    def __init__(self, message: str, field: str = None, value: Any = None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(self.message)

class ValidationUtils:
    """Comprehensive data validation for Agent47 system."""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email address format and domain."""
        try:
            validated = validate_email(email, check_deliverability=True)
            return True
        except EmailNotValidError:
            return False
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """Validate password strength with detailed feedback."""
        errors = []
        warnings = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        elif len(password) < 12:
            warnings.append("Consider using a password longer than 12 characters")
        
        if not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r"[0-9]", password):
            errors.append("Password must contain at least one digit")
        
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            errors.append("Password must contain at least one special character")
        
        # Check for common patterns
        if re.search(r"(.)\1{2,}", password):
            warnings.append("Avoid repeating characters more than twice")
        
        if re.search(r"(123|abc|qwe)", password.lower()):
            warnings.append("Avoid common keyboard patterns")
        
        strength_score = 0
        if len(password) >= 8:
            strength_score += 1
        if re.search(r"[A-Z]", password):
            strength_score += 1
        if re.search(r"[a-z]", password):
            strength_score += 1
        if re.search(r"[0-9]", password):
            strength_score += 1
        if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            strength_score += 1
        if len(password) >= 12:
            strength_score += 1
        
        strength_level = "weak" if strength_score <= 2 else "medium" if strength_score <= 4 else "strong"
        
        return {
            "is_valid": len(errors) == 0,
            "strength_score": strength_score,
            "strength_level": strength_level,
            "errors": errors,
            "warnings": warnings
        }
    
    @staticmethod
    def validate_username(username: str) -> Dict[str, Any]:
        """Validate username format and requirements."""
        errors = []
        
        if len(username) < 3:
            errors.append("Username must be at least 3 characters long")
        
        if len(username) > 30:
            errors.append("Username must be no more than 30 characters long")
        
        if not re.match(r"^[a-zA-Z0-9_-]+$", username):
            errors.append("Username can only contain letters, numbers, underscores, and hyphens")
        
        if username.startswith("-") or username.endswith("-"):
            errors.append("Username cannot start or end with a hyphen")
        
        if username.startswith("_") or username.endswith("_"):
            errors.append("Username cannot start or end with an underscore")
        
        # Check for reserved usernames
        reserved_names = ["admin", "root", "system", "guest", "test", "demo", "support", "help"]
        if username.lower() in reserved_names:
            errors.append("Username is reserved and cannot be used")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }
    
    @staticmethod
    def validate_phone_number(phone: str, country_code: str = "US") -> bool:
        """Validate phone number format based on country."""
        # Remove all non-digit characters
        digits_only = re.sub(r"\D", "", phone)
        
        if country_code == "US":
            # US phone numbers should be 10 digits (or 11 with country code)
            if len(digits_only) == 10:
                return True
            elif len(digits_only) == 11 and digits_only.startswith("1"):
                return True
            return False
        elif country_code == "UK":
            # UK phone numbers should be 10-11 digits
            return 10 <= len(digits_only) <= 11
        else:
            # Generic validation for other countries
            return 7 <= len(digits_only) <= 15
        
        return False
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format."""
        url_pattern = re.compile(
            r"^https?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
            r"localhost|"  # localhost...
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$", re.IGNORECASE)
        return bool(url_pattern.match(url))
    
    @staticmethod
    def validate_uuid(uuid_string: str) -> bool:
        """Validate UUID format."""
        try:
            uuid.UUID(uuid_string)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_json_schema(data: Any, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data against a JSON schema."""
        errors = []
        
        try:
            # Basic schema validation
            if "type" in schema:
                expected_type = schema["type"]
                if expected_type == "string" and not isinstance(data, str):
                    errors.append(f"Expected string, got {type(data).__name__}")
                elif expected_type == "number" and not isinstance(data, (int, float)):
                    errors.append(f"Expected number, got {type(data).__name__}")
                elif expected_type == "integer" and not isinstance(data, int):
                    errors.append(f"Expected integer, got {type(data).__name__}")
                elif expected_type == "boolean" and not isinstance(data, bool):
                    errors.append(f"Expected boolean, got {type(data).__name__}")
                elif expected_type == "array" and not isinstance(data, list):
                    errors.append(f"Expected array, got {type(data).__name__}")
                elif expected_type == "object" and not isinstance(data, dict):
                    errors.append(f"Expected object, got {type(data).__name__}")
            
            # String validations
            if isinstance(data, str) and "string" in schema:
                string_schema = schema["string"]
                if "minLength" in string_schema and len(data) < string_schema["minLength"]:
                    errors.append(f"String too short. Minimum length: {string_schema['minLength']}")
                if "maxLength" in string_schema and len(data) > string_schema["maxLength"]:
                    errors.append(f"String too long. Maximum length: {string_schema['maxLength']}")
                if "pattern" in string_schema and not re.match(string_schema["pattern"], data):
                    errors.append(f"String does not match pattern: {string_schema['pattern']}")
            
            # Number validations
            if isinstance(data, (int, float)) and "number" in schema:
                number_schema = schema["number"]
                if "minimum" in number_schema and data < number_schema["minimum"]:
                    errors.append(f"Number too small. Minimum: {number_schema['minimum']}")
                if "maximum" in number_schema and data > number_schema["maximum"]:
                    errors.append(f"Number too large. Maximum: {number_schema['maximum']}")
            
            # Array validations
            if isinstance(data, list) and "array" in schema:
                array_schema = schema["array"]
                if "minItems" in array_schema and len(data) < array_schema["minItems"]:
                    errors.append(f"Array too short. Minimum items: {array_schema['minItems']}")
                if "maxItems" in array_schema and len(data) > array_schema["maxItems"]:
                    errors.append(f"Array too long. Maximum items: {array_schema['maxItems']}")
                
                # Validate array items if schema provided
                if "items" in array_schema and data:
                    for i, item in enumerate(data):
                        item_errors = DataValidator.validate_json_schema(item, array_schema["items"])
                        if item_errors["errors"]:
                            errors.extend([f"Item {i}: {error}" for error in item_errors["errors"]])
            
            # Object validations
            if isinstance(data, dict) and "object" in schema:
                object_schema = schema["object"]
                if "required" in object_schema:
                    for required_field in object_schema["required"]:
                        if required_field not in data:
                            errors.append(f"Required field missing: {required_field}")
                
                if "properties" in object_schema:
                    for field_name, field_value in data.items():
                        if field_name in object_schema["properties"]:
                            field_errors = DataValidator.validate_json_schema(field_value, object_schema["properties"][field_name])
                            if field_errors["errors"]:
                                errors.extend([f"{field_name}: {error}" for error in field_errors["errors"]])
                        elif "additionalProperties" in object_schema and not object_schema["additionalProperties"]:
                            errors.append(f"Additional property not allowed: {field_name}")
            
            return {
                "is_valid": len(errors) == 0,
                "errors": errors
            }
            
        except Exception as e:
            return {
                "is_valid": False,
                "errors": [f"Validation error: {str(e)}"]
            }
    
    @staticmethod
    def validate_date_format(date_string: str, format_string: str = "%Y-%m-%d") -> bool:
        """Validate date string format."""
        try:
            datetime.strptime(date_string, format_string)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_time_format(time_string: str, format_string: str = "%H:%M:%S") -> bool:
        """Validate time string format."""
        try:
            datetime.strptime(time_string, format_string)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_datetime_format(datetime_string: str, format_string: str = "%Y-%m-%d %H:%M:%S") -> bool:
        """Validate datetime string format."""
        try:
            datetime.strptime(datetime_string, format_string)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_credit_card(card_number: str) -> bool:
        """Validate credit card number using Luhn algorithm."""
        # Remove spaces and dashes
        card_number = re.sub(r"\D", "", card_number)
        
        if not card_number.isdigit():
            return False
        
        if len(card_number) < 13 or len(card_number) > 19:
            return False
        
        # Luhn algorithm
        total = 0
        is_even = False
        
        for digit in reversed(card_number):
            digit = int(digit)
            if is_even:
                digit *= 2
                if digit > 9:
                    digit -= 9
            total += digit
            is_even = not is_even
        
        return total % 10 == 0
    
    @staticmethod
    def validate_postal_code(postal_code: str, country_code: str = "US") -> bool:
        """Validate postal code format based on country."""
        if country_code == "US":
            # US ZIP code: 5 digits or 5+4 format
            pattern = r"^\d{5}(-\d{4})?$"
        elif country_code == "UK":
            # UK postcode format
            pattern = r"^[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}$"
        elif country_code == "CA":
            # Canadian postal code: A1A 1A1 format
            pattern = r"^[A-Za-z]\d[A-Za-z] ?\d[A-Za-z]\d$"
        else:
            # Generic validation for other countries
            pattern = r"^[A-Za-z0-9\s\-]{3,10}$"
        
        return bool(re.match(pattern, postal_code))
    
    @staticmethod
    def validate_currency_code(currency_code: str) -> bool:
        """Validate ISO 4217 currency code."""
        if not isinstance(currency_code, str) or len(currency_code) != 3:
            return False
        
        # Check if it's all uppercase letters
        return currency_code.isalpha() and currency_code.isupper()
    
    @staticmethod
    def validate_language_code(language_code: str) -> bool:
        """Validate ISO 639-1 language code."""
        if not isinstance(language_code, str) or len(language_code) != 2:
            return False
        
        # Check if it's all lowercase letters
        return language_code.isalpha() and language_code.islower()
    
    @staticmethod
    def validate_timezone(timezone_string: str) -> bool:
        """Validate timezone string."""
        try:
            import pytz
            pytz.timezone(timezone_string)
            return True
        except (ImportError, pytz.exceptions.UnknownTimeZoneError):
            # Fallback validation for common timezone formats
            common_timezones = [
                "UTC", "GMT", "EST", "EDT", "CST", "CDT", "MST", "MDT", "PST", "PDT",
                "Europe/London", "Europe/Paris", "Asia/Tokyo", "America/New_York"
            ]
            return timezone_string in common_timezones
    
    @staticmethod
    def sanitize_input(input_string: str, max_length: int = 1000) -> str:
        """Sanitize user input to prevent injection attacks."""
        if not isinstance(input_string, str):
            return ""
        
        # Remove null bytes
        sanitized = input_string.replace("\x00", "")
        
        # Remove control characters except newlines and tabs
        sanitized = "".join(char for char in sanitized if ord(char) >= 32 or char in "\n\t")
        
        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        # Remove HTML tags
        sanitized = re.sub(r"<[^>]*>", "", sanitized)
        
        # Remove script tags and javascript: URLs
        sanitized = re.sub(r"javascript:", "", sanitized, flags=re.IGNORECASE)
        
        return sanitized.strip()
    
    @staticmethod
    def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
        """Validate file extension against allowed list."""
        if not filename:
            return False
        
        file_extension = filename.lower().split(".")[-1] if "." in filename else ""
        return file_extension in [ext.lower() for ext in allowed_extensions]
    
    @staticmethod
    def validate_file_size(file_size_bytes: int, max_size_mb: int) -> bool:
        """Validate file size against maximum allowed size."""
        max_size_bytes = max_size_mb * 1024 * 1024
        return file_size_bytes <= max_size_bytes

class Agent47Validator:
    """Specialized validator for Agent47 system requirements."""
    
    @staticmethod
    def validate_agent_name(name: str) -> Dict[str, Any]:
        """Validate agent name for the Agent47 system."""
        errors = []
        
        if not name:
            errors.append("Agent name cannot be empty")
        
        if len(name) > 100:
            errors.append("Agent name cannot exceed 100 characters")
        
        # Check for reserved agent names
        reserved_names = ["system", "admin", "root", "agent47", "aria", "clara", "eric", "joe", "jackie", "shakes", "purity"]
        if name.lower() in reserved_names:
            errors.append(f"Agent name '{name}' is reserved and cannot be used")
        
        # Check for special characters that might cause issues
        if re.search(r"[<>\"'&]", name):
            errors.append("Agent name contains invalid characters")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }
    
    @staticmethod
    def validate_task_parameters(parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate task parameters for agent execution."""
        errors = []
        
        if not isinstance(parameters, dict):
            errors.append("Task parameters must be a dictionary")
            return {"is_valid": False, "errors": errors}
        
        # Check for required fields
        required_fields = ["task_type", "description"]
        for field in required_fields:
            if field not in parameters:
                errors.append(f"Required field missing: {field}")
        
        # Validate task_type
        if "task_type" in parameters:
            task_type = parameters["task_type"]
            if not isinstance(task_type, str):
                errors.append("task_type must be a string")
            elif len(task_type) > 100:
                errors.append("task_type cannot exceed 100 characters")
        
        # Validate description
        if "description" in parameters:
            description = parameters["description"]
            if not isinstance(description, str):
                errors.append("description must be a string")
            elif len(description) > 1000:
                errors.append("description cannot exceed 1000 characters")
        
        # Validate additional parameters
        if "priority" in parameters:
            priority = parameters["priority"]
            if not isinstance(priority, int) or priority < 1 or priority > 10:
                errors.append("priority must be an integer between 1 and 10")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }
    
    @staticmethod
    def validate_user_tier(tier: str) -> bool:
        """Validate user tier for the Agent47 system."""
        valid_tiers = ["free", "starter", "pro"]
        return tier.lower() in valid_tiers
    
    @staticmethod
    def validate_api_key_format(api_key: str) -> bool:
        """Validate API key format."""
        if not api_key:
            return False
        
        # Check if it's a valid format (typically alphanumeric with possible hyphens/underscores)
        pattern = r"^[A-Za-z0-9_-]{32,128}$"
        return bool(re.match(pattern, api_key))
    
    @staticmethod
    def validate_webhook_url(url: str) -> bool:
        """Validate webhook URL for integrations."""
        if not DataValidator.validate_url(url):
            return False
        
        # Ensure it's HTTPS for security
        if not url.startswith("https://"):
            return False
        
        # Check for common webhook patterns
        webhook_patterns = [
            r"webhook",
            r"callback",
            r"hook",
            r"notify",
            r"ping"
        ]
        
        return any(re.search(pattern, url.lower()) for pattern in webhook_patterns)

# Convenience functions for common validations
def is_valid_email(email: str) -> bool:
    """Quick email validation."""
    return DataValidator.validate_email(email)

def is_valid_password(password: str) -> bool:
    """Quick password validation."""
    result = DataValidator.validate_password_strength(password)
    return result["is_valid"]

def is_valid_username(username: str) -> bool:
    """Quick username validation."""
    result = DataValidator.validate_username(username)
    return result["is_valid"]

def sanitize_string(input_string: str, max_length: int = 1000) -> str:
    """Quick string sanitization."""
    return DataValidator.sanitize_input(input_string, max_length)

def validate_agent47_data(data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
    """Validate Agent47-specific data based on type."""
    if data_type == "agent_name":
        return Agent47Validator.validate_agent_name(data.get("name", ""))
    elif data_type == "task_parameters":
        return Agent47Validator.validate_task_parameters(data)
    elif data_type == "user_tier":
        return {"is_valid": Agent47Validator.validate_user_tier(data.get("tier", "")), "errors": []}
    elif data_type == "api_key":
        return {"is_valid": Agent47Validator.validate_api_key_format(data.get("api_key", "")), "errors": []}
    elif data_type == "webhook_url":
        return {"is_valid": Agent47Validator.validate_webhook_url(data.get("url", "")), "errors": []}
    else:
        return {"is_valid": False, "errors": [f"Unknown data type: {data_type}"]}

# Global instance
_validation_utils = None

def get_validation_utils() -> ValidationUtils:
    """Get the global ValidationUtils instance."""
    global _validation_utils
    if _validation_utils is None:
        _validation_utils = ValidationUtils()
    return _validation_utils
