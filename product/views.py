from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import ProductType, BrandType, ProductStyle, Product, ProductVariant, Wishlist, ShoppingCart, CartItems, SharableCollection
from .serializers import ProductTypeSerializer, BrandTypeSerializer, ProductStyleSerializer, ProductSerializer,  ProductVariantSerializer, WishlistSerializer, CartSerializer, SharableCollectionSerializer
from backend.utils import superuser_required
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.conf import settings

# ProductType CRUD API View
class ProductTypeAPIView(APIView):

    def get(self, request, pk=None):
        if pk:
            try:
                product_type = ProductType.objects.get(pk=pk)
                serializer = ProductTypeSerializer(product_type, context={'request': request})
                return Response(serializer.data, status=status.HTTP_200_OK)
            except ProductType.DoesNotExist:
                return Response({"error": "ProductType not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            product_types = ProductType.objects.all()
            serializer = ProductTypeSerializer(product_types, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    @superuser_required
    def post(self, request):
        serializer = ProductTypeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                created_by=self.request.user,
                updated_by=self.request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @superuser_required
    def put(self, request, pk=None):
        try:
            product_type = ProductType.objects.get(pk=pk)
        except ProductType.DoesNotExist:
            return Response({"error": "ProductType not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProductTypeSerializer(product_type, data=request.data)
        if serializer.is_valid():
            serializer.save(
                updated_by=self.request.user
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @superuser_required
    def delete(self, request, pk=None):
        try:
            product_type = ProductType.objects.get(pk=pk)
        except ProductType.DoesNotExist:
            return Response({"error": "ProductType not found"}, status=status.HTTP_404_NOT_FOUND)

        product_type.delete()
        return Response({"message": "ProductType delete successfully."}, status=status.HTTP_204_NO_CONTENT)


class BrandTypeAPIView(APIView):

    def get(self, request, pk=None):
        if pk:
            try:
                brand_type = BrandType.objects.get(pk=pk)
                serializer = BrandTypeSerializer(brand_type)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except BrandType.DoesNotExist:
                return Response({"error": "BrandType not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            brand_types = BrandType.objects.all()
            serializer = BrandTypeSerializer(brand_types, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
    @superuser_required
    def post(self, request):
        serializer = BrandTypeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                created_by=self.request.user,
                updated_by=self.request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @superuser_required
    def put(self, request, pk=None):
        try:
            brand_type = BrandType.objects.get(pk=pk)
        except BrandType.DoesNotExist:
            return Response({"error": "BrandType not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = BrandTypeSerializer(brand_type, data=request.data)
        if serializer.is_valid():
            serializer.save(
                updated_by=self.request.user
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @superuser_required
    def delete(self, request, pk=None):
        try:
            brand_type = BrandType.objects.get(pk=pk)
        except BrandType.DoesNotExist:
            return Response({"error": "BrandType not found"}, status=status.HTTP_404_NOT_FOUND)

        brand_type.delete()
        return Response({"message": "Product Brand delete successfully."}, status=status.HTTP_204_NO_CONTENT)


class ProductStyleAPIView(APIView):

    def get(self, request, pk=None):
        if pk:
            try:
                product_style = ProductStyle.objects.get(pk=pk)
                serializer = ProductStyleSerializer(product_style)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except ProductStyle.DoesNotExist:
                return Response({"error": "Product Style not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            product_styles = ProductStyle.objects.all()
            
            # Pagination setup
            paginator = PageNumberPagination()
            paginator.page_size = settings.PAGE_LIMIT
            
            # Paginate the queryset
            paginated_product_styles = paginator.paginate_queryset(product_styles, request)
            
            # Serialize the paginated queryset
            serializer = ProductStyleSerializer(paginated_product_styles, many=True)
            
            # Return paginated response
            return paginator.get_paginated_response(serializer.data)
        
    @superuser_required
    def post(self, request):
        serializer = ProductStyleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                created_by=self.request.user,
                updated_by=self.request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @superuser_required
    def put(self, request, pk=None):
        try:
            product_style = ProductStyle.objects.get(pk=pk)
        except ProductStyle.DoesNotExist:
            return Response({"error": "Product Style not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProductStyleSerializer(product_style, data=request.data)
        if serializer.is_valid():
            serializer.save(
                updated_by=self.request.user
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @superuser_required
    def delete(self, request, pk=None):
        try:
            product_style = ProductStyle.objects.get(pk=pk)
        except ProductStyle.DoesNotExist:
            return Response({"error": "Product Style not found"}, status=status.HTTP_404_NOT_FOUND)

        product_style.delete()
        return Response({"message": "Product style delete successfully."}, status=status.HTTP_204_NO_CONTENT)


class ProductAPIView(APIView):
    """
    APIView for CRUD operations on Product.
    """

    def get(self, request, pk=None, *args, **kwargs):
        product_type = self.request.data.get('product_type', None)
        if pk:
            try:
                product = Product.objects.get(pk=pk)
                serializer = ProductSerializer(product)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Product.DoesNotExist:
                return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        products = Product.objects.filter(product_type_id=product_type) if product_type else Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @superuser_required
    def post(self, request, *args, **kwargs):
        serializer = ProductSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(
                created_by = self.request.user,
                updated_by = self.request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @superuser_required
    def put(self, request, pk=None, *args, **kwargs):
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ProductSerializer(product, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(
                updated_by = self.request.user
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @superuser_required
    def patch(self, request, pk, *args, **kwargs):
        try:
            # Retrieve the product instance
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        # Pass partial=True to the serializer to allow partial updates
        serializer = ProductSerializer(product, data=request.data, partial=True, context={'request': request})

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @superuser_required
    def delete(self, request, pk=None, *args, **kwargs):
        try:
            product = Product.objects.get(pk=pk)
            product.delete()
            return Response({"message": "Product deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Product.DoesNotExist:
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)


class ProductVariantAPIView(APIView):
    """
    APIView for CRUD operations on ProductVariant.
    """

    def get(self, request, pk=None, *args, **kwargs):
        product_id = request.query_params.get('product_id')

        if pk:
            try:
                product_variant = ProductVariant.objects.get(pk=pk)
                serializer = ProductVariantSerializer(product_variant)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except ProductVariant.DoesNotExist:
                return Response({"error": "Product Variant not found."}, status=status.HTTP_404_NOT_FOUND)

        if product_id:
            try:
                product_variants = ProductVariant.objects.filter(product_id=product_id)
                if product_variants.exists():
                    serializer = ProductVariantSerializer(product_variants, many=True)
                    return Response(serializer.data, status=status.HTTP_200_OK)
                else:
                    return Response({"error": "No Product Variants found for this product."}, status=status.HTTP_404_NOT_FOUND)
            except ProductVariant.DoesNotExist:
                return Response({"error": "Product Variant not found."}, status=status.HTTP_404_NOT_FOUND)

        product_variants = ProductVariant.objects.all()
        serializer = ProductVariantSerializer(product_variants, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @superuser_required
    def post(self, request, *args, **kwargs):
        serializer = ProductVariantSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                created_by = self.request.user,
                updated_by = self.request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @superuser_required
    def put(self, request, pk=None, *args, **kwargs):
        try:
            product_variant = ProductVariant.objects.get(pk=pk)
        except ProductVariant.DoesNotExist:
            return Response({"error": "Product Variant not found."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ProductVariantSerializer(product_variant, data=request.data)
        if serializer.is_valid():
            serializer.save(
                updated_by = self.request.user
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @superuser_required
    def delete(self, request, pk=None, *args, **kwargs):
        try:
            product_variant = ProductVariant.objects.get(pk=pk)
            product_variant.delete()
            return Response({"message": "Product Variant deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except ProductVariant.DoesNotExist:
            return Response({"error": "Product Variant not found."}, status=status.HTTP_404_NOT_FOUND)


class WishlistView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        wishlist_items = Wishlist.objects.filter(user=request.user)
        serializer = WishlistSerializer(wishlist_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        product_id = request.data.get("product_id")
        product = Product.objects.filter(id=product_id, status=Product.ACTIVE).exists()
        if product:
            wishlist_item, created = Wishlist.objects.get_or_create(user=self.request.user, product_id=product_id)

            if created:
                return Response({"message": "Product added to wishlist."}, status=status.HTTP_201_CREATED)
            return Response({"message": "Product already in wishlist"}, status=status.HTTP_200_OK)
        return Response({"message": "Something Went Wrong!"}, status=status.HTTP_200_OK)

    def delete(self, request, id):
        wishlist_item = Wishlist.objects.filter(id=id, user=self.request.user).first()
        if wishlist_item:
            wishlist_item.delete()
            return Response({"message": "Product removed from wishlist"}, status=status.HTTP_200_OK)
        return Response({"message": "Product not in wishlist"}, status=status.HTTP_404_NOT_FOUND)


class CartAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get the cart items for the logged-in user."""
        user_cart =  ShoppingCart.objects.filter(user=self.request.user).first()
        cart_items = CartItems.objects.filter(cart_id=user_cart.id)
        serializer = CartSerializer(cart_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Add a product to the user's cart."""
        product_variant_id = request.data.get("product_variant_id")
        quantity = request.data.get("quantity", 1)

        # Validate product_variant belongs to product_color
        product_variant = get_object_or_404(ProductVariant, id=product_variant_id, is_stock=True, product__status=Product.ACTIVE)

        shoping_cart = ShoppingCart.objects.filter(user=self.request.user).first()
        if not shoping_cart:
            shoping_cart = ShoppingCart.objects.create(user=self.request.user)

        # Check if the product is already in the cart
        cart_item, created = CartItems.objects.get_or_create(
            cart=shoping_cart,
            product_variant=product_variant,
            defaults={'quantity': int(quantity)}
        )

        if not created:
            # Update the quantity if the product already exists in the cart
            cart_item.quantity += int(quantity)
            cart_item.save()

        serializer = CartSerializer(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request, cart_item_id):
        """Increment or decrement the quantity of a product in the cart."""
        user_cart = get_object_or_404(ShoppingCart, user=self.request.user)
        cart_item = get_object_or_404(CartItems, id=cart_item_id, cart_id=user_cart.id)
        action = request.data.get("action", None)

        if action == "increment":
            # Increase the quantity by 1
            cart_item.quantity += 1
            cart_item.save()
            serializer = CartSerializer(cart_item)
            return Response(serializer.data, status=status.HTTP_200_OK)

        elif action == "decrement": 
            # Decrease the quantity by 1
            cart_item.quantity -= 1

            # If quantity is now 0, delete the item from the cart
            if cart_item.quantity <= 0:
                cart_item.delete()
                return Response({"detail": "Item removed from cart"}, status=status.HTTP_204_NO_CONTENT)

            cart_item.save()
            serializer = CartSerializer(cart_item)
            return Response(serializer.data, status=status.HTTP_200_OK)

        else:
            return Response({"detail": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, cart_item_id):
        """Remove an item from the user's cart."""
        user_cart = get_object_or_404(ShoppingCart, user=self.request.user)
        cart_item = get_object_or_404(CartItems, id=cart_item_id, cart_id=user_cart.id)
        cart_item.delete()

        return Response({"detail": "Item removed from cart"}, status=status.HTTP_204_NO_CONTENT)


class SharableCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):    
        """
        Retrieve a list of sharable collections or a specific collection by its ID.
        """
        pk = request.data.get("collection_id", None)
        if pk:
            try:
                sharable_collection = SharableCollection.objects.get(pk=pk)
                serializer = SharableCollectionSerializer(sharable_collection, context={'request': request})
                return Response(serializer.data, status=status.HTTP_200_OK)
            except SharableCollection.DoesNotExist:
                return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Get all collections and pass request context to the serializer
        collections = SharableCollection.objects.all()
        serializer = SharableCollectionSerializer(collections, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = SharableCollectionSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            sharable_collection = serializer.save(
                created_by=self.request.user,
                updated_by=self.request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """
        Delete an existing sharable collection.
        """
        try:
            sharable_collection = SharableCollection.objects.get(pk=pk)
            sharable_collection.delete()
            return Response({"message": "Sharable link deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except SharableCollection.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)


class SharableCollectionDetailView(APIView):
    def get(self, request, slug):
        sharable_collection = get_object_or_404(SharableCollection, slug=slug)

        if sharable_collection.valid_time() and sharable_collection.is_validate:
        
            # Split the string into a list and convert to integers
            product_ids = [int(pid) for pid in sharable_collection.product_variant_ids.split(",")]
            
            # Filter products based on the list of product IDs
            products = ProductVariant.objects.filter(id__in=product_ids)
            
            # Serialize the products
            product_data = ProductVariantSerializer(products, many=True).data
            
            return Response({
                'products': product_data
            }, status=status.HTTP_200_OK)
        return Response({'error': 'link is expired'}, status=status.HTTP_403_FORBIDDEN)


class ProductImageListAPIView(APIView):
    """
    API to list all products with their main images.
    """
    def get(self, request):
        products = Product.objects.filter(status=Product.ACTIVE)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductVariantImageListAPIView(APIView):
    """
    API to get all variant images for a specific product.
    """
    def get(self, request, product_id):
        product = Product.objects.filter(id=product_id, status=Product.ACTIVE).first()
        if not product:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        variants = ProductVariant.objects.filter(product=product)
        serializer = ProductVariantSerializer(variants, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)