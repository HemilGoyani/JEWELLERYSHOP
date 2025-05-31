from django.urls import path
from .views import OrderAPIView, CreateRazorpayOrder, VerifyPayment, SellingListAPI, SellsVsStockAPI, OrderPaymentListView, InvoiceListView, DownloadInvoiceView 

urlpatterns = [
    # Product Type API
    path('', OrderAPIView.as_view(), name='product_type_list_create'),
    path('<int:pk>/', OrderAPIView.as_view(), name='product_type_detail'),
    path('checkout-order/', CreateRazorpayOrder.as_view(), name='checkout_order'),
    path('verify-payment/', VerifyPayment.as_view(), name='verify_payment'),
    path('sellings/', SellingListAPI.as_view(), name='selling-list'),
    path('sell-versus-stock/', SellsVsStockAPI.as_view(), name='sell-versus-stock'),
    path('order-payments/', OrderPaymentListView.as_view(), name='order-payment-list'),
    path('invoices/', InvoiceListView.as_view(), name='invoice-list'),
    path('invoices/<int:pk>/download/', DownloadInvoiceView.as_view(), name='invoice-download'),
]