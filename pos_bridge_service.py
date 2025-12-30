"""
POS Bridge Service - Windows Service for POS Communication

This service runs on Windows machine and uses DLL to communicate with POS device.
Other systems can send HTTP requests to this service to process payments.

Usage:
    python pos_bridge_service.py

Configuration:
    Set HOST and PORT in the script or use environment variables:
    - POS_BRIDGE_HOST (default: 0.0.0.0)
    - POS_BRIDGE_PORT (default: 8080)
    - POS_DLL_PATH (path to pna.pcpos.dll)
    - POS_TCP_HOST (POS device IP)
    - POS_TCP_PORT (POS device port, default: 1362)
    - POS_TERMINAL_ID
    - POS_MERCHANT_ID
    - POS_DEVICE_SERIAL
"""

import os
import sys
import time
import json
import socket
from typing import Dict, Any
from flask import Flask, request, jsonify
from flask_cors import CORS

# Try to import pythonnet for DLL access
try:
    import clr
    PYTHONNET_AVAILABLE = True
except ImportError:
    PYTHONNET_AVAILABLE = False
    print("⚠️  pythonnet not available. Install with: pip install pythonnet")
    print("   This service requires Windows and pythonnet to use DLL.")

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

# Configuration
HOST = os.getenv('POS_BRIDGE_HOST', '0.0.0.0')
# Default port changed to 8081 to avoid conflicts with common services
PORT = int(os.getenv('POS_BRIDGE_PORT', 8081))
DLL_PATH = os.getenv('POS_DLL_PATH', 'pna.pcpos.dll')
POS_TCP_HOST = os.getenv('POS_TCP_HOST', '192.168.1.100')
POS_TCP_PORT = int(os.getenv('POS_TCP_PORT', 1362))
TERMINAL_ID = os.getenv('POS_TERMINAL_ID', '')
MERCHANT_ID = os.getenv('POS_MERCHANT_ID', '')
DEVICE_SERIAL = os.getenv('POS_DEVICE_SERIAL', '')

# Global POS instance
pos_instance = None


