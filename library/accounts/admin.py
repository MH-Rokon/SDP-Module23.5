from django.contrib import admin
from .models import UserAddress,Category,Book,UserBookAccount 

admin.site.register(UserAddress)
admin.site.register(Category)
admin.site.register(Book)
admin.site.register(UserBookAccount)