"""
DLL Response Waiter - Handles waiting for and polling DLL responses.
"""
import time
from typing import Any, Optional, Tuple
from apps.logs.services.log_service import LogService
from .exceptions import GatewayException


class DLLResponseWaiter:
    """Handles waiting for DLL transaction responses."""
    
    def __init__(self, pos_instance, max_wait_time: int = 120):
        """
        Initialize response waiter.
        
        Args:
            pos_instance: POS instance from DLL
            max_wait_time: Maximum time to wait in seconds (default: 120)
        """
        self.pos_instance = pos_instance
        self.max_wait_time = max_wait_time
        self.start_time = None
        self.last_rrn_check = None
    
    def wait_for_response(
        self, 
        response_received: bool = False,
        response_obj: Optional[Any] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[Any]]:
        """
        Wait for transaction response from DLL.
        
        Args:
            response_received: Whether event handler received response
            response_obj: Response object from event handler
            
        Returns:
            Tuple of (response_string, raw_response, response_object)
        """
        self.start_time = time.time()
        response = None
        raw_response = None
        
        LogService.log_info('payment', 'dll_waiting_for_response', details={
            'max_wait_time': self.max_wait_time,
            'message': 'TCP/IP connection is active. Waiting for user interaction (card swipe, PIN entry, or cancel)'
        })
        
        for attempt in range(self.max_wait_time):
            if attempt > 0:
                time.sleep(1)
            
            elapsed = int(time.time() - self.start_time)
            if elapsed > 0 and elapsed % 10 == 0:
                LogService.log_info('payment', 'dll_waiting_progress', details={
                    'elapsed': elapsed,
                    'max_attempts': self.max_wait_time
                })
            
            # Check if event handler received response
            if response_received and response_obj:
                LogService.log_info('payment', 'dll_response_received_from_event')
                return self._extract_response_strings(response_obj), raw_response, response_obj
            
            # Check Response object
            transaction_complete, response_obj = self._check_response_object(response_obj)
            if transaction_complete:
                response, raw_response = self._extract_response_strings(response_obj)
                return response, raw_response, response_obj
            
            # Check GetParsedResp
            response = self._check_getparsedresp()
            if response:
                return response, raw_response, response_obj
            
            # Check Response Code
            transaction_complete, response_obj = self._check_response_code(response_obj)
            if transaction_complete:
                response, raw_response = self._extract_response_strings(response_obj)
                return response, raw_response, response_obj
            
            # Check RRN
            transaction_complete, response_obj = self._check_rrn(response_obj)
            if transaction_complete:
                response, raw_response = self._extract_response_strings(response_obj)
                return response, raw_response, response_obj
            
            # Check connection status
            self._check_connection_status()
            
            # Check RawResponse
            raw_response = self._check_rawresponse()
            if raw_response:
                return raw_response, raw_response, response_obj
            
            # Check GetResponse
            response = self._check_getresponse()
            if response:
                return response, raw_response, response_obj
            
            # Check error message
            error_msg = self._check_error_message()
            if error_msg:
                raise GatewayException(f'خطا از دستگاه POS: {error_msg}')
        
        # Timeout - check for final error
        self._raise_timeout_error()
        return None, None, None
    
    def _check_response_object(self, response_obj: Optional[Any]) -> Tuple[bool, Optional[Any]]:
        """Check Response object for transaction completion."""
        if not hasattr(self.pos_instance, 'Response') or self.pos_instance.Response is None:
            return False, response_obj
        
        response_obj = self.pos_instance.Response
        
        # Check Response Code
        transaction_complete = self._check_response_code_in_object(response_obj)
        if transaction_complete:
            return True, response_obj
        
        # Check RRN
        transaction_complete = self._check_rrn_in_object(response_obj)
        if transaction_complete:
            return True, response_obj
        
        # Check Serial
        self._check_serial_in_object(response_obj)
        
        return False, response_obj
    
    def _check_response_code_in_object(self, response_obj: Any) -> bool:
        """Check if response object has valid response code."""
        try:
            if hasattr(response_obj, 'GetTrxnResp'):
                resp_code = response_obj.GetTrxnResp()
                resp_code_str = str(resp_code).strip() if resp_code else ''
                
                if resp_code_str and resp_code_str not in ['=', 'None', '']:
                    LogService.log_info('payment', 'dll_response_code_received', details={
                        'response_code': resp_code_str
                    })
                    
                    if resp_code_str == '81':
                        LogService.log_warning('payment', 'dll_transaction_cancelled', details={
                            'response_code': resp_code_str
                        })
                    elif resp_code_str in ['00', '01', '02', '03', '13']:
                        LogService.log_info('payment', 'dll_transaction_completed', details={
                            'response_code': resp_code_str
                        })
                    else:
                        LogService.log_info('payment', 'dll_transaction_completed_other_code', details={
                            'response_code': resp_code_str
                        })
                    
                    return True
        except (AttributeError, RuntimeError) as e:
            LogService.log_warning(
                'payment',
                'dll_response_code_check_error',
                details={'error': str(e), 'error_type': type(e).__name__}
            )
        
        return False
    
    def _check_rrn_in_object(self, response_obj: Any) -> bool:
        """Check if response object has valid RRN."""
        try:
            if hasattr(response_obj, 'GetTrxnRRN'):
                rrn = response_obj.GetTrxnRRN()
                rrn_str = str(rrn).strip() if rrn else ''
                
                if (rrn_str and rrn_str not in ['=', 'None', 'RN =', ''] and 
                    len(rrn_str) > 2 and any(c.isdigit() for c in rrn_str)):
                    LogService.log_info('payment', 'dll_rrn_received', details={'rrn': rrn_str})
                    return True
        except (AttributeError, RuntimeError) as e:
            LogService.log_warning(
                'payment',
                'dll_rrn_check_error',
                details={'error': str(e), 'error_type': type(e).__name__}
            )
        
        return False
    
    def _check_serial_in_object(self, response_obj: Any):
        """Check if response object has valid serial number."""
        try:
            if hasattr(response_obj, 'GetTrxnSerial'):
                serial = response_obj.GetTrxnSerial()
                serial_str = str(serial).strip() if serial else ''
                
                if (serial_str and serial_str not in ['=', 'None', 'SR =', ''] and 
                    len(serial_str) > 2 and any(c.isdigit() for c in serial_str)):
                    LogService.log_info('payment', 'dll_serial_received', details={'serial': serial_str})
        except (AttributeError, RuntimeError) as e:
            LogService.log_warning(
                'payment',
                'dll_serial_check_error',
                details={'error': str(e), 'error_type': type(e).__name__}
            )
    
    def _check_getparsedresp(self) -> Optional[str]:
        """Check GetParsedResp method."""
        try:
            if hasattr(self.pos_instance, 'GetParsedResp'):
                resp = self.pos_instance.GetParsedResp()
                if resp:
                    resp_str = str(resp).strip()
                    if (resp_str and resp_str != 'Intek.PcPosLibrary.Response' and 
                        len(resp_str) > 5):
                        LogService.log_info('payment', 'dll_getparsedresp_received', details={
                            'response_preview': resp_str[:100] if len(resp_str) > 100 else resp_str
                        })
                        return resp_str
        except (AttributeError, RuntimeError) as e:
            LogService.log_warning(
                'payment',
                'dll_getparsedresp_error',
                details={'error': str(e), 'error_type': type(e).__name__}
            )
        
        return None
    
    def _check_response_code(self, response_obj: Optional[Any]) -> Tuple[bool, Optional[Any]]:
        """Check Response Code from pos_instance."""
        try:
            if hasattr(self.pos_instance, 'GetTrxnResp'):
                resp_code = self.pos_instance.GetTrxnResp()
                resp_code_str = str(resp_code).strip() if resp_code else ''
                
                if resp_code_str and resp_code_str not in ['=', 'None', '']:
                    LogService.log_info('payment', 'dll_response_code_from_instance', details={
                        'response_code': resp_code_str
                    })
                    
                    if resp_code_str == '81':
                        LogService.log_warning('payment', 'dll_transaction_cancelled_code_81')
                    elif resp_code_str in ['00', '01', '02', '03', '13']:
                        LogService.log_info('payment', 'dll_transaction_completed_code', details={
                            'response_code': resp_code_str
                        })
                    
                    if hasattr(self.pos_instance, 'Response'):
                        response_obj = self.pos_instance.Response
                    
                    return True, response_obj
        except (AttributeError, RuntimeError) as e:
            LogService.log_warning(
                'payment',
                'dll_response_code_check_error',
                details={'error': str(e), 'error_type': type(e).__name__}
            )
        
        return False, response_obj
    
    def _check_rrn(self, response_obj: Optional[Any]) -> Tuple[bool, Optional[Any]]:
        """Check RRN from pos_instance."""
        try:
            if hasattr(self.pos_instance, 'GetTrxnRRN'):
                rrn = self.pos_instance.GetTrxnRRN()
                rrn_str = str(rrn).strip() if rrn else ''
                
                if (rrn_str and rrn_str not in ['None', '', '=', 'RN ='] and 
                    len(rrn_str) > 2 and any(c.isdigit() for c in rrn_str)):
                    
                    if rrn_str != self.last_rrn_check:
                        LogService.log_info('payment', 'dll_transaction_completed_rrn', details={
                            'rrn': rrn_str
                        })
                        self.last_rrn_check = rrn_str
                        
                        if hasattr(self.pos_instance, 'Response'):
                            response_obj = self.pos_instance.Response
                        
                        # Try to get GetParsedResp
                        if hasattr(self.pos_instance, 'GetParsedResp'):
                            try:
                                parsed = self.pos_instance.GetParsedResp()
                                if parsed:
                                    parsed_str = str(parsed).strip()
                                    if parsed_str and parsed_str != 'Intek.PcPosLibrary.Response':
                                        LogService.log_info('payment', 'dll_getparsedresp_received_after_rrn')
                            except (AttributeError, RuntimeError) as e:
                                LogService.log_warning(
                                    'payment',
                                    'dll_getparsedresp_error_after_rrn',
                                    details={'error': str(e), 'error_type': type(e).__name__}
                                )
                        
                        return True, response_obj
        except (AttributeError, RuntimeError) as e:
            elapsed = int(time.time() - self.start_time) if self.start_time else 0
            if elapsed % 10 == 0:
                LogService.log_warning(
                    'payment',
                    'dll_rrn_check_periodic_error',
                    details={'error': str(e), 'error_type': type(e).__name__, 'elapsed': elapsed}
                )
        
        return False, response_obj
    
    def _check_connection_status(self):
        """Check if connection is still alive."""
        try:
            if hasattr(self.pos_instance, 'IsConnected'):
                is_connected = self.pos_instance.IsConnected
                if not is_connected:
                    raise GatewayException('اتصال به دستگاه POS قطع شد')
            elif hasattr(self.pos_instance, 'ConnectionStatus'):
                status = self.pos_instance.ConnectionStatus
                if status and 'disconnected' in str(status).lower():
                    raise GatewayException('اتصال به دستگاه POS قطع شد')
        except GatewayException:
            raise
        except (AttributeError, RuntimeError) as e:
            LogService.log_warning(
                'payment',
                'dll_connection_check_warning',
                details={'error': str(e), 'error_type': type(e).__name__}
            )
    
    def _check_rawresponse(self) -> Optional[str]:
        """Check RawResponse property."""
        try:
            if hasattr(self.pos_instance, 'RawResponse'):
                raw = self.pos_instance.RawResponse
                if raw:
                    raw_str = str(raw).strip()
                    if raw_str and len(raw_str) > 5:
                        LogService.log_info('payment', 'dll_rawresponse_received', details={
                            'raw_preview': raw_str[:100] if len(raw_str) > 100 else raw_str
                        })
                        return raw_str
        except (AttributeError, RuntimeError) as e:
            LogService.log_warning(
                'payment',
                'dll_rawresponse_check_error',
                details={'error': str(e), 'error_type': type(e).__name__}
            )
        
        return None
    
    def _check_getresponse(self) -> Optional[str]:
        """Check GetResponse method."""
        try:
            if hasattr(self.pos_instance, 'GetResponse'):
                resp = self.pos_instance.GetResponse()
                if resp:
                    resp_str = resp.strip() if isinstance(resp, str) else str(resp).strip()
                    if (resp_str and resp_str != 'Intek.PcPosLibrary.Response' and 
                        len(resp_str) > 5):
                        LogService.log_info('payment', 'dll_getresponse_received', details={
                            'response_preview': resp_str[:100] if len(resp_str) > 100 else resp_str
                        })
                        return resp_str
        except (AttributeError, RuntimeError) as e:
            LogService.log_warning(
                'payment',
                'dll_getresponse_check_error',
                details={'error': str(e), 'error_type': type(e).__name__}
            )
        
        return None
    
    def _check_error_message(self) -> Optional[str]:
        """Check for error message."""
        try:
            if hasattr(self.pos_instance, 'GetErrorMsg'):
                error_msg = self.pos_instance.GetErrorMsg()
                if error_msg and error_msg.strip():
                    LogService.log_warning('payment', 'dll_error_message', details={'error_msg': error_msg})
                    return error_msg
        except (AttributeError, RuntimeError) as e:
            LogService.log_warning(
                'payment',
                'dll_errormsg_check_error',
                details={'error': str(e), 'error_type': type(e).__name__}
            )
        
        return None
    
    def _extract_response_strings(self, response_obj: Optional[Any]) -> Tuple[Optional[str], Optional[str]]:
        """Extract response strings from response object."""
        response = None
        raw_response = None
        
        if not response_obj:
            return None, None
        
        # Try GetParsedResp
        if hasattr(response_obj, 'GetParsedResp'):
            try:
                parsed = response_obj.GetParsedResp()
                if parsed:
                    parsed_str = str(parsed).strip()
                    if parsed_str and parsed_str != 'Intek.PcPosLibrary.Response':
                        response = parsed_str
            except (AttributeError, RuntimeError):
                pass
        
        # Try RawResponse
        if not response and hasattr(response_obj, 'RawResponse'):
            try:
                raw = response_obj.RawResponse
                if raw:
                    raw_str = str(raw).strip()
                    if raw_str:
                        response = raw_str
                        raw_response = raw_str
            except (AttributeError, RuntimeError):
                pass
        
        # Try ToString
        if not response:
            try:
                to_string = response_obj.ToString()
                if to_string and to_string != 'Intek.PcPosLibrary.Response':
                    response = to_string
            except (AttributeError, RuntimeError):
                pass
        
        # Try from pos_instance
        if not response and hasattr(self.pos_instance, 'GetParsedResp'):
            try:
                parsed = self.pos_instance.GetParsedResp()
                if parsed:
                    parsed_str = str(parsed).strip()
                    if parsed_str and parsed_str != 'Intek.PcPosLibrary.Response':
                        response = parsed_str
            except (AttributeError, RuntimeError):
                pass
        
        return response, raw_response
    
    def _raise_timeout_error(self):
        """Raise timeout error with details."""
        error_msg = ''
        status_code = None
        
        try:
            if hasattr(self.pos_instance, 'GetErrorMsg'):
                error_msg = self.pos_instance.GetErrorMsg()
                if error_msg and error_msg.strip():
                    LogService.log_warning('payment', 'dll_error_message', details={'error_msg': error_msg})
        except (AttributeError, RuntimeError):
            pass
        
        try:
            if hasattr(self.pos_instance, 'GetTrxnResp'):
                status_code = self.pos_instance.GetTrxnResp()
                if status_code and str(status_code).strip():
                    LogService.log_warning('payment', 'dll_status_code', details={'status_code': str(status_code)})
        except (AttributeError, RuntimeError):
            pass
        
        elapsed_seconds = int(time.time() - self.start_time) if self.start_time else self.max_wait_time
        
        if error_msg:
            raise GatewayException(f'خطا از دستگاه POS: {error_msg}')
        elif status_code:
            raise GatewayException(f'خطا از دستگاه POS با کد: {status_code}')
        else:
            raise GatewayException(
                f'هیچ پاسخی از دستگاه POS دریافت نشد (بعد از {elapsed_seconds} ثانیه). '
                'لطفاً بررسی کنید که:\n'
                '  - دستگاه روشن است و مبلغ را نمایش می‌دهد\n'
                '  - کارت را کشیده‌اید\n'
                '  - رمز را وارد کرده‌اید\n'
                '  - یا در دستگاه لغو کرده‌اید'
            )

