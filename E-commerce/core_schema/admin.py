
from django.contrib import admin
from .models import (
	Permission, CustomGroup, Roles, Category, Images, Product, ProductOptions, Cart, Order, OrderItems, Review
)

admin.site.register(Permission)
admin.site.register(CustomGroup)
admin.site.register(Roles)
admin.site.register(Category)
admin.site.register(Images)
admin.site.register(Product)
admin.site.register(ProductOptions)
admin.site.register(Cart)
admin.site.register(Order)
admin.site.register(OrderItems)
admin.site.register(Review)
