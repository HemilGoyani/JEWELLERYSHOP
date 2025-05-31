from django.db import models
from backend.models import BaseModel
from product.models import ProductVariant, Employee
from users.models import User

class Memo(BaseModel):
    client_name = models.CharField(max_length=255, null=True, blank=False)
    company_name = models.CharField(max_length=255, null=True, blank=False)
    jangad_number = models.CharField(max_length=255, null=True, blank=False)
    qc_employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name="product_variant")
    def __str__(self):
        return f"{self.client_name} - {self.jangad_number}"


class MemoDetail(BaseModel):
    PENDING = 'PENDING'
    INPROCESS = 'INPROCESS'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    
    QC_STATUS = [
        ('PENDING', 'PENDING'),
        ('INPROCESS', 'INPROCESS'),
        ('APPROVED', 'APPROVED'),
        ('REJECTED', 'REJECTED'),
    ]
    memo = models.ForeignKey(Memo, on_delete=models.CASCADE, related_name="memo_detail")
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, related_name="memo_product_category")
    qc_employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name="memo_detail_qc")
    qc_status = models.CharField(choices=QC_STATUS, default="PENDING")


    def __str__(self):
        return self.memo.jangad_number   


class QualityCheck(BaseModel):
    PENDING = 'PENDING'
    INPROCESS = 'INPROCESS'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    
    QC_STATUS = [
        ('PENDING', 'PENDING'),
        ('INPROCESS', 'INPROCESS'),
        ('APPROVED', 'APPROVED'),
        ('REJECTED', 'REJECTED'),
    ]
    memo_detail = models.ForeignKey(MemoDetail, null=True, blank=True, on_delete=models.CASCADE, related_name="qc_memo_detail")
    product_variant = models.ForeignKey(ProductVariant, null=True, blank=True, on_delete=models.CASCADE, related_name="qc_product_variant")
    sender = models.ForeignKey(User, null=False, blank=False, on_delete=models.CASCADE, related_name="qc_sender_client")
    assigned_employee = models.ForeignKey(Employee, null=False, blank=False, on_delete=models.CASCADE, related_name="qc_receiver_client")
    qc_status = models.CharField(choices=QC_STATUS, default="INPROCESS")

    def __str__(self):
        return self.product_variant.product.code