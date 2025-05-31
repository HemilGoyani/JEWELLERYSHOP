from django_admin_listfilter_dropdown.filters import ChoiceDropdownFilter
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter

from django.contrib import admin
from .models import Product, ProductType, BrandType, ProductStyle

class ProductTypeAdmin(admin.ModelAdmin):
    model = ProductType
    list_display = ('id', 'name', 'created_at', 'created_by', 'updated_at', 'updated_by')
    list_filter = ('name',)
    search_fields = ('name',)
    ordering = ('-id',)
    list_per_page = 10

admin.site.register(ProductType, ProductTypeAdmin)

class BrandTypeAdmin(admin.ModelAdmin):
    model = BrandType
    list_display = ('id', 'name', 'created_at', 'created_by', 'updated_at', 'updated_by')
    list_filter = ('name',)
    search_fields = ('name',)
    ordering = ('-id',)
    list_per_page = 10

admin.site.register(BrandType, BrandTypeAdmin)

class ProductStyleAdmin(admin.ModelAdmin):
    model = ProductStyle
    list_display = ('id', 'name', 'created_at', 'created_by', 'updated_at', 'updated_by')
    list_filter = ('name',)
    search_fields = ('name',)
    ordering = ('-id',)
    list_per_page = 10

admin.site.register(ProductStyle, ProductStyleAdmin)