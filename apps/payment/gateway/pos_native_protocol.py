"""
Native POS Protocol Implementation - Based on DLL Analysis

This module implements the exact protocol that DLL uses based on:
1. DLL tag analysis from DLL_INFO.md
2. Pardakht Novin POS device specifications
3. Common POS protocol patterns

The DLL uses a tag-based string format:
- Tags: PR, AM, TE, ME, SO, CU, etc.
- Format: TAG + VALUE (no separators between tags)
- Example: PR00AM000000010000TE30739260ME300000001235935SOTEST-002
"""

def build_payment_message(amount: int, terminal_id: str = '', merchant_id: str = '', 
                         order_number: str = '', customer_name: str = '', 
                         payment_id: str = '', bill_id: str = '') -> bytes:
    """
    Build payment message exactly as DLL does.
    
    Based on DLL analysis, the format is:
    PR{payment_type}AM{amount}TE{terminal_id}ME{merchant_id}SO{order_number}CU{customer_name}...
    
    Args:
        amount: Payment amount in Rial
        terminal_id: Terminal ID (8 digits)
        merchant_id: Merchant ID (15 digits)
        order_number: Order number (up to 20 chars)
        customer_name: Customer name (up to 50 chars)
        payment_id: Payment ID (up to 11 chars)
        bill_id: Bill ID (up to 20 chars)
        
    Returns:
        bytes: Formatted message ready to send
    """
    parts = []
    
    # PR - Payment Request Type (00 = normal payment)
    parts.append("PR00")
    
    # AM - Amount (12 digits, zero-padded)
    amount_str = str(amount).zfill(12)
    parts.append(f"AM{amount_str}")
    
    # TE - Terminal ID (8 digits, zero-padded)
    if terminal_id:
        terminal_id_str = str(terminal_id).zfill(8)
        parts.append(f"TE{terminal_id_str}")
    
    # ME - Merchant ID (15 digits, zero-padded)
    if merchant_id:
        merchant_id_str = str(merchant_id).zfill(15)
        parts.append(f"ME{merchant_id_str}")
    
    # SO - Sale Order / Order Number (up to 20 chars, left-padded with spaces)
    if order_number:
        order_num = order_number[:20] if len(order_number) > 20 else order_number
        parts.append(f"SO{order_num.ljust(20)}")
    
    # CU - Customer Name (up to 50 chars, left-padded with spaces)
    if customer_name:
        customer = customer_name[:50] if len(customer_name) > 50 else customer_name
        parts.append(f"CU{customer.ljust(50)}")
    
    # PD - Payment ID (11 digits, zero-padded)
    if payment_id:
        payment_id_str = str(payment_id)[:11].zfill(11)
        parts.append(f"PD{payment_id_str}")
    
    # BI - Bill ID (20 digits/chars, zero-padded)
    if bill_id:
        bill_id_str = str(bill_id)[:20].zfill(20)
        parts.append(f"BI{bill_id_str}")
    
    # Join all parts (no separator between tags)
    message = "".join(parts)
    
    # Convert to bytes (ASCII encoding for POS devices)
    return message.encode('ascii')


def parse_response(response: str) -> dict:
    """
    Parse response from POS device.
    
    Response format based on DLL analysis:
    RS{response_code}SR{serial}RN{reference}TI{terminal}PN{pan}...
    
    Args:
        response: Response string from POS
        
    Returns:
        dict: Parsed response data
    """
    result = {
        'success': False,
        'status': 'failed',
        'response_code': '',
        'response_message': '',
        'transaction_id': '',
        'card_number': '',
        'reference_number': '',
        'terminal_id': '',
        'raw_response': response
    }
    
    if not response:
        return result
    
    # RS - Response Status Code
    # RS013 or RS01 = success
    # RS00X = error (X = error code)
    if 'RS013' in response or 'RS01' in response:
        result['success'] = True
        result['status'] = 'success'
        result['response_code'] = '00'
    elif 'RS00' in response:
        # Extract error code
        import re
        match = re.search(r'RS00(\d+)', response)
        if match:
            result['response_code'] = match.group(1)
        else:
            result['response_code'] = '01'
        result['status'] = 'failed'
    
    # SR - Serial Number / Transaction Serial
    match = re.search(r'SR(\d+)', response)
    if match:
        result['transaction_id'] = match.group(1)
    
    # RN - Reference Number (RRN)
    match = re.search(r'RN(\d+)', response)
    if match:
        result['reference_number'] = match.group(1)
    
    # TI - Terminal ID
    match = re.search(r'TI(\d+)', response)
    if match:
        result['terminal_id'] = match.group(1)
    
    # PN - PAN (Card Number) - usually masked
    match = re.search(r'PN([\d*]+)', response)
    if match:
        result['card_number'] = match.group(1)
    
    # DS - Date (YYMMDD)
    match = re.search(r'DS(\d{6})', response)
    if match:
        result['transaction_date'] = match.group(1)
    
    # TM - Time (HHMM)
    match = re.search(r'TM(\d{4})', response)
    if match:
        result['transaction_time'] = match.group(1)
    
    return result

