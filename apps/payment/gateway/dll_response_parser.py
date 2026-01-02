"""
DLL Response Parser for POS gateway.
"""
from typing import Dict, Any, Optional
import re
from apps.logs.services.log_service import LogService
from .dll_helpers import get_system_namespace, extract_properties_from_object, is_valid_response_value


class DLLResponseParser:
    """Parser for DLL response objects and strings."""
    
    @staticmethod
    def parse_response_string(response_text: str) -> Dict[str, Any]:
        """
        Parse response string from DLL.
        
        Args:
            response_text: Response string from DLL
            
        Returns:
            Dict[str, Any]: Parsed response data
        """
        result = {
            'success': False,
            'status': 'failed',
            'response_code': '',
            'response_message': ''
        }
        
        if not response_text:
            result['response_message'] = 'هیچ پاسخی از دستگاه دریافت نشد'
            return result
        
        # Check if transaction was successful
        # DLL usually returns response codes in format like "RS01" for success
        if 'RS01' in response_text or 'RS013' in response_text:
            result['success'] = True
            result['status'] = 'success'
            result['response_code'] = '00'
        elif 'RS00' in response_text:
            # Extract specific error code
            result['status'] = 'failed'
            error_match = re.search(r'RS00(\d+)', response_text)
            if error_match:
                error_code = error_match.group(1)
                result['response_code'] = error_code
            else:
                result['response_code'] = '01'  # Generic error
            result['response_message'] = DLLResponseParser._get_error_message(result['response_code'])
        else:
            # Unknown response format
            result['status'] = 'failed'
            result['response_code'] = '99'
            result['response_message'] = f'پاسخ نامشخص از دستگاه: {response_text[:100]}'
        
        return result
    
    @staticmethod
    def extract_from_response_object(response_obj, pos_instance=None) -> Dict[str, Any]:
        """
        Extract transaction details from Response object.
        
        Args:
            response_obj: Response object from DLL
            pos_instance: POS instance (optional, for fallback methods)
            
        Returns:
            Dict[str, Any]: Extracted transaction details
        """
        result = {}
        
        if not response_obj:
            return result
        
        # Extract properties using reflection
        system_namespace = get_system_namespace()
        response_data = extract_properties_from_object(response_obj, system_namespace)
        
        # Map common properties to result
        property_mappings = {
            'card_number': ['PANID', 'PanID', 'CardNumber', 'CardNo', 'PAN'],
            'bank_name': ['BankName', 'Bank'],
            'terminal_id': ['TerminalID', 'TerminalId', 'TermID'],
            'amount': ['Amount', 'TransactionAmount', 'TrxnAmount'],
            'reference_number': ['RRN', 'TrxnRRN', 'ReferenceNumber', 'RefNumber'],
            'transaction_serial': ['Serial', 'TrxnSerial', 'TransactionSerial'],
            'transaction_date': ['DateTime', 'TrxnDateTime', 'TransactionDate'],
            'response_code': ['ResponseCode', 'RespCode', 'Code', 'Status']
        }
        
        for result_key, property_keys in property_mappings.items():
            for prop_key in property_keys:
                if prop_key in response_data:
                    value = response_data[prop_key]
                    if is_valid_response_value(value):
                        result[result_key] = value
                        break
        
        # Try methods if properties didn't work
        method_mappings = {
            'card_number': ['GetPANID', 'GetCardNumber', 'GetPAN'],
            'bank_name': ['GetBankName'],
            'terminal_id': ['GetTerminalID'],
            'amount': ['GetAmount'],
            'reference_number': ['GetTrxnRRN'],
            'transaction_serial': ['GetTrxnSerial'],
            'transaction_date': ['GetTrxnDateTime']
        }
        
        for result_key, method_names in method_mappings.items():
            if result_key not in result:
                for method_name in method_names:
                    if hasattr(response_obj, method_name):
                        try:
                            method = getattr(response_obj, method_name)
                            value = method()
                            if is_valid_response_value(value):
                                if result_key == 'amount':
                                    result[result_key] = int(value)
                                else:
                                    result[result_key] = str(value).strip()
                                break
                        except (AttributeError, RuntimeError) as e:
                            LogService.log_warning(
                                'payment',
                                'dll_method_extraction_error',
                                details={'error': str(e), 'error_type': type(e).__name__, 'method': method_name}
                            )
        
        # Store all response data for debugging
        if response_data:
            result['response_data'] = response_data
        
        # Try to get from pos_instance if available
        if pos_instance:
            DLLResponseParser._extract_from_pos_instance(pos_instance, result)
        
        return result
    
    @staticmethod
    def _extract_from_pos_instance(pos_instance, result: Dict[str, Any]):
        """
        Extract transaction details from pos_instance methods.
        
        Args:
            pos_instance: POS instance
            result: Result dictionary to update
        """
        method_mappings = {
            'reference_number': ('GetTrxnRRN', str),
            'transaction_id': ('GetTrxnSerial', str),
            'transaction_datetime': ('GetTrxnDateTime', str),
            'bank_name': ('GetBankName', str)
        }
        
        for result_key, (method_name, converter) in method_mappings.items():
            if result_key not in result and hasattr(pos_instance, method_name):
                try:
                    method = getattr(pos_instance, method_name)
                    value = method()
                    if is_valid_response_value(value):
                        result[result_key] = converter(value)
                except (AttributeError, RuntimeError) as e:
                    LogService.log_warning(
                        'payment',
                        'dll_instance_method_error',
                        details={'error': str(e), 'error_type': type(e).__name__, 'method': method_name}
                    )
    
    @staticmethod
    def _get_error_message(error_code: str) -> str:
        """Get human-readable error message from error code."""
        error_messages = {
            '00': 'تراکنش موفق',
            '01': 'تراکنش ناموفق - کارت نامعتبر',
            '02': 'تراکنش ناموفق - موجودی کافی نیست',
            '03': 'تراکنش ناموفق - رمز اشتباه',
            '04': 'تراکنش ناموفق - کارت منقضی شده',
            '05': 'تراکنش ناموفق - خطا در ارتباط',
            '06': 'تراکنش ناموفق - خطای سیستم',
            '81': 'تراکنش توسط کاربر لغو شد',
            '99': 'تراکنش ناموفق - خطای نامشخص',
        }
        return error_messages.get(error_code, f'خطای نامشخص: {error_code}')

