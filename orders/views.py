from rest_framework import status, permissions, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Order, Notification, OrderItem, Selling
from .serializers import OrderSerializer, SendPaymentRequestSerializer, SellingSerializer, OrderPaymentSerializer, InvoiceListSerializer
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.conf import settings
from django.utils import timezone
import razorpay
from datetime import timedelta
from product.models import ProductVariant, ProductType, BrandType
from datetime import datetime
from django.db.models import Sum
from django.utils.dateparse import parse_datetime
from django.http import FileResponse


class OrderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Retrieve a list of orders or a single order for the authenticated user.
        """
        order_id = kwargs.get('pk')
        if order_id:
            order = get_object_or_404(Order, pk=order_id, user=request.user)
            serializer = OrderSerializer(order)
            return Response(serializer.data)
        
        orders = Order.objects.filter(user=request.user)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        """
        Create a new order for the authenticated user.
        """
        # Pass the request context to the serializer
        serializer = OrderSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            order = serializer.save(
                user=self.request.user,
                created_by = self.request.user,
                updated_by = self.request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        """
        Delete an existing order for the authenticated user.
        """
        order = get_object_or_404(Order, pk=kwargs.get('pk'), user=request.user)
        order.delete()
        return Response({"message": "Order successfully deleted"}, status=status.HTTP_204_NO_CONTENT)

    
class SendPaymentRequest(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, notification_id=None):
        # If notification_id is passed, retrieve a specific notification
        if notification_id:
            notification = get_object_or_404(Notification, id=notification_id)
            serializer = SendPaymentRequestSerializer(notification)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Otherwise, retrieve all notifications
        if self.request.user.is_superuser:
            notifications = Notification.objects.all()
        else:
            notifications = Notification.objects.filter(sender_id=self.request.user.id)
            notifications.update(is_read=True)
        serializer = SendPaymentRequestSerializer(notifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        # Get the current user (sender)
        sender = self.request.user

        # Get the order ID from the request data
        order_id = request.data.get('order')

        # Fetch the order and check if the current user is the same as the order's user
        order = get_object_or_404(Order, id=order_id)

        if order.user != sender:
            return Response({"error": "You are not authorized to send a payment request for this order."}, status=status.HTTP_403_FORBIDDEN)

        # Fetch all superusers and create a list of their IDs
        from django.contrib.auth import get_user_model
        receivers = get_user_model().objects.filter(is_superuser=True)

        if not receivers.exists():
            return Response({"error": "No admin users found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if a notification already exists for this order and sender
        if Notification.objects.filter(order=order, sender=sender, status=Notification.PENDING).exists():
            return Response({"error": "You have already sent a payment request for this order."}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate 30% of the total order price for the token payment
        token_payment = order.total_price * 0.30

        # Create a comma-separated string of superuser IDs
        receiver_ids = ','.join(str(receiver.id) for receiver in receivers)

        # Prepare the payment data
        payment_data = {
            'order': order_id,
            'token_payment': token_payment,
            'sender': sender.id,
            'receiver': receiver_ids
        }

        # Use the serializer to save the notification
        serializer = SendPaymentRequestSerializer(data=payment_data)
        if serializer.is_valid():
            notification = serializer.save(
                created_by = self.request.user,
                updated_by = self.request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class DeleteNotification(APIView):
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, notification_id):
        # Fetch the notification object by ID
        notification = get_object_or_404(Notification, id=notification_id)

        # Ensure only the sender or an admin can delete the notification
        if notification.sender != request.user and not self.request.user.is_superuser:
            return Response({"error": "You are not authorized to delete this notification."}, status=status.HTTP_403_FORBIDDEN)

        # If authorized, delete the notification
        notification.status=Notification.DECLINED
        notification.is_admin_read=True
        notification.is_read=False
        notification.save(
            created_by = self.request.user,
            updated_by = self.request.user
        )
        return Response({"message": "Notification deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


def parse_duration(duration_str):
    """Helper function to convert a string like '40:30:00' to a timedelta."""
    try:
        hours, minutes, seconds = map(int, duration_str.split(':'))
        return timedelta(hours=hours, minutes=minutes, seconds=seconds)
    except ValueError:
        return Response({'error': 'Invalid duration format. Use HH:MM:SS format.'}, status=status.HTTP_403_FORBIDDEN)


class ApproveNotificationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, id):
        # Fetch the notification based on its primary key (id)
        notification = get_object_or_404(Notification, pk=id)
        
        # Only allow superusers (admins) to approve and set time duration
        if not self.request.user.is_superuser:
            return Response({'error': 'Only admin users can approve notifications.'}, status=status.HTTP_403_FORBIDDEN)

        # Get the request data
        is_approved = request.data.get('is_approved', False)
        time_duration_str = request.data.get('time_duration', None)

        # Ensure that the `is_approved` and `time_duration` fields are provided
        if not is_approved or not time_duration_str:
            return Response({'error': 'is_approved and time_duration are required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Convert the time_duration string to timedelta
        try:
            time_duration = parse_duration(time_duration_str)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        order = notification.order
        if order.is_approved and notification.status== Notification.APPROVED:
            return Response({'error': 'Payment request already approved.'}, status=status.HTTP_403_FORBIDDEN)
        
        # Start a transaction to update both Notification and Order
        with transaction.atomic():
            # Set the order's approval and time_duration
            order = notification.order
            order.time_duration = time_duration
            order.is_approved = True
            order.updated_at = timezone.now()
            order.updated_by = self.request.user
            order.save()

            # Update notification status to approved
            notification.status = Notification.APPROVED
            notification.is_admin_read = True
            notification.is_read = False
            notification.save()

        return Response({'message': 'Notification approved and payment window set.'}, status=status.HTTP_200_OK)


class NotificationCountAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = self.request.user
        
        # Admins get the count of all unread notifications
        if user.is_superuser:
            unread_count = Notification.objects.filter(is_admin_read=False).count()
        
        # Regular users get the count of their own unread notifications
        else:
            unread_count = Notification.objects.filter(sender=user, is_read=False).count()

        return Response({'unread_notification_count': unread_count}, status=status.HTTP_200_OK)


class CreateRazorpayOrder(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Get order details from your system
        order_id = request.data.get("order_id")
        order = get_object_or_404(Order, id=order_id)
        if not order.is_approved:
            return Response({'error': 'Admin can not approved order payment request.'}, status=status.HTTP_403_FORBIDDEN)

        if order.valid_time() and not order.is_paid:
        
            # Razorpay client initialization
            client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID,
                settings.RAZORPAY_KEY_SECRET)
            )
            
            # Create a Razorpay order
            razorpay_order_data = {
                "amount": int(order.total_price * 100),  # amount in paise (INR)
                "currency": "INR",
                "payment_capture": 1,  # automatic capture after payment
                "receipt": f"order_{order.id}",
            }
            
            try:
                razorpay_order = client.order.create(data=razorpay_order_data)
                order.razorpay_order_id = razorpay_order['id']
                order.created_by = self.request.user
                order.updated_by = self.request.user
                order.save()

                # Send order details to the frontend
                return Response({
                    "razorpay_order_id": razorpay_order['id'],
                    "razorpay_key": settings.RAZORPAY_KEY_ID,
                    "amount": razorpay_order_data['amount'],
                    "currency": razorpay_order_data['currency'],
                    "order_id": order.id
                }, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({'error': 'Payment Approved request time expire, please send payment request again!'}, status=status.HTTP_403_FORBIDDEN)


class VerifyPayment(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        razorpay_payment_id = request.data.get('razorpay_payment_id')
        razorpay_order_id = request.data.get('razorpay_order_id')
        razorpay_signature = request.data.get('razorpay_signature')

        # Verify the order exists
        order = get_object_or_404(Order, razorpay_order_id=razorpay_order_id)

        # Check stock availability before payment verification
        if not self.check_stock_availability(order):
            return Response({"error": "Insufficient stock for one or more items"}, status=status.HTTP_400_BAD_REQUEST)

        # Proceed to verify the payment signature
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }

        try:
            client.utility.verify_payment_signature(params_dict)

            # Mark the order as paid
            order.razorpay_payment_id = razorpay_payment_id
            order.is_paid = True
            order.created_by = self.request.user
            order.updated_by = self.request.user
            order.save()

            # Update stock and log history
            self.update_stock(order)
            
            OrderItemData = OrderItem.objects.filter(order=order)
            for OrderItemObj in OrderItemData:
                Selling.objects.create(order=order, product_variant=OrderItemObj.product_variant, quantity=OrderItemObj.quantity)

            return Response({"status": "Payment Successful"}, status=status.HTTP_200_OK)

        except razorpay.errors.SignatureVerificationError:
            return Response({"error": "Payment verification failed"}, status=status.HTTP_400_BAD_REQUEST)

    def check_stock_availability(self, order):
        """Check if stock is available for all order items."""
        order_items = OrderItem.objects.filter(order_id=order.id)

        for order_item in order_items:
            Variant = ProductVariant.objects.filter(product_variant=order_item.product_variant).first()
            if not Variant or Variant.quantity < order_item.quantity:
                # Insufficient stock for this order item
                return False
        # All stocks are available
        return True  

    def update_stock(self, request, order):
        """Update stock based on order items and log history."""
        order_items = OrderItem.objects.filter(order_id=order.id)

        for order_item in order_items:
            Variant = get_object_or_404(ProductVariant, product_variant=order_item.product_variant)

            # Decrease stock quantity
            Variant.quantity -= order_item.quantity
            Variant.created_by = self.request.user
            Variant.updated_by = self.request.user
            Variant.save()


class SellingListAPI(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, *args, **kwargs):
        # Get query parameters for filtering
        product_type = self.request.data.get('product_type', None)
        product_brand = self.request.data.get('product_brand', None)
        start_date = self.request.data.get('start_date', None)
        end_date = self.request.data.get('end_date', None)

        # Start building the queryset
        queryset = Selling.objects.all()

        # Filter by product type if provided
        if product_type:
            product_type_obj = ProductType.objects.filter(name=product_type).first()
            if product_type_obj:
                queryset = queryset.filter(product_variant__product__product_type=product_type_obj)

        # Filter by product brand if provided
        if product_brand:
            product_brand_obj = BrandType.objects.filter(name=product_brand).first()
            if product_brand_obj:
                queryset = queryset.filter(product_variant__product__product_brand=product_brand_obj)

        # Filter by date range if provided
        if start_date and end_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
                queryset = queryset.filter(created_at__range=[start_date_obj, end_date_obj])
            except ValueError:
                return Response({"error": "Invalid date format. Please use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        # Serialize the data
        serializer = SellingSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SellsVsStockAPI(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, *args, **kwargs):
        # Get query parameters for filtering
        start_date = request.data.get('start_date', None)
        end_date = request.data.get('end_date', None)
        
        # Validate date range
        if start_date and end_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                return Response({"error": "Invalid date format. Please use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "Both start_date and end_date are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Query Selling data within the date range and aggregate total quantity sold per product variant
        sold_data = Selling.objects.filter(created_at__range=[start_date_obj, end_date_obj]) \
            .values('product_variant') \
            .annotate(total_sold=Sum('quantity'))

        # Prepare final result by combining sold and stock data
        result = []
        for sold in sold_data:
            product_variant_id = sold['product_variant']
            total_sold = sold['total_sold']

            # Get the product variant object and stock quantity directly from the variant
            product_variant = ProductVariant.objects.get(id=product_variant_id)
            total_stock = product_variant.quantity  # Stock is stored directly in ProductVariant

            # Get product details (e.g., code, product type, product brand)
            product = product_variant.product
            result.append({
                'product_variant': product.code,
                'product_type': product.product_type.name,
                'product_brand': product.product_brand.name,
                'total_sold': total_sold,
                'total_stock': total_stock
            })

        return Response(result, status=status.HTTP_200_OK)

class InvoiceListView(generics.ListAPIView):
    """
    API to list all orders with invoice details.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = InvoiceListSerializer

    def get_queryset(self):
        # Filter orders for the authenticated user
        return Order.objects.filter(user=self.request.user)

