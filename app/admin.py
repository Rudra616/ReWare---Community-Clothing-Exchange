from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils import timezone

from .models import CustomUser, Item, Swap, AdminReview, State, District

# ------------------------
# CustomUser Admin
# ------------------------

class ItemInline(admin.TabularInline):
    model = Item
    extra = 0
    readonly_fields = ('title', 'category', 'condition', 'approved', 'created_at')
    can_delete = False
    show_change_link = True

class SwapInline(admin.TabularInline):
    model = Swap
    extra = 0
    readonly_fields = ('item', 'status', 'points_used', 'requested_at')
    can_delete = False
    show_change_link = True

class CustomUserAdmin(UserAdmin):
    model = CustomUser

    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'points', 'profile_preview')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')

    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('points', 'bio', 'profile_image')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('points', 'bio', 'profile_image')}),
    )

    inlines = [ItemInline, SwapInline]  # 🆕 Show related Items & Swaps

    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

    def profile_preview(self, obj):
        if obj.profile_image:
            return format_html('<img src="{}" width="40" height="40" style="border-radius:50%;"/>', obj.profile_image.url)
        return "-"
    profile_preview.short_description = 'Profile'


# ------------------------
# Item Admin
# ------------------------

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'category', 'condition', 'approved', 'created_at', 'item_thumbnail')
    list_filter = ('approved', 'category', 'condition')
    search_fields = ('title', 'owner__username')
    date_hierarchy = 'created_at'
    actions = ['approve_items', 'reject_items']

    def item_thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "-"
    item_thumbnail.short_description = 'Image'

    def approve_items(self, request, queryset):
        updated = queryset.update(approved=True)
        for item in queryset:
            AdminReview.objects.create(
                admin=request.user,
                item=item,
                action='Approved',
                reason='Approved via bulk action',
                timestamp=timezone.now()
            )
        self.message_user(request, f"{updated} item(s) successfully approved.")

    approve_items.short_description = "Approve selected items"

    def reject_items(self, request, queryset):
        updated = queryset.update(approved=False)
        for item in queryset:
            AdminReview.objects.create(
                admin=request.user,
                item=item,
                action='Rejected',
                reason='Rejected via bulk action',
                timestamp=timezone.now()
            )
        self.message_user(request, f"{updated} item(s) successfully rejected.")

    reject_items.short_description = "Reject selected items"


# ------------------------
# Swap Admin
# ------------------------

@admin.register(Swap)
class SwapAdmin(admin.ModelAdmin):
    list_display = ('item', 'user', 'status', 'points_used', 'requested_at', 'updated_at')
    list_filter = ('status',)
    search_fields = ('item__title', 'user__username')
    readonly_fields = ('requested_at', 'updated_at')


# ------------------------
# AdminReview Admin
# ------------------------

@admin.register(AdminReview)
class AdminReviewAdmin(admin.ModelAdmin):
    list_display = ('admin', 'item', 'action', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('admin__username', 'item__title')
    readonly_fields = ('timestamp',)


# ------------------------
# State & District Admin
# ------------------------

@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'state')
    search_fields = ('name',)
    list_filter = ('state',)


# ------------------------
# Register CustomUser
# ------------------------

admin.site.register(CustomUser, CustomUserAdmin)
