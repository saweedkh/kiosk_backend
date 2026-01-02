"""
Management command to debug POS connection and DLL issues.

Usage:
    python manage.py debug_pos
"""
import os
import sys
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from apps.payment.gateway.adapter import PaymentGatewayAdapter
from apps.payment.gateway.exceptions import GatewayException


class Command(BaseCommand):
    help = 'عیب‌یابی اتصال POS و DLL'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n=== عیب‌یابی اتصال POS ===\n'))
        
        # 1. Check configuration
        self.stdout.write('1. بررسی تنظیمات:')
        config = settings.PAYMENT_GATEWAY_CONFIG
        self.stdout.write(f'   Gateway Name: {config.get("gateway_name")}')
        self.stdout.write(f'   Use DLL: {config.get("pos_use_dll")}')
        self.stdout.write(f'   DLL Path: {config.get("dll_path")}')
        self.stdout.write(f'   Terminal ID: {config.get("terminal_id")}')
        self.stdout.write(f'   Serial Number: {config.get("device_serial_number")}')
        self.stdout.write(f'   Connection Type: {config.get("connection_type")}')
        self.stdout.write(f'   TCP Host: {config.get("tcp_host")}')
        self.stdout.write(f'   TCP Port: {config.get("tcp_port")}')
        self.stdout.write('')
        
        # 2. Check DLL file
        self.stdout.write('2. بررسی فایل DLL:')
        dll_path = config.get('dll_path', '')
        if dll_path:
            if os.path.exists(dll_path):
                self.stdout.write(self.style.SUCCESS(f'   ✅ فایل DLL موجود است: {dll_path}'))
                self.stdout.write(f'   اندازه فایل: {os.path.getsize(dll_path)} bytes')
            else:
                self.stdout.write(self.style.ERROR(f'   ❌ فایل DLL پیدا نشد: {dll_path}'))
        else:
            self.stdout.write(self.style.WARNING('   ⚠️  مسیر DLL تنظیم نشده است'))
        self.stdout.write('')
        
        # 3. Check pythonnet
        self.stdout.write('3. بررسی pythonnet:')
        try:
            import clr
            self.stdout.write(self.style.SUCCESS('   ✅ pythonnet نصب است'))
            try:
                # Try to load a test DLL or check clr
                self.stdout.write(f'   نسخه clr: {clr.__version__ if hasattr(clr, "__version__") else "نامشخص"}')
            except Exception as e:
                self.stdout.write(f'   ⚠️  خطا در بررسی clr: {str(e)}')
        except ImportError:
            self.stdout.write(self.style.ERROR('   ❌ pythonnet نصب نیست'))
            self.stdout.write('   برای نصب: pip install pythonnet')
        self.stdout.write('')
        
        # 4. Try to load DLL
        if config.get('pos_use_dll') and dll_path and os.path.exists(dll_path):
            self.stdout.write('4. تلاش برای بارگذاری DLL:')
            try:
                import clr
                clr.AddReference(dll_path)
                from Intek.PcPosLibrary import PCPOS
                self.stdout.write(self.style.SUCCESS('   ✅ DLL با موفقیت بارگذاری شد'))
                
                # Try to create instance
                try:
                    pos_instance = PCPOS()
                    self.stdout.write(self.style.SUCCESS('   ✅ نمونه PCPOS ایجاد شد'))
                    
                    # Check available properties
                    self.stdout.write('\n   ویژگی‌های موجود در PCPOS:')
                    properties = [attr for attr in dir(pos_instance) if not attr.startswith('_')]
                    important_props = ['Amount', 'TerminalID', 'Ip', 'Port', 'ConnectionType', 
                                      'send_transaction', 'GetParsedResp', 'RawResponse', 
                                      'TestConnection', 'GetErrorMsg']
                    for prop in important_props:
                        if prop in properties:
                            self.stdout.write(self.style.SUCCESS(f'      ✅ {prop}'))
                        else:
                            self.stdout.write(self.style.WARNING(f'      ⚠️  {prop} (موجود نیست)'))
                    
                    # Try to set configuration
                    self.stdout.write('\n   تنظیمات اتصال:')
                    try:
                        pos_instance.Ip = config.get('tcp_host', '192.168.20.249')
                        pos_instance.Port = config.get('tcp_port', 1362)
                        pos_instance.ConnectionType = "LAN"
                        self.stdout.write(self.style.SUCCESS(f'      ✅ IP: {pos_instance.Ip}'))
                        self.stdout.write(self.style.SUCCESS(f'      ✅ Port: {pos_instance.Port}'))
                        self.stdout.write(self.style.SUCCESS(f'      ✅ ConnectionType: {pos_instance.ConnectionType}'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'      ❌ خطا در تنظیمات: {str(e)}'))
                    
                    # Try to set Terminal ID
                    terminal_id = config.get('terminal_id', '')
                    if terminal_id:
                        try:
                            pos_instance.TerminalID = str(terminal_id)
                            self.stdout.write(self.style.SUCCESS(f'      ✅ TerminalID: {pos_instance.TerminalID}'))
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'      ❌ خطا در تنظیم TerminalID: {str(e)}'))
                    
                    # Try to test connection
                    self.stdout.write('\n   تست اتصال:')
                    try:
                        result = pos_instance.TestConnection()
                        if result:
                            self.stdout.write(self.style.SUCCESS('      ✅ TestConnection: موفق'))
                        else:
                            self.stdout.write(self.style.ERROR('      ❌ TestConnection: ناموفق'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'      ❌ خطا در TestConnection: {str(e)}'))
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'   ❌ خطا در ایجاد نمونه: {str(e)}'))
                    import traceback
                    self.stdout.write(traceback.format_exc())
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ❌ خطا در بارگذاری DLL: {str(e)}'))
                import traceback
                self.stdout.write(traceback.format_exc())
            self.stdout.write('')
        
        # 5. Try to get gateway
        self.stdout.write('5. تلاش برای ایجاد Gateway:')
        try:
            gateway = PaymentGatewayAdapter.get_gateway()
            self.stdout.write(self.style.SUCCESS(f'   ✅ Gateway ایجاد شد: {gateway.__class__.__name__}'))
            
            # Check if it's DLL gateway
            if hasattr(gateway, 'use_dll'):
                self.stdout.write(f'   استفاده از DLL: {gateway.use_dll}')
                if hasattr(gateway, 'pos_instance') and gateway.pos_instance:
                    self.stdout.write(self.style.SUCCESS('   ✅ نمونه POS موجود است'))
                else:
                    self.stdout.write(self.style.WARNING('   ⚠️  نمونه POS موجود نیست'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ خطا در ایجاد Gateway: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())
        self.stdout.write('')
        
        # 6. Network connectivity test
        self.stdout.write('6. تست اتصال شبکه:')
        import socket
        tcp_host = config.get('tcp_host', '192.168.20.249')
        tcp_port = config.get('tcp_port', 1362)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((tcp_host, tcp_port))
            sock.close()
            if result == 0:
                self.stdout.write(self.style.SUCCESS(f'   ✅ اتصال به {tcp_host}:{tcp_port} موفق است'))
            else:
                self.stdout.write(self.style.ERROR(f'   ❌ اتصال به {tcp_host}:{tcp_port} ناموفق است (کد: {result})'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ خطا در تست شبکه: {str(e)}'))
        self.stdout.write('')
        
        self.stdout.write(self.style.SUCCESS('\n=== پایان عیب‌یابی ===\n'))