class OrderPaymentListView(generics.ListAPIView):
    """API to get order payments with optional date range filter."""
    serializer_class = OrderPaymentSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        # Get the queryset from Order model
        queryset = Order.objects.all()

        # Filter by date range (start_date and end_date)
        start_date = self.request.data.get('start_date', None)
        end_date = self.request.data.get('end_date', None)

        if start_date:
            try:
                start_date = parse_datetime(start_date)  # Assuming date in ISO format
                queryset = queryset.filter(created_at__gte=start_date)
            except ValueError:
                return Response({"error": "Invalid start date format"}, status=status.HTTP_400_BAD_REQUEST)

        if end_date:
            try:
                end_date = parse_datetime(end_date)
                queryset = queryset.filter(created_at__lte=end_date)
            except ValueError:
                return Response({"error": "Invalid end date format"}, status=status.HTTP_400_BAD_REQUEST)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DownloadInvoiceView(APIView):
    """
    API to download the invoice for a specific order.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        order_id = kwargs.get('pk')
        order = get_object_or_404(Order, id=order_id, user=request.user)

        # Generate the invoice as a PDF
        pdf_buffer = order.generate_invoice()

        # Create a FileResponse for the PDF
        response = FileResponse(pdf_buffer, as_attachment=True, filename=f"invoice_{order.order_number}.pdf")
        return response
