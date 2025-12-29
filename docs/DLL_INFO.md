# اطلاعات فایل DLL: pna.pcpos.dll

## مشخصات فایل

- **نام فایل**: `pna.pcpos.dll`
- **نسخه**: `2.2.0.0`
- **نوع**: .NET Framework DLL (نسخه 4.0)
- **سازنده**: پرداخت نوین آرین (PNA)
- **تاریخ ساخت**: 2024
- **نوع فایل**: PE32 executable (DLL) برای Windows

## توابع اصلی موجود در DLL

از بررسی فایل DLL، توابع زیر شناسایی شدند:

### توابع اصلی تراکنش:
- `send_transaction` - ارسال تراکنش اصلی
- `send_transaction_ML` - ارسال تراکنش Multi-Lane
- `send_transaction_SL` - ارسال تراکنش Single-Lane
- `send_transaction_bill_payment` - پرداخت قبض
- `send_transaction_charge` - شارژ
- `send_transaction_Trx_Cancel` - لغو تراکنش
- `send_transaction_Trx_Revers` - برگشت تراکنش
- `send_transaction_Trx_Advice` - تایید تراکنش
- `send_transaction_Shift_Open` - باز کردن شیفت
- `send_transaction_Shift_Close` - بستن شیفت
- `send_transaction_Get_Lats_Trxn` - دریافت آخرین تراکنش
- `send_transaction_FaraPurchaseTwoSteps` - خرید فراپایا دو مرحله‌ای
- `send_transaction_FaraInquery` - استعلام فراپایا
- `send_transaction_MoallemInsurance` - بیمه معلم
- `send_transaction_WareHoff` - واریز
- `send_transaction_Kalabarg` - کالابرگ
- `send_transaction_food_safety` - سلامت غذا

### توابع کمکی:
- `TestConnection` - تست اتصال
- `GetParsedResp` - دریافت پاسخ پارس شده
- `GetTrxnResp` - دریافت پاسخ تراکنش
- `GetTrxnRRN` - دریافت شماره مرجع تراکنش
- `GetTrxnSerial` - دریافت سریال تراکنش
- `GetTrxnDateTime` - دریافت تاریخ و زمان تراکنش
- `GetBankName` - دریافت نام بانک
- `GetBankBin` - دریافت BIN بانک
- `GetTraceNo` - دریافت شماره ردیابی
- `GetTerminalID` - دریافت شناسه ترمینال
- `GetPANID` - دریافت شناسه PAN
- `GetKalaBargID` - دریافت شناسه کالابرگ
- `GetDiscount` - دریافت تخفیف
- `GetAmount` - دریافت مبلغ
- `GetNumericValue` - دریافت مقدار عددی

### توابع اتصال:
- `sendToLan` - ارسال از طریق شبکه (TCP/IP)
- `sendToSerialPort` - ارسال از طریق پورت سریال

## کلاس‌ها و Properties

از بررسی DLL، کلاس‌های زیر شناسایی شدند:

### کلاس اصلی: `PCPOS`
- `TerminalID` - شناسه ترمینال
- `BIllID` - شناسه قبض
- `PaymentID` - شناسه پرداخت
- `CH` - شماره چک
- `Service` - نوع سرویس
- `Code` - کد
- `SignCode` - کد امضا
- `PrCode` - کد محصول
- `ConnectionType` - نوع اتصال (LAN/SERIAL)
- `Response` - پاسخ
- `RawResponse` - پاسخ خام
- `ShiftClose` - بستن شیفت
- `baudRate` - نرخ انتقال سریال
- `KeyValue` - مقدار کلید
- `Kalabarg` - کالابرگ
- `CodeLength` - طول کد
- `CheckSumLength` - طول چک‌سام
- `MoallemSerial` - سریال معلم
- `Settel` - تسویه
- `ShiftOpen` - باز کردن شیفت
- `Ip` - آدرس IP
- `ServiceGroup` - گروه سرویس
- `ReferenceNumber` - شماره مرجع
- `Port` - پورت
- `ComPort` - پورت COM
- `Request` - درخواست
- `Currency` - ارز
- `foodSafety` - سلامت غذا
- `Amount` - مبلغ
- `Connected` - وضعیت اتصال
- `IsOpen` - باز بودن اتصال

### Properties برای Additional Data:
- `ID1` تا `ID10` - شناسه‌های اضافی
- `D1` تا `D10` - داده‌های اضافی
- `Y1` تا `Y10` - سال‌های اضافی
- `Amount1` تا `Amount10` - مبالغ اضافی

## نحوه استفاده

این DLL یک DLL .NET است و برای استفاده در Python نیاز به `pythonnet` دارد:

```python
import clr
clr.AddReference("pna.pcpos.dll")
from PCPOS import PCPOS

# ایجاد نمونه
pos = PCPOS()

# تنظیمات
pos.TerminalID = "12345678"
pos.Ip = "192.168.1.100"
pos.Port = 1362
pos.ConnectionType = "LAN"

# تست اتصال
if pos.TestConnection():
    # ارسال تراکنش
    pos.Amount = 50000
    pos.send_transaction()
    
    # دریافت پاسخ
    response = pos.GetParsedResp()
```

## نکات مهم

1. **این DLL فقط در Windows کار می‌کند**
2. **نیاز به .NET Framework 4.0 یا بالاتر دارد**
3. **برای استفاده در Python نیاز به `pythonnet` دارد**
4. **DLL باید در مسیر قابل دسترسی باشد**

## کدهای پاسخ

از بررسی DLL، کدهای پاسخ زیر شناسایی شدند:
- `MSG_ID_SUCCESS` - موفقیت
- `MSG_ID_INVALID` - نامعتبر
- `MSG_ID_INVALID_SIGNCODE` - کد امضا نامعتبر
- `MSG_ID_EMPTY_BOTH` - هر دو خالی
- `MSG_ID_EMPTY_ACCOUNT` - حساب خالی
- `MSG_ID_EMPTY_SERIAL` - سریال خالی

## فرمت پیام‌ها

از بررسی DLL، تگ‌های زیر برای ساخت پیام شناسایی شدند:
- `PR` - پرداخت
- `AM` - مبلغ
- `CU` - مشتری
- `TL` - تلفن
- `SD` - تاریخ
- `R1` تا `R9`, `R0` - فیلدهای R
- `T1`, `T2` - فیلدهای T
- `SV` - سرویس
- `SG` - گروه سرویس
- `AD` - آدرس
- `A1` تا `A10` - مبالغ اضافی
- `I1` تا `I10` - شناسه‌های اضافی
- `D1` تا `D10` - داده‌های اضافی
- `Y1` تا `Y10` - سال‌های اضافی
- `PD` - شناسه پرداخت
- `BI` - شناسه قبض
- `PI` - شناسه پرداخت
- `CH` - شماره چک
- `SO` - شماره سفارش
- `TC` - کد تراکنش
- `GA` - کد گارانتی
- `GR` - کد گروه
- `LT` - آخرین تراکنش
- `FS` - سلامت غذا
- `SC` - کد سرویس
- `GT` - کد گروه
- `SE` - کد تسویه
- `AN` - شماره حساب
- `FA` - کد فاکتور
- `KB` - کالابرگ
- `RN` - شماره مرجع
- `DS` - تاریخ
- `TR` - تراکنش
- `EX` - کد خطا
- `PN` - شماره پین
- `TM` - زمان
- `SR` - سریال
- `TI` - شناسه ترمینال

