from django.urls import path
from .views import MemoAPIView, MemoDetailAPIView, GenerateBarcodeAPIView, EmployeeListCreateAPIView, EmployeeRetrieveUpdateDeleteAPIView, QualityCheckListAPIView, QualityCheckCreateAPIView, AssignToStock, AssignToPurchase, ProductVariantsInStock

urlpatterns = [
    path('', ProductVariantsInStock.as_view(), name='product-variants-in-stock'),
    path('memo/', MemoAPIView.as_view(), name='memo-list'),
    path('memo/<int:memo_id>/', MemoAPIView.as_view(), name='memo-detail'),
    path('memo/<int:memo_id>/details/', MemoDetailAPIView.as_view(), name='memo-details'),
    path('generate-barcode/<int:id>/', GenerateBarcodeAPIView.as_view(), name='generate-barcode'),
    path('employees/', EmployeeListCreateAPIView.as_view(), name='employee-list-create'),
    path('employees/<int:id>/', EmployeeRetrieveUpdateDeleteAPIView.as_view(), name='employee-retrieve-update-delete'),
    path('quality-checks/', QualityCheckListAPIView.as_view(), name='quality-check-list'),
    path('quality-checks/assign/', QualityCheckCreateAPIView.as_view(), name='quality-check-assign'),
    path('assign-to-stock/', AssignToStock.as_view(), name='assign-to-stock'),
    path('assign-to-purchase/', AssignToPurchase.as_view(), name='assign-to-purchase'),
]
