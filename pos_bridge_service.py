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
PORT = int(os.getenv('POS_BRIDGE_PORT', 8080))
DLL_PATH = os.getenv('POS_DLL_PATH', 'pna.pcpos.dll')
POS_TCP_HOST = os.getenv('POS_TCP_HOST', '192.168.1.100')
POS_TCP_PORT = int(os.getenv('POS_TCP_PORT', 1362))
TERMINAL_ID = os.getenv('POS_TERMINAL_ID', '')
MERCHANT_ID = os.getenv('POS_MERCHANT_ID', '')
DEVICE_SERIAL = os.getenv('POS_DEVICE_SERIAL', '')

# Global POS instance
pos_instance = None


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
        
        if response_obj:
            try:
                # Get response code
                if hasattr(response_obj, 'GetTrxnResp'):
                    resp_code = response_obj.GetTrxnResp()
                    if resp_code:
                        result['response_code'] = str(resp_code).strip()
                        if result['response_code'] == '00':
                            result['success'] = True
                            result['status'] = 'success'
                        elif result['response_code'] == '81':
                            result['response_message'] = 'Transaction cancelled by user'
                
                # Get RRN
                if hasattr(response_obj, 'GetTrxnRRN'):
                    rrn = response_obj.GetTrxnRRN()
                    if rrn:
                        rrn_str = str(rrn).strip()
                        if rrn_str and rrn_str != '=' and rrn_str != 'None' and len(rrn_str) > 2:
                            result['reference_number'] = rrn_str
                
                # Get serial
                if hasattr(response_obj, 'GetTrxnSerial'):
                    serial = response_obj.GetTrxnSerial()
                    if serial:
                        serial_str = str(serial).strip()
                        if serial_str and serial_str != '=' and serial_str != 'None' and len(serial_str) > 2:
                            result['transaction_id'] = serial_str
                
                # Get card number
                if hasattr(response_obj, 'GetPANID'):
                    pan = response_obj.GetPANID()
                    if pan:
                        result['card_number'] = str(pan).strip()
                
                # Get bank name
                if hasattr(response_obj, 'GetBankName'):
                    bank = response_obj.GetBankName()
                    if bank:
                        result['bank_name'] = str(bank).strip()
            except Exception as e:
                print(f"⚠️  Error parsing response: {e}")
        
        # Generate transaction ID if not provided
        if not result['transaction_id']:
            result['transaction_id'] = f"POS-{int(time.time())}-{amount}"
        
        # Set response message
        if not result['response_message']:
            if result['response_code'] == '00':
                result['response_message'] = 'Transaction successful'
            elif result['response_code'] == '81':
                result['response_message'] = 'Transaction cancelled by user'
            elif result['response_code']:
                result['response_message'] = f'Transaction failed with code: {result["response_code"]}'
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
    print(f"   curl -X POST http://{HOST}:{PORT}/payment \\")
    print(f"        -H 'Content-Type: application/json' \\")
    print(f"        -d '{{\"amount\": 10000, \"order_number\": \"TEST-001\"}}'")
    print("\n" + "=" * 60 + "\n")
    
    app.run(host=HOST, port=PORT, debug=False)

