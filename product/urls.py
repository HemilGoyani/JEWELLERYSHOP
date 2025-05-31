from django.urls import path
from .views import ProductTypeAPIView, BrandTypeAPIView, ProductStyleAPIView, ProductAPIView, ProductVariantAPIView, WishlistView, CartAPIView, SharableCollectionAPIView, SharableCollectionDetailView, ProductImageListAPIView, ProductVariantImageListAPIView

urlpatterns = [
    # Product Type API
    path('product-types/', ProductTypeAPIView.as_view(), name='product_type_list_create'),
    path('product-types/<int:pk>/', ProductTypeAPIView.as_view(), name='product_type_detail'),

    # Product Brand API
    path('brand-types/', BrandTypeAPIView.as_view(), name='brand_type_list_create'),
    path('brand-types/<int:pk>/', BrandTypeAPIView.as_view(), name='brand_type_detail'),

    # Product Style API
    path('product-styles/', ProductStyleAPIView.as_view(), name='product_style_list_create'),
    path('product-styles/<int:pk>/', ProductStyleAPIView.as_view(), name='product_style_detail'),

    # Product API
    path('', ProductAPIView.as_view(), name='product_list'),
    path('<int:pk>/', ProductAPIView.as_view(), name='product_detail'),
    
    # Product Variant API
    path('product-variant/', ProductVariantAPIView.as_view(), name='product_variant_list'),
    path('product-variant/<int:pk>/', ProductVariantAPIView.as_view(), name='product_variant_detail'),

    # Product Wish List
    path('wishlist/', WishlistView.as_view(), name='wishlist'),
    path('wishlist/<int:id>/', WishlistView.as_view(), name='remove_from_wishlist'),

    # User Cart API
    path('cart/', CartAPIView.as_view(), name='cart-list'),
    path('cart/<int:cart_item_id>/', CartAPIView.as_view(), name='cart_item_detail'),

    # Premium Product sharable API
    path('premium/sharable-collections/', SharableCollectionAPIView.as_view(), name='premium_product_link'),
    path('premium/sharable-collections/<int:pk>/', SharableCollectionAPIView.as_view(), name='delete_premium_link'),
    path('premium/<slug:slug>/', SharableCollectionDetailView.as_view(), name='sharable_collection_detail'),

    # Get gallery image API
    path('images/', ProductImageListAPIView.as_view(), name='product-image-list'),
    path('variants/<int:product_id>/images/', ProductVariantImageListAPIView.as_view(), name='product-variant-image-list'),
]