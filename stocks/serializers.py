from rest_framework import serializers
from .models import Memo, MemoDetail, ProductVariant, QualityCheck
from product.serializers import ProductVariantSerializer, ProductSerializer
from product.models import ProductVariant, Employee
from users.models import User
from users.serializers import UserListSerializer
import random
import string


class MemoDetailSerializer(serializers.ModelSerializer):
    product_variant = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all(), write_only=True)
    product_variant_details = ProductVariantSerializer(source='product_variant', read_only=True)
    price = serializers.FloatField(source='product_variant.price', read_only=True)
    weight = serializers.FloatField(source='product_variant.weight', read_only=True)
    QC = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = MemoDetail
        fields = ['product_variant', 'product_variant_details', 'price', 'weight', 'QC']

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Check if a related QualityCheck exists for this MemoDetail
        qc_exists = QualityCheck.objects.filter(memo_detail=instance).exists()

        # Set QC to True if a related QualityCheck exists, otherwise False
        data['QC'] = qc_exists
        return data

class MemoSerializer(serializers.ModelSerializer):
    memo_detail = MemoDetailSerializer(many=True)
    jangad_number = serializers.CharField(read_only=True)
    total_amount = serializers.FloatField(read_only=True)
    total_pieces = serializers.IntegerField(read_only=True)
    total_weight = serializers.FloatField(read_only=True)

    class Meta:
        model = Memo
        fields = ['id', 'client_name', 'company_name', 'jangad_number', 'memo_detail', 'total_amount', 'total_pieces', 'total_weight', 'qc_employee']
        read_only_fields =  ['id']
 
    def create(self, validated_data):
        # Generate a random jangad_number
        jangad_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        # Extract memo details data
        memo_details_data = validated_data.pop('memo_detail')
        
        # Create memo instance
        memo = Memo.objects.create(jangad_number=jangad_number, **validated_data)
        
        # Create MemoDetail instances
        for detail_data in memo_details_data:
            MemoDetail.objects.create(memo=memo, **detail_data)
        
        return memo

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Calculate total pieces, total weight, and total amount, with defaults to handle missing values
        total_pieces = len(data['memo_detail'])
        total_weight = sum(detail['product_variant_details']['weight'] for detail in data['memo_detail'])
        total_amount = sum(detail.get('price', 0.0) for detail in data['memo_detail'])
        
        # Add these totals to the response
        data['total_pieces'] = total_pieces
        data['total_weight'] = total_weight
        data['total_amount'] = total_amount
        
        return data


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'

class QualityCheckSerializer(serializers.ModelSerializer):
    sender_detail = serializers.SerializerMethodField()
    assigned_employee_detail = serializers.SerializerMethodField()
    memo_detail_data = MemoDetailSerializer(source='memo_detail', read_only=True)

    class Meta:
        model = QualityCheck
        fields = ['id', 'sender_detail', 'assigned_employee_detail', 'memo_detail_data', 'qc_status']
    
    def get_sender_detail(self, obj):
        sender_data = User.objects.filter(id=obj.sender.id)
        return UserListSerializer(
            sender_data, many=True, read_only=True, context=self.context
        ).data
    
    def get_assigned_employee_detail(self, obj):
        sender_data = User.objects.filter(id=obj.assigned_employee.id)
        return UserListSerializer(
            sender_data, many=True, read_only=True, context=self.context
        ).data

class ProductVariantSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True) 
    class Meta:
        model = ProductVariant
        fields = ['id', 'product', 'color', 'weight', 'size', 'carat', 'price', 'quantity', 'notes', 'is_stock']