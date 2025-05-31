from rest_framework import serializers
from .models import Order, OrderItem, Notification, Selling
from product.models import Product, ProductVariant
from django.shortcuts import get_object_or_404
from users.models import User
from users.serializers import UserListSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product_variant', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    is_valid_time = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'user', 'total_price', 'items', 
            'time_duration', 'is_approved', 'is_deleted', 'is_valid_time'
        ]
        read_only_fields = ('user', 'total_price', 'time_duration', 'is_approved', 'is_deleted', 'order_number')

    def get_is_valid_time(self, obj):
        # Call the valid_time method to determine if the order is still valid
        return obj.valid_time()

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        total_price = 0

        # Create the order
        order = Order.objects.create(**validated_data)

        # Calculate total price based on items and create OrderItem instances
        for item_data in items_data:
            # Extract the product ID instead of the product instance
            product_variant = item_data.get("product_variant", None)

            # Validate product_variant belongs to product_color
            product_variant = get_object_or_404(ProductVariant, id=product_variant.id)

            quantity = item_data['quantity']
            price = product_variant.price
            total_price += quantity * price

            # Create the OrderItem instance
            OrderItem.objects.create(order=order, **item_data)

        # Update the total price in the order
        order.total_price = total_price
        order.save()

        return order


class SendPaymentRequestSerializer(serializers.ModelSerializer):
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all(), write_only=True)
    order_details = OrderSerializer(source='order', read_only=True)
    class Meta:
        model = Notification
        fields = ['id', 'order', 'order_details', 'token_payment', 'sender', 'receiver', 'status', 'is_admin_read', 'is_read', 'created_at', 'updated_at']
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']


class ApproveNotificationSerializer(serializers.ModelSerializer):
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all(), write_only=True)
    order_details = OrderSerializer(source='order', read_only=True)
    class Meta:
        model = Notification
        fields = ['id', 'order', 'order_details', 'token_payment', 'sender', 'receiver']
        extra_kwargs = {
            'is_approved': {'required': True},
            'time_duration': {'required': True}
        }
        read_only_fields = ['id', 'order', 'order_details', 'token_payment', 'sender', 'receiver']


class SellingSerializer(serializers.ModelSerializer):
    product_variant = serializers.CharField(source='product_variant.product.code')
    product_type = serializers.CharField(source='product_variant.product.product_type.name')
    product_brand = serializers.CharField(source='product_variant.product.product_brand.name')
    order_id = serializers.IntegerField(source='order.id')
    quantity = serializers.IntegerField()

    class Meta:
        model = Selling
        fields = ['order_id', 'product_variant', 'product_type', 'product_brand', 'quantity', 'created_at']

class SellsVsStockSerializer(serializers.Serializer):
    product_variant = serializers.CharField(source='product_variant.product.code')
    product_type = serializers.CharField(source='product_variant.product.product_type.name')
    product_brand = serializers.CharField(source='product_variant.product.product_brand.name')
    total_sold = serializers.IntegerField()
    total_stock = serializers.IntegerField()


class OrderPaymentSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email")
    total_price = serializers.FloatField()

    class Meta:
        model = Order
        fields = ['id', 'user_email', 'total_price', 'status', 'is_paid', 'razorpay_payment_id', 'created_at']


class InvoiceListSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    class Meta:
        model = Order
        fields = ['id', 'order_number', 'user', 'total_price', 'status', 'is_paid']
    
    def get_user(self, obj):
        user_data = User.objects.filter(id=obj.user.id)
        return UserListSerializer(
            user_data, read_only=True, context=self.context
        ).data