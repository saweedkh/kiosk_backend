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
        max_attempts = 120
        start_time = time.time()
        response_obj = None
        
        for attempt in range(max_attempts):
            if attempt > 0:
                time.sleep(1)
            
            elapsed = int(time.time() - start_time)
            if elapsed > 0 and elapsed % 10 == 0:
                print(f"⏳ Waiting for response... ({elapsed}/{max_attempts} seconds)")
            
            # Check for response
            try:
                if hasattr(pos_instance, 'Response') and pos_instance.Response is not None:
                    response_obj = pos_instance.Response
                    
                    # Check for response code
                    resp_code = None
                    if hasattr(response_obj, 'GetTrxnResp'):
                        resp_code = response_obj.GetTrxnResp()
                        resp_code_str = str(resp_code).strip() if resp_code else ''
                        if resp_code_str and resp_code_str != '=' and resp_code_str != 'None' and resp_code_str != '':
                            print(f"✅ Response Code received: {resp_code_str}")
                            break
                    
                    # Check for RRN
                    if hasattr(response_obj, 'GetTrxnRRN'):
                        rrn = response_obj.GetTrxnRRN()
                        rrn_str = str(rrn).strip() if rrn else ''
                        if rrn_str and rrn_str != '=' and rrn_str != 'None' and rrn_str != 'RN =' and len(rrn_str) > 2:
                            if any(c.isdigit() for c in rrn_str):
                                print(f"✅ RRN received: {rrn_str}")
                                break
            except Exception as e:
                pass
            
            # Check pos_instance methods directly
            try:
                if hasattr(pos_instance, 'GetTrxnResp'):
                    resp_code = pos_instance.GetTrxnResp()
                    resp_code_str = str(resp_code).strip() if resp_code else ''
                    if resp_code_str and resp_code_str != '=' and resp_code_str != 'None' and resp_code_str != '':
                        print(f"✅ Response Code from pos_instance: {resp_code_str}")
                        if hasattr(pos_instance, 'Response'):
                            response_obj = pos_instance.Response
                        break
            except Exception:
                pass
            
            try:
                if hasattr(pos_instance, 'GetTrxnRRN'):
                    rrn = pos_instance.GetTrxnRRN()
                    rrn_str = str(rrn).strip() if rrn else ''
                    if rrn_str and rrn_str != 'None' and rrn_str != '' and rrn_str != '=' and len(rrn_str) > 2:
                        if any(c.isdigit() for c in rrn_str):
                            print(f"✅ RRN from pos_instance: {rrn_str}")
                            if hasattr(pos_instance, 'Response'):
                                response_obj = pos_instance.Response
                            break
            except Exception:
                pass
        
        # Parse response
        result = {
            'success': False,
            'status': 'failed',
            'response_code': '',
            'response_message': '',
            'transaction_id': '',
            'card_number': '',
            'reference_number': '',
            'amount': amount
        }
        
        # IMPORTANT: Try to get data from pos_instance directly first
        # Sometimes response_obj might not have all data, but pos_instance methods do
        try:
            # Get response code from pos_instance
            if hasattr(pos_instance, 'GetTrxnResp'):
                resp_code = pos_instance.GetTrxnResp()
                if resp_code:
                    resp_code_str = str(resp_code).strip()
                    # Clean up response code (remove "=" or other artifacts)
                    if resp_code_str and resp_code_str != '=' and resp_code_str != 'None':
                        result['response_code'] = resp_code_str
                        print(f"📋 Response Code from pos_instance: {resp_code_str}")
            
            # Get RRN from pos_instance
            if hasattr(pos_instance, 'GetTrxnRRN'):
                rrn = pos_instance.GetTrxnRRN()
                if rrn:
                    rrn_str = str(rrn).strip()
                    # Clean up RRN (remove "RN =", "=", etc.)
                    if rrn_str and rrn_str != '=' and rrn_str != 'None' and rrn_str != 'RN =':
                        # Remove "RN =" prefix if present
                        if rrn_str.startswith('RN ='):
                            rrn_str = rrn_str[4:].strip()
                        if rrn_str and len(rrn_str) > 2 and any(c.isdigit() for c in rrn_str):
                            result['reference_number'] = rrn_str
                            print(f"📋 RRN from pos_instance: {rrn_str}")
            
            # Get serial from pos_instance
            if hasattr(pos_instance, 'GetTrxnSerial'):
                serial = pos_instance.GetTrxnSerial()
                if serial:
                    serial_str = str(serial).strip()
                    # Clean up serial (remove "SR =", "=", etc.)
                    if serial_str and serial_str != '=' and serial_str != 'None' and serial_str != 'SR =':
                        # Remove "SR =" prefix if present
                        if serial_str.startswith('SR ='):
                            serial_str = serial_str[4:].strip()
                        if serial_str and len(serial_str) > 2 and any(c.isdigit() for c in serial_str):
                            result['transaction_id'] = serial_str
                            print(f"📋 Serial from pos_instance: {serial_str}")
            
            # Get card number from pos_instance
            if hasattr(pos_instance, 'GetPANID'):
                pan = pos_instance.GetPANID()
                if pan:
                    pan_str = str(pan).strip()
                    # Clean up PAN (remove "PN =", "=", etc.)
                    if pan_str and pan_str != '=' and pan_str != 'None' and pan_str != 'PN =':
                        # Remove "PN =" prefix if present
                        if pan_str.startswith('PN ='):
                            pan_str = pan_str[4:].strip()
                        if pan_str and len(pan_str) > 2:
                            result['card_number'] = pan_str
                            print(f"📋 PAN from pos_instance: {pan_str}")
            
            # Get bank name from pos_instance
            if hasattr(pos_instance, 'GetBankName'):
                bank = pos_instance.GetBankName()
                if bank:
                    bank_str = str(bank).strip()
                    if bank_str and bank_str != '=' and bank_str != 'None':
                        result['bank_name'] = bank_str
                        print(f"📋 Bank Name from pos_instance: {bank_str}")
        except Exception as e:
            print(f"⚠️  Error getting data from pos_instance: {e}")
        
        # Also try to get from response_obj if available
        if response_obj:
            try:
                # Get response code (if not already set)
                if not result['response_code'] and hasattr(response_obj, 'GetTrxnResp'):
                    resp_code = response_obj.GetTrxnResp()
                    if resp_code:
                        resp_code_str = str(resp_code).strip()
                        if resp_code_str and resp_code_str != '=' and resp_code_str != 'None':
                            result['response_code'] = resp_code_str
                
                # Get RRN (if not already set)
                if not result['reference_number'] and hasattr(response_obj, 'GetTrxnRRN'):
                    rrn = response_obj.GetTrxnRRN()
                    if rrn:
                        rrn_str = str(rrn).strip()
                        if rrn_str and rrn_str != '=' and rrn_str != 'None' and rrn_str != 'RN =':
                            if rrn_str.startswith('RN ='):
                                rrn_str = rrn_str[4:].strip()
                            if rrn_str and len(rrn_str) > 2 and any(c.isdigit() for c in rrn_str):
                                result['reference_number'] = rrn_str
                
                # Get serial (if not already set)
                if not result['transaction_id'] and hasattr(response_obj, 'GetTrxnSerial'):
                    serial = response_obj.GetTrxnSerial()
                    if serial:
                        serial_str = str(serial).strip()
                        if serial_str and serial_str != '=' and serial_str != 'None' and serial_str != 'SR =':
                            if serial_str.startswith('SR ='):
                                serial_str = serial_str[4:].strip()
                            if serial_str and len(serial_str) > 2 and any(c.isdigit() for c in serial_str):
                                result['transaction_id'] = serial_str
                
                # Get card number (if not already set)
                if not result['card_number'] and hasattr(response_obj, 'GetPANID'):
                    pan = response_obj.GetPANID()
                    if pan:
                        pan_str = str(pan).strip()
                        if pan_str and pan_str != '=' and pan_str != 'None' and pan_str != 'PN =':
                            if pan_str.startswith('PN ='):
                                pan_str = pan_str[4:].strip()
                            if pan_str and len(pan_str) > 2:
                                result['card_number'] = pan_str
                
                # Get bank name (if not already set)
                if not result.get('bank_name') and hasattr(response_obj, 'GetBankName'):
                    bank = response_obj.GetBankName()
                    if bank:
                        bank_str = str(bank).strip()
                        if bank_str and bank_str != '=' and bank_str != 'None':
                            result['bank_name'] = bank_str
            except Exception as e:
                print(f"⚠️  Error parsing response_obj: {e}")
        
        # Generate transaction ID if not provided
        if not result['transaction_id']:
            result['transaction_id'] = f"POS-{int(time.time())}-{amount}"
        
        # IMPORTANT: Determine success based on response code AND presence of RRN
        # If we have RRN, transaction was likely successful even if response code is not '00'
        # Response code '81' might mean different things depending on POS device
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
            print(f"✅ Transaction considered successful (has RRN: {result['reference_number']})")
        
        # Set response message
        if not result['response_message']:
            if result['response_code'] == '00':
                result['response_message'] = 'Transaction successful'
            elif result['response_code'] == '81':
                if has_rrn:
                    # If we have RRN, '81' might not mean cancelled
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

