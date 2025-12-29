# مقایسه نحوه اتصال: DLL vs pos.py

## خلاصه

**بله، هر دو از سوکت (TCP/IP) یا پورت سریال استفاده می‌کنند!**

## نحوه اتصال

### DLL (pna.pcpos.dll)

```csharp
// در داخل DLL (کد .NET):
// برای TCP/IP:
TcpClient client = new TcpClient();
client.Connect(ip, port);
NetworkStream stream = client.GetStream();

// برای Serial:
SerialPort serialPort = new SerialPort();
serialPort.PortName = "COM1";
serialPort.BaudRate = 9600;
serialPort.Open();
```

### pos.py (پروتکل مستقیم)

```python
# برای TCP/IP:
import socket
connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connection.connect((host, port))

# برای Serial:
import serial
connection = serial.Serial(port='COM1', baudrate=9600)
```

## تفاوت‌ها

| ویژگی | DLL | pos.py |
|-------|-----|--------|
| **TCP/IP** | `TcpClient` + `NetworkStream` (.NET) | `socket.socket` (Python) |
| **Serial** | `SerialPort` (.NET) | `serial.Serial` (pyserial) |
| **زبان** | C#/.NET | Python |
| **نتیجه** | ✅ هر دو به کارت‌خوان وصل می‌شوند | ✅ هر دو به کارت‌خوان وصل می‌شوند |

## کد واقعی

### در DLL:
```python
# pos_dll_net.py
self.pos_instance.Ip = "192.168.1.100"
self.pos_instance.Port = 1362
self.pos_instance.ConnectionType = "LAN"
# DLL خودش با TcpClient وصل می‌شود
```

### در pos.py:
```python
# pos.py
self._connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
self._connection.connect(("192.168.1.100", 1362))
# ما خودمان با socket وصل می‌شویم
```

## نتیجه‌گیری

✅ **هر دو از سوکت استفاده می‌کنند**
- DLL: از طریق `TcpClient` در .NET
- pos.py: از طریق `socket` در Python

✅ **هر دو به یک کارت‌خوان وصل می‌شوند**
- فقط روش پیاده‌سازی متفاوت است
- نتیجه یکسان است

## مثال عملی

### با DLL:
```
برنامه Python
    ↓
DLL (pna.pcpos.dll)
    ↓
TcpClient (.NET)
    ↓
Socket (TCP/IP)
    ↓
کارت‌خوان POS
```

### با pos.py:
```
برنامه Python
    ↓
socket.socket (Python)
    ↓
Socket (TCP/IP)
    ↓
کارت‌خوان POS
```

**هر دو در نهایت از همان پروتکل TCP/IP استفاده می‌کنند!**

