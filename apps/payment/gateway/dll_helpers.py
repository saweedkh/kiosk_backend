"""
Helper functions and utilities for DLL-based POS gateway.
"""
from typing import Optional, Dict, Any
from apps.logs.services.log_service import LogService


def check_pythonnet_available() -> bool:
    """
    Check if pythonnet is available (lazy loading).
    
    Returns:
        bool: True if pythonnet is available, False otherwise
    """
    global PYTHONNET_AVAILABLE, _clr_module
    
    if PYTHONNET_AVAILABLE is not None:
        return PYTHONNET_AVAILABLE
    
    try:
        import clr
        _clr_module = clr
        # Try to load clr - this might fail if Mono/.NET runtime is not available
        try:
            clr.__version__  # Just check if it's loaded
            PYTHONNET_AVAILABLE = True
        except (RuntimeError, AttributeError):
            # clr is imported but runtime is not available
            PYTHONNET_AVAILABLE = False
    except (ImportError, RuntimeError):
        PYTHONNET_AVAILABLE = False
    
    return PYTHONNET_AVAILABLE


# Global variables for lazy loading
PYTHONNET_AVAILABLE = None
_clr_module = None


def get_system_namespace():
    """
    Get System namespace from .NET (if available).
    
    Returns:
        System namespace module or None
    """
    try:
        import System
        return System
    except (ImportError, RuntimeError) as e:
        LogService.log_warning(
            'payment',
            'dll_system_namespace_unavailable',
            details={'error': str(e), 'error_type': type(e).__name__}
        )
        return None


def get_clr_module():
    """
    Get clr module (if available).
    
    Returns:
        clr module or None
    """
    global _clr_module
    
    if not check_pythonnet_available():
        return None
    
    if _clr_module is None:
        try:
            import clr
            _clr_module = clr
        except (ImportError, RuntimeError):
            return None
    
    return _clr_module


def is_valid_response_value(value: Any) -> bool:
    """
    Check if a response value is valid (not empty, not None, not placeholder).
    
    Args:
        value: Value to check
        
    Returns:
        bool: True if value is valid, False otherwise
    """
    if value is None:
        return False
    
    value_str = str(value).strip()
    
    # Check for invalid placeholder values
    invalid_values = ['=', 'None', '', 'RN =', 'SR =', 'Intek.PcPosLibrary.Response']
    
    if value_str in invalid_values:
        return False
    
    # Must have minimum length
    if len(value_str) <= 2:
        return False
    
    return True


def extract_properties_from_object(obj, system_namespace=None) -> Dict[str, Any]:
    """
    Extract all properties from a .NET object using reflection.
    
    Args:
        obj: .NET object to extract properties from
        system_namespace: System namespace (optional, will be imported if not provided)
        
    Returns:
        Dict[str, Any]: Dictionary of property names and values
    """
    properties = {}
    
    if system_namespace is None:
        system_namespace = get_system_namespace()
    
    if system_namespace is None:
        return properties
    
    try:
        response_type = obj.GetType()
        prop_list = response_type.GetProperties()
        
        for prop in prop_list:
            try:
                prop_name = prop.Name
                prop_value = prop.GetValue(obj, None)
                
                if prop_value is not None:
                    prop_str = str(prop_value).strip()
                    # Skip if it's just the class name or empty
                    if prop_str and prop_str != 'Intek.PcPosLibrary.Response' and prop_str != 'None':
                        properties[prop_name] = prop_str
            except (AttributeError, RuntimeError) as e:
                LogService.log_warning(
                    'payment',
                    'dll_property_extraction_error',
                    details={'error': str(e), 'error_type': type(e).__name__, 'property': prop_name}
                )
    except (AttributeError, RuntimeError) as e:
        LogService.log_warning(
            'payment',
            'dll_reflection_error',
            details={'error': str(e), 'error_type': type(e).__name__}
        )
    
    return properties

