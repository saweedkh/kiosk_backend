from rest_framework import generics
from rest_framework.response import Response
from django.http import FileResponse
from apps.orders.models import Invoice
from apps.orders.api.invoices.invoices_serializers import InvoiceSerializer
from apps.orders.selectors.invoice_selector import InvoiceSelector
from apps.orders.services.invoice_service import InvoiceService


class InvoiceRetrieveAPIView(generics.RetrieveAPIView):
    serializer_class = InvoiceSerializer
    lookup_field = 'pk'
    
    def get_queryset(self):
        return InvoiceSelector.get_invoices_with_orders()


class InvoiceDownloadPDFAPIView(generics.GenericAPIView):
    def get(self, request, pk):
        invoice = InvoiceSelector.get_invoice_by_id(pk)
        if not invoice or not invoice.pdf_file:
            return Response({'error': 'Invoice PDF not found'}, status=404)
        
        return FileResponse(
            invoice.pdf_file.open('rb'),
            content_type='application/pdf',
            filename=f"{invoice.invoice_number}.pdf"
        )


class InvoiceDownloadJSONAPIView(generics.GenericAPIView):
    def get(self, request, pk):
        invoice = InvoiceSelector.get_invoice_by_id(pk)
        if not invoice:
            return Response({'error': 'Invoice not found'}, status=404)
        
        json_data = invoice.json_data or InvoiceService.get_invoice_data(invoice.order_id)
        
        return Response(json_data)


class InvoiceCreateAPIView(generics.GenericAPIView):
    def post(self, request, order_id):
        invoice = InvoiceService.create_invoice(order_id)
        
        return Response(
            InvoiceSerializer(invoice).data,
            status=201
        )