def check_port_available(port, host='0.0.0.0'):
    """Check if port is available."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            return True
    except OSError:
        return False


def init_pos_dll():
    """Initialize POS DLL connection."""
    global pos_instance
    
    if not PYTHONNET_AVAILABLE:
        raise Exception("pythonnet is not available. This service requires Windows and pythonnet.")
    
    try:
        # Get absolute path to DLL
        if not os.path.isabs(DLL_PATH):
            # Try to find DLL in current directory or parent directories
            current_dir = os.path.dirname(os.path.abspath(__file__))
            dll_full_path = os.path.join(current_dir, DLL_PATH)
            if not os.path.exists(dll_full_path):
                # Try parent directory
                dll_full_path = os.path.join(os.path.dirname(current_dir), DLL_PATH)
        else:
            dll_full_path = DLL_PATH
        
        if not os.path.exists(dll_full_path):
            raise Exception(f"DLL not found at: {dll_full_path}")
        
        print(f"📦 Loading DLL from: {dll_full_path}")
        
        # Add reference to DLL
        clr.AddReference(dll_full_path)
        
        # Import PCPOS class
        from Intek.PcPosLibrary import PCPOS
        
        # Create instance
        pos_instance = PCPOS()
        
        # Configure connection
        pos_instance.Ip = str(POS_TCP_HOST)
        pos_instance.Port = int(POS_TCP_PORT)
        pos_instance.ConnectionType = PCPOS.cnType.LAN
        
        # Set timeout
        if hasattr(pos_instance, 'Timeout'):
            pos_instance.Timeout = 120000  # 120 seconds
        
        # Set terminal ID
        if TERMINAL_ID:
            pos_instance.TerminalID = str(TERMINAL_ID)
        
        # Set merchant ID
        if MERCHANT_ID:
            if hasattr(pos_instance, 'R0Merchant'):
                pos_instance.R0Merchant = str(MERCHANT_ID)
            elif hasattr(pos_instance, 'MerchantID'):
                pos_instance.MerchantID = str(MERCHANT_ID)
        
        # Set device serial
        if DEVICE_SERIAL:
            if hasattr(pos_instance, 'SerialNumber'):
                pos_instance.SerialNumber = str(DEVICE_SERIAL)
            elif hasattr(pos_instance, 'DeviceSerial'):
                pos_instance.DeviceSerial = str(DEVICE_SERIAL)
        
        print(f"✅ POS DLL initialized")
        print(f"   IP: {POS_TCP_HOST}:{POS_TCP_PORT}")
        print(f"   Terminal ID: {TERMINAL_ID}")
        print(f"   Merchant ID: {MERCHANT_ID}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize POS DLL: {e}")
        import traceback
        traceback.print_exc()
        return False


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'dll_available': PYTHONNET_AVAILABLE,
        'pos_initialized': pos_instance is not None,
        'service': 'POS Bridge Service'
    })


@app.route('/test-connection', methods=['POST'])
def test_connection():
    """Test connection to POS device."""
    if not pos_instance:
        return jsonify({
            'success': False,
            'error': 'POS DLL not initialized'
        }), 500
    
    try:
        if hasattr(pos_instance, 'TestConnection'):
            result = pos_instance.TestConnection()
            return jsonify({
                'success': bool(result),
                'message': 'Connection test completed',
                'connected': bool(result)
            })
        else:
            return jsonify({
                'success': False,
                'error': 'TestConnection method not available'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/payment', methods=['POST'])
def process_payment():
    """
    Process payment transaction.
    
    Request body:
    {
        "amount": 10000,  # Amount in Rial
        "order_number": "ORDER-001",  # Optional
        "customer_name": "John Doe",  # Optional
        "payment_id": "PAY123",  # Optional
        "bill_id": "BILL456"  # Optional
    }
    
    Returns:
    {
        "success": true/false,
        "transaction_id": "...",
        "status": "success/failed",
        "response_code": "00",
        "response_message": "...",
        "reference_number": "...",
        "card_number": "...",
        ...
    }
    """
    if not pos_instance:
        return jsonify({
            'success': False,
            'error': 'POS DLL not initialized'
        }), 500
    
    try:
        # Parse request
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        amount = data.get('amount')
        if not amount:
            return jsonify({
                'success': False,
                'error': 'Amount is required'
            }), 400
        
        order_number = data.get('order_number', '')
        customer_name = data.get('customer_name', '')
        payment_id = data.get('payment_id', '')
        bill_id = data.get('bill_id', '')
        
        print(f"\n📤 Processing payment request:")
        print(f"   Amount: {amount:,} Rial")
        print(f"   Order Number: {order_number}")
        print(f"   Payment ID: {payment_id}")
        print(f"   Bill ID: {bill_id}")
        
        # Set amount
        pos_instance.Amount = str(amount)
        
        # Set order number
        if order_number and hasattr(pos_instance, 'OrderNumber'):
            pos_instance.OrderNumber = str(order_number)
        
        # Set customer name
        if customer_name and hasattr(pos_instance, 'CustomerName'):
            pos_instance.CustomerName = customer_name
        
        # Set payment ID
        if payment_id:
            if hasattr(pos_instance, 'PaymentID'):
                pos_instance.PaymentID = str(payment_id)
            elif hasattr(pos_instance, 'PaymentId'):
                pos_instance.PaymentId = str(payment_id)
            elif hasattr(pos_instance, 'PD'):
                pos_instance.PD = str(payment_id)
        
        # Set bill ID
        if bill_id:
            if hasattr(pos_instance, 'BillID'):
                pos_instance.BillID = str(bill_id)
            elif hasattr(pos_instance, 'BillId'):
                pos_instance.BillId = str(bill_id)
            elif hasattr(pos_instance, 'BI'):
                pos_instance.BI = str(bill_id)
        
        # Test connection first
        if hasattr(pos_instance, 'TestConnection'):
            connection_ok = pos_instance.TestConnection()
            if not connection_ok:
                return jsonify({
                    'success': False,
                    'error': 'Failed to connect to POS device'
                }), 500
        
        # Send transaction
        print(f"📤 Sending transaction to POS device...")
        pos_instance.send_transaction()
        print(f"✅ Transaction sent. Waiting for response...")
        
        # Wait for response (up to 120 seconds)
        # IMPORTANT: Use EXACT same logic as pos_dll_net.py which works correctly
        max_attempts = 120
        start_time = time.time()
        response_obj = None
        response = None
        raw_response = None
        last_rrn_check = None  # Track last RRN value to detect changes
        
        # Debug: Print status
        print(f"📤 تراکنش ارسال شد. منتظر پاسخ از دستگاه POS...")
        print(f"   ⚠️  اتصال TCP/IP فعال است و منتظر پاسخ می‌ماند")
        print(f"   لطفاً کارت را بکشید و رمز را وارد کنید (یا در دستگاه لغو کنید)")
        
        for attempt in range(max_attempts):
            # Check for response every second
            if attempt > 0:
                time.sleep(1)
            
            elapsed = int(time.time() - start_time)
            if elapsed > 0 and elapsed % 10 == 0:
                print(f"⏳ منتظر پاسخ... ({elapsed}/{max_attempts} ثانیه)")
            
            # Try to get Response object and check if it has actual data
            transaction_complete = False  # Flag to break outer loop
            try:
                if hasattr(pos_instance, 'Response') and pos_instance.Response is not None:
                    response_obj = pos_instance.Response
                    
                    # Check if Response object has actual data (not just empty object)
                    # Try to get properties that indicate transaction completion
                    has_data = False
                    
                    # Check for Response Code FIRST - this tells us if transaction is complete
                    resp_code = None
                    try:
                        if hasattr(response_obj, 'GetTrxnResp'):
                            resp_code = response_obj.GetTrxnResp()
                            resp_code_str = str(resp_code).strip() if resp_code else ''
                            # Check if response code is valid (not empty, not just "=")
                            if resp_code_str and resp_code_str != '=' and resp_code_str != 'None' and resp_code_str != '':
                                has_data = True
                                print(f"✅ Response Code دریافت شد: {resp_code_str}")
                                
                                # IMPORTANT: ANY response code means transaction is complete
                                # Response code 81 might mean cancelled, but transaction is still complete
                                if resp_code_str == '81':
                                    print(f"⚠️  Response Code 81 دریافت شد - تراکنش کامل شد")
                                    # Transaction is complete, break the loop
                                    transaction_complete = True
                                elif resp_code_str in ['00', '01', '02', '03', '13']:
                                    # Valid response code - transaction completed
                                    print(f"✅ تراکنش کامل شد (کد: {resp_code_str})")
                                    # Transaction is complete, break the loop
                                    transaction_complete = True
                                else:
                                    # Any other response code also means transaction is complete
                                    print(f"✅ Response Code دریافت شد: {resp_code_str} - تراکنش کامل شد")
                                    transaction_complete = True
                    except Exception as e:
                        pass
                    
                    # If transaction is complete (response code received), break
                    if transaction_complete:
                        break
                    
                    # Check for RRN (Reference Number) - this indicates transaction completed successfully
                    # IMPORTANT: Only accept RRN if it has actual value (not empty, not "RN =")
                    try:
                        if hasattr(response_obj, 'GetTrxnRRN'):
                            rrn = response_obj.GetTrxnRRN()
                            rrn_str = str(rrn).strip() if rrn else ''
                            # Check if RRN is valid (not empty, not "RN =", not "=", has actual digits)
                            # IMPORTANT: Don't print if RRN is empty or invalid
                            if rrn_str and rrn_str != '=' and rrn_str != 'None' and rrn_str != 'RN =' and rrn_str != '' and len(rrn_str) > 2:
                                # Check if it contains actual digits (not just spaces or special chars)
                                if any(c.isdigit() for c in rrn_str):
                                    has_data = True
                                    print(f"✅ RRN دریافت شد: {rrn_str}")
                                    # We have valid RRN - transaction completed successfully
                                    transaction_complete = True
                    except:
                        pass
                    
                    # If transaction is complete (RRN received), break
                    if transaction_complete:
                        break
                    
                    # Check for Serial Number - only if it has actual value
                    # IMPORTANT: Don't print if Serial is empty or invalid
                    try:
                        if hasattr(response_obj, 'GetTrxnSerial'):
                            serial = response_obj.GetTrxnSerial()
                            serial_str = str(serial).strip() if serial else ''
                            # Check if serial is valid (not empty, not "SR =", not "=", has actual digits)
                            if serial_str and serial_str != '=' and serial_str != 'None' and serial_str != 'SR =' and serial_str != '' and len(serial_str) > 2:
                                # Check if it contains actual digits
                                if any(c.isdigit() for c in serial_str):
                                    has_data = True
                                    print(f"✅ Serial Number دریافت شد: {serial_str}")
                    except:
                        pass
                    
                    # If we have data, try to get string representation
                    if has_data:
                        try:
                            if hasattr(response_obj, 'ToString'):
                                response = response_obj.ToString()
                            elif hasattr(response_obj, 'Message'):
                                response = str(response_obj.Message)
                            if response and response != 'Intek.PcPosLibrary.Response':
                                break
                        except:
                            pass
            except Exception as e:
                pass
            
            # Try GetParsedResp from pos_instance - this is the main method
            try:
                if hasattr(pos_instance, 'GetParsedResp'):
                    resp = pos_instance.GetParsedResp()
                    if resp:
                        resp_str = str(resp).strip()
                        # Check if it's a valid response (not just class name or empty)
                        if resp_str and resp_str != 'Intek.PcPosLibrary.Response' and len(resp_str) > 5:
                            response = resp_str
                            print(f"✅ GetParsedResp: {resp_str[:100]}...")
                            break
            except Exception as e:
                pass
            
            # Try to check Response Code from pos_instance FIRST
            # IMPORTANT: Response code tells us if transaction is complete (success or cancelled)
            # ANY valid response code means transaction is complete - we should break
            transaction_complete_from_code = False
            try:
                if hasattr(pos_instance, 'GetTrxnResp'):
                    resp_code = pos_instance.GetTrxnResp()
                    resp_code_str = str(resp_code).strip() if resp_code else ''
                    # Check if response code is valid (not empty, not just "=")
                    if resp_code_str and resp_code_str != '=' and resp_code_str != 'None' and resp_code_str != '':
                        # We have a valid response code - transaction is complete
                        print(f"✅ Response Code از pos_instance: {resp_code_str}")
                        
                        # IMPORTANT: ANY response code means transaction is complete
                        # Response code 81 might mean cancelled, but transaction is still complete
                        if resp_code_str == '81':
                            print(f"⚠️  Response Code 81 دریافت شد - تراکنش کامل شد")
                        elif resp_code_str in ['00', '01', '02', '03', '13']:
                            print(f"✅ تراکنش کامل شد (کد: {resp_code_str})")
                        
                        # Get Response object
                        if hasattr(pos_instance, 'Response'):
                            response_obj = pos_instance.Response
                        
                        # Transaction is complete - break the loop
                        transaction_complete_from_code = True
            except Exception as e:
                pass
            
            # IMPORTANT: Break outer loop if transaction is complete
            if transaction_complete_from_code:
                break
            
            # Try to check if transaction is complete by checking for RRN from pos_instance
            # This is the most reliable way - check pos_instance methods directly
            # IMPORTANT: RRN only appears when transaction is actually completed successfully
            try:
                if hasattr(pos_instance, 'GetTrxnRRN'):
                    rrn = pos_instance.GetTrxnRRN()
                    rrn_str = str(rrn).strip() if rrn else ''
                    
                    # IMPORTANT: Only accept RRN if it has actual value (not empty, not "RN =", has digits)
                    if rrn_str and rrn_str != 'None' and rrn_str != '' and rrn_str != '=' and rrn_str != 'RN =':
                        # Check if it contains actual digits (not just spaces or special chars)
                        if any(c.isdigit() for c in rrn_str) and len(rrn_str) > 2:
                            # Check if this is a new RRN (different from last check)
                            if rrn_str != last_rrn_check:
                                # Transaction completed - we have valid RRN
                                print(f"✅ تراکنش کامل شد - RRN: {rrn_str}")
                                last_rrn_check = rrn_str
                                
                                # Get Response object now
                                if hasattr(pos_instance, 'Response'):
                                    response_obj = pos_instance.Response
                                
                                # Also try to get GetParsedResp
                                if hasattr(pos_instance, 'GetParsedResp'):
                                    try:
                                        parsed = pos_instance.GetParsedResp()
                                        if parsed:
                                            parsed_str = str(parsed).strip()
                                            if parsed_str and parsed_str != 'Intek.PcPosLibrary.Response':
                                                response = parsed_str
                                                print(f"✅ GetParsedResp دریافت شد")
                                    except Exception as e:
                                        print(f"⚠️  خطا در GetParsedResp: {e}")
                                
                                # We have valid RRN, transaction is complete
                                break
            except Exception as e:
                # Debug: Print error if any
                if attempt % 10 == 0:  # Print every 10 attempts
                    print(f"⚠️  خطا در بررسی RRN: {e}")
                pass
            
            # IMPORTANT: Check if connection is still alive
            # If DLL has a method to check connection status, use it
            try:
                if hasattr(pos_instance, 'IsConnected'):
                    is_connected = pos_instance.IsConnected
                    if not is_connected:
                        raise Exception('اتصال به دستگاه POS قطع شد')
                elif hasattr(pos_instance, 'ConnectionStatus'):
                    status = pos_instance.ConnectionStatus
                    if status and 'disconnected' in str(status).lower():
                        raise Exception('اتصال به دستگاه POS قطع شد')
            except Exception as e:
                if 'قطع شد' in str(e):
                    raise
                # Connection check not available or failed, continue
                pass
            
            # Try RawResponse property from pos_instance
            try:
                if hasattr(pos_instance, 'RawResponse'):
                    raw = pos_instance.RawResponse
                    if raw:
                        raw_str = str(raw).strip()
                        # Check if it's a valid response
                        if raw_str and len(raw_str) > 5:
                            raw_response = raw_str
                            if not response:
                                response = raw_str
                            print(f"✅ RawResponse: {raw_str[:100]}...")
                            break
            except Exception:
                pass
            
            # Try GetResponse method
            try:
                if hasattr(pos_instance, 'GetResponse'):
                    resp = pos_instance.GetResponse()
                    if resp:
                        if isinstance(resp, str):
                            resp_str = resp.strip()
                        else:
                            # If it's an object, try to get string representation
                            resp_str = str(resp).strip()
                        # Check if it's a valid response
                        if resp_str and resp_str != 'Intek.PcPosLibrary.Response' and len(resp_str) > 5:
                            response = resp_str
                            print(f"✅ GetResponse: {resp_str[:100]}...")
                            break
            except Exception:
                pass
            
            # Check if there's an error message
            try:
                if hasattr(pos_instance, 'GetErrorMsg'):
                    error_msg = pos_instance.GetErrorMsg()
                    if error_msg and error_msg.strip():
                        raise Exception(f'خطا از دستگاه POS: {error_msg}')
            except Exception as e:
                if 'خطا' in str(e):
                    raise
                pass
        
        # Final check: If we have response_obj but no response string, check if it has data
        if response_obj and not response:
            # Check if response_obj has actual data by checking methods
            try:
                # Check RRN first (most reliable indicator)
                if hasattr(response_obj, 'GetTrxnRRN'):
                    rrn = response_obj.GetTrxnRRN()
                    if rrn and str(rrn).strip() and str(rrn) != 'None' and str(rrn) != '':
                        # We have data, response_obj is valid
                        print(f"✅ Response object معتبر است - RRN: {rrn}")
                    else:
                        # Response object exists but empty - might not be ready yet
                        print(f"⚠️  Response object موجود است اما RRN خالی است. منتظر می‌مانیم...")
                        # Don't use empty response_obj - continue waiting
                        response_obj = None
            except Exception as e:
                print(f"⚠️  خطا در بررسی Response object: {e}")
                pass
        
        # If still no response, try to get error message
        if not response and not raw_response and not response_obj:
            error_msg = ''
            try:
                if hasattr(pos_instance, 'GetErrorMsg'):
                    error_msg = pos_instance.GetErrorMsg()
                    if error_msg and error_msg.strip():
                        print(f"⚠️  پیام خطا: {error_msg}")
            except Exception:
                pass
            
            # Try to get response code or status
            status_code = None
            try:
                if hasattr(pos_instance, 'GetTrxnResp'):
                    status_code = pos_instance.GetTrxnResp()
                    if status_code and str(status_code).strip():
                        print(f"⚠️  Response Code: {status_code}")
            except Exception:
                pass
            
            if error_msg:
                raise Exception(f'خطا از دستگاه POS: {error_msg}')
            elif status_code:
                raise Exception(f'خطا از دستگاه POS با کد: {status_code}')
            else:
                elapsed_seconds = int(time.time() - start_time)
                raise Exception(
                    f'هیچ پاسخی از دستگاه POS دریافت نشد (بعد از {elapsed_seconds} ثانیه). '
                    'لطفاً بررسی کنید که:\n'
                    '  - دستگاه روشن است و مبلغ را نمایش می‌دهد\n'
                    '  - کارت را کشیده‌اید\n'
                    '  - رمز را وارد کرده‌اید\n'
                    '  - یا در دستگاه لغو کرده‌اید'
                )
        
        # If we have response_obj, try to extract more information
        # IMPORTANT: Check if response_obj actually has data, not just empty object
        if response_obj:
            try:
                # First, check if Response object has actual data by checking key methods
                has_actual_data = False
                
                # Check for RRN (most reliable indicator of completed transaction)
                try:
                    if hasattr(response_obj, 'GetTrxnRRN'):
                        rrn = response_obj.GetTrxnRRN()
                        if rrn and str(rrn).strip() and str(rrn) != 'None':
                            has_actual_data = True
                            print(f"✅ Response object has RRN: {rrn}")
                except:
                    pass
                
                # Check for Response Code
                if not has_actual_data:
                    try:
                        if hasattr(response_obj, 'GetTrxnResp'):
                            resp_code = response_obj.GetTrxnResp()
                            if resp_code and str(resp_code).strip() and str(resp_code) != 'None':
                                has_actual_data = True
                                print(f"✅ Response object has Response Code: {resp_code}")
                    except:
                        pass
                
                # If we have actual data, extract it
                if has_actual_data:
                    # Try to get all properties from Response object using reflection
                    import System
                    response_type = response_obj.GetType()
                    
                    # Get all properties
                    properties = response_type.GetProperties()
                    for prop in properties:
                        try:
                            prop_name = prop.Name
                            prop_value = prop.GetValue(response_obj, None)
                            if prop_value is not None:
                                prop_str = str(prop_value).strip()
                                # Skip if it's just the class name or None
                                if prop_str and prop_str != 'Intek.PcPosLibrary.Response' and prop_str != 'None':
                                    if not response:
                                        response = f"{prop_name}={prop_str}"
                                    else:
                                        response += f", {prop_name}={prop_str}"
                        except Exception:
                            pass
                else:
                    # Response object exists but has no data yet - continue waiting
                    print(f"⚠️  Response object موجود است اما هنوز داده‌ای ندارد. منتظر می‌مانیم...")
                    response_obj = None  # Reset to continue waiting
                
                # Also try common methods
                if not response:
                    # Try GetParsedResp method
                    if hasattr(response_obj, 'GetParsedResp'):
                        try:
                            parsed = response_obj.GetParsedResp()
                            if parsed:
                                parsed_str = str(parsed).strip()
                                if parsed_str and parsed_str != 'Intek.PcPosLibrary.Response':
                                    response = parsed_str
                        except Exception:
                            pass
                    
                    # Try RawResponse property
                    if not response and hasattr(response_obj, 'RawResponse'):
                        try:
                            raw = response_obj.RawResponse
                            if raw:
                                raw_str = str(raw).strip()
                                if raw_str:
                                    response = raw_str
                        except Exception:
                            pass
                    
                    # Try ToString method
                    if not response:
                        try:
                            to_string = response_obj.ToString()
                            if to_string and to_string != 'Intek.PcPosLibrary.Response':
                                response = to_string
                        except Exception:
                            pass
                
                # If still no response, try to get from pos_instance directly
                if not response:
                    if hasattr(pos_instance, 'GetParsedResp'):
                        try:
                            parsed = pos_instance.GetParsedResp()
                            if parsed:
                                parsed_str = str(parsed).strip()
                                if parsed_str and parsed_str != 'Intek.PcPosLibrary.Response':
                                    response = parsed_str
                        except Exception:
                            pass
            except Exception as e:
                # Log error but continue - don't crash
                import traceback
                print(f"⚠️  خطا در خواندن Response object: {e}")
                traceback.print_exc()
        
        # Parse response using EXACT same logic as pos_dll_net.py
        result = _parse_dll_response(response, raw_response, response_obj, pos_instance, amount)
        
        print(f"✅ Payment processed:")
        print(f"   Success: {result['success']}")
        print(f"   Response Code: {result['response_code']}")
        print(f"   Reference Number: {result['reference_number']}")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error processing payment: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def _parse_dll_response(response: str, raw_response: str, response_obj=None, pos_instance=None, amount: int = 0) -> Dict[str, Any]:
    """
    Parse DLL response - EXACT same logic as pos_dll_net.py.
    
    Args:
        response: Parsed response from DLL
        raw_response: Raw response string
        response_obj: Response object from DLL
        pos_instance: POS instance to get data from
        amount: Payment amount
        
    Returns:
        Dict[str, Any]: Parsed response
    """
    result = {
        'success': False,
        'status': 'failed',
        'response_code': '',
        'response_message': '',
        'transaction_id': '',
        'card_number': '',
        'reference_number': '',
        'raw_response': raw_response or '',
        'parsed_response': response or '',
        'amount': amount
    }
    
    # If no response at all, return early
    if not response and not raw_response:
        result['response_message'] = 'هیچ پاسخی از دستگاه دریافت نشد'
        return result
    
    # Use raw_response if response is empty
    response_text = response or raw_response or ''
    
    # Try to extract transaction details from response
    # Adjust parsing based on actual DLL response format
    
    # Check if transaction was successful
    # DLL usually returns response codes in format like "RS01" for success
    # Common success codes: RS01, RS013, RS00 (with specific subcodes)
    if 'RS01' in response_text or 'RS013' in response_text:
        result['success'] = True
        result['status'] = 'success'
        result['response_code'] = '00'
    elif 'RS00' in response_text:
        # Extract specific error code
        result['status'] = 'failed'
        # Try to extract error code (RS00XX format)
        import re
        error_match = re.search(r'RS00(\d+)', response_text)
        if error_match:
            error_code = error_match.group(1)
            result['response_code'] = error_code
        else:
            result['response_code'] = '01'  # Generic error
        result['response_message'] = _get_error_message(result['response_code'])
    else:
        # Unknown response format
        result['status'] = 'failed'
        result['response_code'] = '99'
        result['response_message'] = f'پاسخ نامشخص از دستگاه: {response_text[:100]}'
    
    # Extract transaction details from Response object if available
    if response_obj:
        try:
            import System
            response_type = response_obj.GetType()
            
            # Try to get all properties using reflection
            properties = response_type.GetProperties()
            response_data = {}
            for prop in properties:
                try:
                    prop_name = prop.Name
                    prop_value = prop.GetValue(response_obj, None)
                    if prop_value is not None:
                        prop_str = str(prop_value).strip()
                        # Skip if it's just the class name or empty
                        if prop_str and prop_str != 'Intek.PcPosLibrary.Response' and prop_str != 'None':
                            response_data[prop_name] = prop_str
                except Exception:
                    pass
            
            # Map common properties to result
            # Try to get PAN ID (card number) - common property names
            for pan_key in ['PANID', 'PanID', 'CardNumber', 'CardNo', 'PAN']:
                if pan_key in response_data:
                    result['card_number'] = response_data[pan_key]
                    break
            
            # Try methods if properties didn't work
            if not result['card_number']:
                for method_name in ['GetPANID', 'GetCardNumber', 'GetPAN']:
                    if hasattr(response_obj, method_name):
                        try:
                            method = getattr(response_obj, method_name)
                            pan_id = method()
                            if pan_id:
                                result['card_number'] = str(pan_id).strip()
                                break
                        except Exception:
                            pass
            
            # Try to get bank name
            for bank_key in ['BankName', 'Bank']:
                if bank_key in response_data:
                    result['bank_name'] = response_data[bank_key]
                    break
            
            if 'bank_name' not in result:
                if hasattr(response_obj, 'GetBankName'):
                    try:
                        bank_name = response_obj.GetBankName()
                        if bank_name:
                            result['bank_name'] = str(bank_name).strip()
                    except Exception:
                        pass
            
            # Try to get terminal ID
            for term_key in ['TerminalID', 'TerminalId', 'TermID']:
                if term_key in response_data:
                    result['terminal_id'] = response_data[term_key]
                    break
            
            if 'terminal_id' not in result:
                if hasattr(response_obj, 'GetTerminalID'):
                    try:
                        term_id = response_obj.GetTerminalID()
                        if term_id:
                            result['terminal_id'] = str(term_id).strip()
                    except Exception:
                        pass
            
            # Try to get amount
            for amount_key in ['Amount', 'TransactionAmount', 'TrxnAmount']:
                if amount_key in response_data:
                    result['amount'] = response_data[amount_key]
                    break
            
            if 'amount' not in result:
                if hasattr(response_obj, 'GetAmount'):
                    try:
                        amount_val = response_obj.GetAmount()
                        if amount_val:
                            result['amount'] = int(amount_val)
                    except Exception:
                        pass
            
            # Try to get reference number (RRN)
            for rrn_key in ['RRN', 'TrxnRRN', 'ReferenceNumber', 'RefNumber']:
                if rrn_key in response_data:
                    result['reference_number'] = response_data[rrn_key]
                    break
            
            if not result['reference_number']:
                if hasattr(response_obj, 'GetTrxnRRN'):
                    try:
                        rrn = response_obj.GetTrxnRRN()
                        if rrn:
                            result['reference_number'] = str(rrn).strip()
                    except Exception:
                        pass
            
            # Try to get transaction serial
            for serial_key in ['Serial', 'TrxnSerial', 'TransactionSerial']:
                if serial_key in response_data:
                    result['transaction_serial'] = response_data[serial_key]
                    break
            
            if 'transaction_serial' not in result:
                if hasattr(response_obj, 'GetTrxnSerial'):
                    try:
                        serial = response_obj.GetTrxnSerial()
                        if serial:
                            result['transaction_serial'] = str(serial).strip()
                    except Exception:
                        pass
            
            # Try to get transaction date/time
            for date_key in ['DateTime', 'TrxnDateTime', 'TransactionDate']:
                if date_key in response_data:
                    result['transaction_date'] = response_data[date_key]
                    break
            
            if 'transaction_date' not in result:
                if hasattr(response_obj, 'GetTrxnDateTime'):
                    try:
                        date_time = response_obj.GetTrxnDateTime()
                        if date_time:
                            result['transaction_date'] = str(date_time).strip()
                    except Exception:
                        pass
            
            # Try to get response code
            for resp_code_key in ['ResponseCode', 'RespCode', 'Code', 'Status']:
                if resp_code_key in response_data:
                    code = response_data[resp_code_key]
                    if code and not result['response_code']:
                        result['response_code'] = str(code).strip()
                        # Update success status based on response code
                        if code == '00' or code == 'RS01' or code == 'RS013':
                            result['success'] = True
                            result['status'] = 'success'
                        break
            
            # Store all response data for debugging
            if response_data:
                result['response_data'] = response_data
            
            # Try RawResponse property
            if hasattr(response_obj, 'RawResponse'):
                raw = response_obj.RawResponse
                if raw and not raw_response:
                    raw_response = raw
        except Exception:
            pass
    
    # Extract transaction details from pos_instance methods
    # Adjust based on actual DLL response format
    if pos_instance:
        try:
            # Try to get reference number
            if hasattr(pos_instance, 'GetTrxnRRN'):
                rrn = pos_instance.GetTrxnRRN()
                if rrn and not result.get('reference_number'):
                    rrn_str = str(rrn).strip()
                    # Clean up RRN
                    if rrn_str and rrn_str != '=' and rrn_str != 'None' and rrn_str != 'RN =':
                        if rrn_str.startswith('RN ='):
                            rrn_str = rrn_str[4:].strip()
                        if rrn_str and len(rrn_str) > 2 and any(c.isdigit() for c in rrn_str):
                            result['reference_number'] = rrn_str
            
            # Try to get transaction serial
            if hasattr(pos_instance, 'GetTrxnSerial'):
                serial = pos_instance.GetTrxnSerial()
                if serial and not result.get('transaction_id'):
                    serial_str = str(serial).strip()
                    # Clean up serial
                    if serial_str and serial_str != '=' and serial_str != 'None' and serial_str != 'SR =':
                        if serial_str.startswith('SR ='):
                            serial_str = serial_str[4:].strip()
                        if serial_str and len(serial_str) > 2 and any(c.isdigit() for c in serial_str):
                            result['transaction_id'] = serial_str
            
            # Try to get transaction date/time
            if hasattr(pos_instance, 'GetTrxnDateTime'):
                transaction_datetime = pos_instance.GetTrxnDateTime()
                if transaction_datetime and not result.get('transaction_datetime'):
                    result['transaction_datetime'] = str(transaction_datetime).strip()
            
            # Try to get bank name
            if hasattr(pos_instance, 'GetBankName'):
                bank_name = pos_instance.GetBankName()
                if bank_name and not result.get('bank_name'):
                    result['bank_name'] = str(bank_name).strip()
            
            # Try to get response code
            if hasattr(pos_instance, 'GetTrxnResp'):
                resp_code = pos_instance.GetTrxnResp()
                if resp_code and not result.get('response_code'):
                    resp_code_str = str(resp_code).strip()
                    if resp_code_str and resp_code_str != '=' and resp_code_str != 'None':
                        result['response_code'] = resp_code_str
                        # Update success status based on response code
                        if resp_code_str == '00':
                            result['success'] = True
                            result['status'] = 'success'
            
            # Try to get card number
            if hasattr(pos_instance, 'GetPANID'):
                pan = pos_instance.GetPANID()
                if pan and not result.get('card_number'):
                    pan_str = str(pan).strip()
                    if pan_str and pan_str != '=' and pan_str != 'None' and pan_str != 'PN =':
                        if pan_str.startswith('PN ='):
                            pan_str = pan_str[4:].strip()
                        if pan_str and len(pan_str) > 2:
                            result['card_number'] = pan_str
        except Exception:
            pass
    
    # Generate transaction ID if not provided
    if not result['transaction_id']:
        result['transaction_id'] = f"POS-{int(time.time())}-{amount}"
    
    # IMPORTANT: Determine success based on response code AND presence of RRN
    # Use EXACT same logic as pos_dll_net.py
    has_rrn = bool(result.get('reference_number') and len(result['reference_number']) > 2)
    
    # Set success status
    if result['response_code'] == '00':
        result['success'] = True
        result['status'] = 'success'
    elif has_rrn:
        # If we have RRN, transaction was likely successful
        # Some POS devices return different response codes but still provide RRN
        result['success'] = True
        result['status'] = 'success'
    
    # Set response message
    if not result['response_message']:
        if result['response_code'] == '00':
            result['response_message'] = 'Transaction successful'
        elif result['response_code'] == '81':
            if has_rrn:
                result['response_message'] = 'Transaction completed'
            else:
                result['response_message'] = 'Transaction cancelled by user'
        elif result['response_code']:
            if has_rrn:
                result['response_message'] = f'Transaction completed (code: {result["response_code"]})'
            else:
                result['response_message'] = f'Transaction failed with code: {result["response_code"]}'
        else:
            if has_rrn:
                result['response_message'] = 'Transaction completed'
            else:
                result['response_message'] = 'No response from POS device'
    
    return result


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


if __name__ == '__main__':
    print("=" * 60)
    print("POS Bridge Service")
    print("=" * 60)
    print(f"Host: {HOST}")
    print(f"Port: {PORT}")
    print(f"DLL Path: {DLL_PATH}")
    print(f"POS Device: {POS_TCP_HOST}:{POS_TCP_PORT}")
    print("=" * 60)
    
    # Check if port is available
    print(f"\n🔍 Checking if port {PORT} is available...")
    if not check_port_available(PORT, HOST):
        print(f"❌ Port {PORT} is already in use or not accessible!")
        print(f"\n💡 Solutions:")
        print(f"   1. Change port in .env: POS_BRIDGE_PORT=8081")
        print(f"   2. Check what's using the port:")
        print(f"      netstat -ano | findstr :{PORT}")
        print(f"   3. Run as Administrator")
        print(f"   4. Check Windows Firewall settings")
        sys.exit(1)
    print(f"✅ Port {PORT} is available")
    
    # Initialize POS DLL
    if PYTHONNET_AVAILABLE:
        if not init_pos_dll():
            print("❌ Failed to initialize POS DLL. Service may not work correctly.")
            sys.exit(1)
    else:
        print("⚠️  pythonnet not available. Service will not work without DLL.")
        print("   Install with: pip install pythonnet")
    
    print(f"\n🚀 Starting server on {HOST}:{PORT}")
    print(f"📡 API Endpoints:")
    print(f"   GET  /health - Health check")
    print(f"   POST /test-connection - Test POS connection")
    print(f"   POST /payment - Process payment")
    print(f"\n💡 Example request:")
    print(f"   curl -X POST http://localhost:{PORT}/payment \\")
    print(f"        -H 'Content-Type: application/json' \\")
    print(f"        -d '{{\"amount\": 10000, \"order_number\": \"TEST-001\"}}'")
    print("\n" + "=" * 60 + "\n")
    
    try:
        app.run(host=HOST, port=PORT, debug=False)
    except OSError as e:
        if "access a socket in a way forbidden" in str(e) or "permission" in str(e).lower():
            print("\n" + "=" * 60)
            print("❌ خطا: دسترسی به پورت رد شد!")
            print("=" * 60)
            print("\n🔧 راه‌حل‌های ممکن:")
            print("\n1️⃣ تغییر پورت:")
            print("   در .env یا environment variables:")
            print("   POS_BRIDGE_PORT=8081  # یا هر پورت دیگری")
            print("\n2️⃣ بررسی استفاده از پورت:")
            print("   netstat -ano | findstr :8080")
            print("   اگر پورت استفاده شده، سرویس را ببندید یا پورت را تغییر دهید")
            print("\n3️⃣ اجرا به عنوان Administrator:")
            print("   - راست کلیک روی Command Prompt")
            print("   - انتخاب 'Run as administrator'")
            print("   - سپس دوباره اجرا کنید")
            print("\n4️⃣ غیرفعال کردن فایروال موقتاً (برای تست):")
            print("   - Windows Security > Firewall")
            print("   - یا در Command Prompt (as admin):")
            print("     netsh advfirewall set allprofiles state off")
            print("\n5️⃣ اضافه کردن exception در فایروال:")
            print("   - Windows Security > Firewall > Advanced settings")
            print("   - Inbound Rules > New Rule")
            print("   - Port > TCP > Specific local ports: 8080")
            print("   - Allow the connection")
            print("\n" + "=" * 60)
            sys.exit(1)
        else:
            raise

