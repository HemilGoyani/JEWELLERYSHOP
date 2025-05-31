from rest_framework import generics, permissions, status
from .models import Memo, MemoDetail, QualityCheck
from .serializers import MemoSerializer, MemoDetailSerializer, EmployeeSerializer, QualityCheckSerializer, ProductVariantSerializer
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from product.models import ProductVariant, Product, Employee
from django.http import FileResponse
from barcode.writer import ImageWriter
from users.models import User
import barcode
import io
import json


class MemoAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        serializer = MemoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                created_by = self.request.user,
                updated_by = self.request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, memo_id=None):
        if memo_id:
            memo = Memo.objects.prefetch_related('memo_detail').get(id=memo_id)
            serializer = MemoSerializer(memo)
            return Response(serializer.data)
        
        memos = Memo.objects.prefetch_related('memo_detail').all()
        serializer = MemoSerializer(memos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, memo_id):
        memo = Memo.objects.get(id=memo_id)
        serializer = MemoSerializer(memo, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(
                updated_by = self.request.user
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, memo_id):
        memo = Memo.objects.get(id=memo_id)
        memo.delete()
        return Response({"message": "Memo deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class MemoDetailAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = MemoDetailSerializer

    def get(self, request, memo_id):
        # Check if the memo exists
        memo = get_object_or_404(Memo, id=memo_id)
        
        # Filter MemoDetail objects by the specified memo
        memo_details = MemoDetail.objects.filter(memo=memo)
        serializer = self.get_serializer(memo_details, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)


class GenerateBarcodeAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, id):
        # Fetch the product variant using the given ID
        product_variant = get_object_or_404(ProductVariant, pk=id, status=ProductVariant.ACTIVE)

        # Construct the data as a dictionary for JSON formatting
        barcode_data = {
            "Code": product_variant.product_color.product.code,
        }

        # Convert the dictionary to a JSON string
        barcode_data_json = json.dumps(barcode_data, separators=(',', ':'))

        # Generate the barcode with JSON data
        barcode_class = barcode.get_barcode_class('code128')
        barcode_instance = barcode_class(barcode_data_json, writer=ImageWriter())

        # Customize the writer to remove the text
        buffer = io.BytesIO()
        barcode_instance.write(buffer, options={'write_text': False})
        buffer.seek(0)

        # Return the barcode image as a response
        return FileResponse(buffer, as_attachment=True, filename=f"{product_variant.product_color.product.code}-barcode.png", content_type='image/png')


class EmployeeListCreateAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        employees = Employee.objects.all()
        serializer = EmployeeSerializer(employees, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = EmployeeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                created_by = self.request.user,
                updated_by = self.request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmployeeRetrieveUpdateDeleteAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get_object(self, id):
        try:
            return Employee.objects.get(pk=id)
        except Employee.DoesNotExist:
            return None

    def get(self, request, id):
        employee = self.get_object(id)
        if not employee:
            return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = EmployeeSerializer(employee)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, id):
        employee = self.get_object(id)
        if not employee:
            return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = EmployeeSerializer(employee, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        employee = self.get_object(id)
        if not employee:
            return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)
        employee.delete()
        return Response({"message": "Employee deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class QualityCheckCreateAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        data = request.data
        memo_id = data.get("memo_id", None)
        memo_detail_id = data.get("memo_detail_id", None)
        variant_id = data.get("variant_id", None)
        assigned_employee_id = data.get("assigned_employee_id", None)
        sender_id = self.request.user.id

        if not assigned_employee_id:
            return Response({"error": "Assigned employee is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            assigned_employee = Employee.objects.get(id=assigned_employee_id)
            sender = User.objects.get(id=sender_id)
        except (Employee.DoesNotExist, User.DoesNotExist):
            return Response({"error": "Invalid employee or sender."}, status=status.HTTP_404_NOT_FOUND)

        qc_records = []

        if memo_id:
            memo_details = MemoDetail.objects.filter(memo_id=memo_id)
            for detail in memo_details:
                qc = QualityCheck(
                    memo_detail_id=detail.id,
                    sender=sender,
                    assigned_employee=assigned_employee,
                    qc_status = QualityCheck.INPROCESS,
                )
                qc_records.append(qc)
                detail.qc_employee = assigned_employee
                detail.save()
            Memo.objects.filter(id=memo_id).update(qc_employee=assigned_employee)

        elif memo_detail_id:
            try:
                memo_detail = MemoDetail.objects.get(id=memo_detail_id)
                qc = QualityCheck(
                    memo_detail_id=memo_detail.id,
                    sender=sender,
                    assigned_employee=assigned_employee,
                    qc_status = QualityCheck.INPROCESS
                )
                qc_records.append(qc)
                memo_detail.qc_employee = assigned_employee
                memo_detail.save()
            except MemoDetail.DoesNotExist:
                return Response({"error": "MemoDetail not found."}, status=status.HTTP_404_NOT_FOUND)

        elif variant_id:
            try:
                product_variant = ProductVariant.objects.get(id=variant_id)
                qc = QualityCheck(
                    product_variant=product_variant,
                    sender=sender,
                    assigned_employee=assigned_employee,
                    qc_status = QualityCheck.INPROCESS
                )
                qc_records.append(qc)
                product_variant.qc_employee = assigned_employee
                product_variant.qc_status = QualityCheck.INPROCESS
                product_variant.save()
            except:
                return Response({"error": "Product variant not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"error": "Either memo_id or memo_detail_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Bulk create records
        QualityCheck.objects.bulk_create(qc_records)

        serializer = QualityCheckSerializer(qc_records, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class QualityCheckListAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        qc_records = QualityCheck.objects.all()
        serializer = QualityCheckSerializer(qc_records, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class AssignToStock(APIView):
    """
    Assign product variant to stock by updating the is_stock flag.
    """
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, *args, **kwargs):
        # Retrieve the Quality Check ID from the request body
        qc_id = request.data.get("qc_id", None)

        if not qc_id:
            return Response({"error": "QC ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch the QualityCheck instance
            quality_check = QualityCheck.objects.get(id=qc_id)
            if quality_check.qc_status == ProductVariant.APPROVED:
                return Response({"error": "Already Approved with this QC."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                product_variant = quality_check.memo_detail.product_variant
                quality_check.memo_detail.qc_status = ProductVariant.APPROVED
                quality_check.memo_detail.save()
            except:
                product_variant = quality_check.product_variant

            if not product_variant:
                return Response({"error": "No Product Variant associated with this QC."}, status=status.HTTP_400_BAD_REQUEST)

            # Update the `is_stock` field of the ProductVariant
            product_variant.is_stock = True
            product_variant.updated_by = self.request.user
            product_variant.qc_status = ProductVariant.APPROVED
            product_variant.save()
            quality_check.qc_status = ProductVariant.APPROVED
            quality_check.save()

            # Delete the QC List
            # quality_check.delete()

            return Response(
                {"message": f"Product Variant {product_variant.product.code} marked as stock."},
                status=status.HTTP_200_OK
            )

        except QualityCheck.DoesNotExist:
            return Response({"error": "QualityCheck not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AssignToPurchase(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        qc_id = request.data.get("qc_id", None)
        defect_notes = request.data.get("defect_notes", "")

        if not qc_id:
            return Response({"error": "QC ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch the QualityCheck instance
            quality_check = QualityCheck.objects.get(id=qc_id)
            if quality_check.qc_status == ProductVariant.APPROVED:
                return Response({"error": "Already Approved with this QC."}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                product_variant = quality_check.memo_detail.product_variant
                quality_check.memo_detail.qc_status = ProductVariant.REJECTED
                quality_check.memo_detail.save()
            except:
                product_variant = quality_check.product_variant

            if not product_variant:
                return Response({"error": "ProductVariant not found."}, status=status.HTTP_404_NOT_FOUND)

            # Update the ProductVariant notes and QC flag
            product_variant.notes = defect_notes
            product_variant.is_stock = False
            product_variant.save()

            product_variant.is_stock = True
            product_variant.updated_by = self.request.user
            product_variant.qc_status = ProductVariant.REJECTED
            product_variant.save()
            quality_check.qc_status = ProductVariant.REJECTED
            quality_check.save()

            return Response(
                {"message": "ProductVariant updated successfully.", "product_variant_id": product_variant.id},
                status=status.HTTP_200_OK,
            )

        except QualityCheck.DoesNotExist:
            return Response({"error": "QualityCheck not found."}, status=status.HTTP_404_NOT_FOUND)

class ProductVariantsInStock(APIView):
    permission_classes = [permissions.AllowAny]  # Adjust permissions as needed

    def get(self, request):
        # Filter product variants with is_stock=True
        in_stock_variants = ProductVariant.objects.filter(is_stock=True)

        # Serialize the data
        serializer = ProductVariantSerializer(in_stock_variants, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)