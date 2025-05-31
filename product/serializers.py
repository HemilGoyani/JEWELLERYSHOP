from rest_framework import serializers
from .models import ProductType, BrandType, ProductStyle, Product, ProductVariant, Wishlist, CartItems, SharableCollection
import uuid
from django.urls import reverse

class UniqueNameValidationMixin:
    def validate_name(self, value):
        model_class = self.Meta.model
        if self.instance:
            # For update: exclude the current instance
            if model_class.objects.filter(name=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError(f"A {model_class.__name__} with this name already exists.")
        else:
            # For create: check if name already exists
            if model_class.objects.filter(name=value).exists():
                raise serializers.ValidationError(f"A {model_class.__name__} with this name already exists.")
        return value


class ProductTypeSerializer(serializers.ModelSerializer, UniqueNameValidationMixin):
    class Meta:
        model = ProductType
        fields = '__all__'

    
class BrandTypeSerializer(serializers.ModelSerializer, UniqueNameValidationMixin):
    class Meta:
        model = BrandType
        fields = '__all__'


class ProductStyleSerializer(serializers.ModelSerializer, UniqueNameValidationMixin):
    class Meta:
        model = ProductStyle
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    product_type = serializers.CharField(write_only=True)
    product_brand = serializers.CharField(write_only=True)
    product_style = serializers.CharField(write_only=True)

    product_type_detail = ProductTypeSerializer(source='product_type', read_only=True)
    product_brand_detail = BrandTypeSerializer(source='product_brand', read_only=True)
    product_style_detail = ProductStyleSerializer(source='product_style', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'product_category', 'code', 'product_type', 'product_type_detail',
            'product_brand', 'product_brand_detail', 'product_style', 'product_style_detail', 'stones', 'status', 'image',
            'created_by', 'updated_by'
        ]

    def create(self, validated_data):
        # Get the current user from the request context
        user = self.context.get('request').user

        # Set created_by and updated_by fields to the current user
        validated_data['created_by'] = user
        validated_data['updated_by'] = user

        # Get or create the related ProductType, BrandType, and ProductStyle
        product_type_name = validated_data.pop('product_type')
        product_brand_name = validated_data.pop('product_brand')
        product_style_name = validated_data.pop('product_style')

        # Create or get the related models with proper user fields
        product_type, created = ProductType.objects.get_or_create(name=product_type_name)
        if created:  # If newly created, set both created_by and updated_by
            product_type.created_by = user
        product_type.updated_by = user
        product_type.save()

        product_brand, created = BrandType.objects.get_or_create(name=product_brand_name)
        if created:  # If newly created, set both created_by and updated_by
            product_brand.created_by = user
        product_brand.updated_by = user
        product_brand.save()

        product_style, created = ProductStyle.objects.get_or_create(name=product_style_name)
        if created:  # If newly created, set both created_by and updated_by
            product_style.created_by = user
        product_style.updated_by = user
        product_style.save()

        # Create the Product instance with the correct related model instances
        product = Product.objects.create(
            product_type=product_type,
            product_brand=product_brand,
            product_style=product_style,
            **validated_data
        )

        return product

    def update(self, instance, validated_data):
        # Get the current user from the request context
        user = self.context.get('request').user
        validated_data['updated_by'] = user  # Update the updated_by field

        # Ensure that related fields are properly handled during update
        if 'product_type' in validated_data:
            product_type_name = validated_data.pop('product_type')
            product_type, created = ProductType.objects.get_or_create(name=product_type_name)
            if created:  # If newly created, set both created_by and updated_by
                product_type.created_by = user
            product_type.updated_by = user
            product_type.save()
            instance.product_type = product_type

        if 'product_brand' in validated_data:
            product_brand_name = validated_data.pop('product_brand')
            product_brand, created = BrandType.objects.get_or_create(name=product_brand_name)
            if created:  # If newly created, set both created_by and updated_by
                product_brand.created_by = user
            product_brand.updated_by = user
            product_brand.save()
            instance.product_brand = product_brand

        if 'product_style' in validated_data:
            product_style_name = validated_data.pop('product_style')
            product_style, created = ProductStyle.objects.get_or_create(name=product_style_name)
            if created:  # If newly created, set both created_by and updated_by
                product_style.created_by = user
            product_style.updated_by = user
            product_style.save()
            instance.product_style = product_style

        # Call the parent class's update method to handle the rest of the fields
        return super().update(instance, validated_data)



class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = '__all__'

    def validate(self, attrs):
        # Get the product and color from the incoming data
        product = attrs.get('product')
        color = attrs.get('color')
        carat = attrs.get('carat')

        # Check if a ProductVariant with the same product, color, and carat already exists
        if ProductVariant.objects.filter(product=product, color=color, carat=carat).exists():
            raise serializers.ValidationError("A ProductVariant with this color and carat already exists for this product.")

        return attrs   

class WishlistSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), write_only=True)
    product_details = ProductSerializer(source='product', read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'user', 'product', 'product_details']
        read_only_fileds = ['id', 'user']

class CartSerializer(serializers.ModelSerializer):
    product_variant = ProductVariantSerializer()

    class Meta:
        model = CartItems
        fields = ['id', 'cart', 'product_variant', 'quantity']


class SharableCollectionSerializer(serializers.ModelSerializer):
    sharable_url = serializers.SerializerMethodField()

    class Meta:
        model = SharableCollection
        fields = ['id', 'slug', 'product_variant_ids', 'time_duration', 'is_validate', 'created_at', 'updated_at', 'sharable_url']
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['slug'] = str(uuid.uuid4())
        return super().create(validated_data)

    def get_sharable_url(self, obj):
        request = self.context.get('request')
        if request is None:
            return None  # or handle the error as needed
        return request.build_absolute_uri(reverse('sharable_collection_detail', kwargs={'slug': obj.slug}))