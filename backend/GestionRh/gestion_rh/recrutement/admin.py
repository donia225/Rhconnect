from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Candidat

# ✅ Custom User Admin (without mandatory Groups & Permissions)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")
    
    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        ("Roles", {"fields": ("role",)}),  # ✅ Role selection
        ("Permissions", {"fields": ("is_staff", "is_active")}),
    )  # ✅ Removed 'groups' & 'user_permissions' from fieldsets

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "password1", "password2", "role", "is_staff", "is_active"),
        }),
    )  # ✅ Allow adding users without groups

    search_fields = ("username", "email")
    ordering = ("username",)

# ✅ Register User Model in Django Admin
admin.site.register(User, CustomUserAdmin)
admin.site.register(Candidat)
