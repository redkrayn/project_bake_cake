from django.contrib import admin
from data.models import User, Cake, Order, Delivery
from django.utils.html import format_html


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'telegram_id',
        'username',
        'phone',
        'privacy_agreement_accepted',
        'registration_date'
        )
    search_fields = ('telegram_id', 'username', 'phone')
    list_filter = ('privacy_agreement_accepted', 'registration_date',)
    readonly_fields = ('registration_date',)


@admin.register(Cake)
class CakeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'levels',
        'form',
        'topping',
        'berries',
        'decor',
        'total_price',
        'status',
        'delivery_date',
        'is_urgent',
        'photo'
    )

    def display_photo(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" width="50" height="50" />',
                obj.photo.url
                )
        return "Нет фото"

    display_photo.short_description = "Фото торта"

    list_filter = (
        'status',
        'levels',
        'form',
        'topping',
        'berries',
        'decor',
        'is_urgent'
    )

    search_fields = (
        'user__telegram_id',
        'user__username',
        'text',
        'comment'
    )

    readonly_fields = (
        'created_at',
        'total_price'
    )

    fieldsets = (
        ('Основная информация', {
            'fields': (
                'user',
                'levels',
                'form',
                'topping',
                'berries',
                'decor',
                'text',
                'comment',
                'photo'
                'comment'

            )
        }),
        ('Доставка', {
            'fields': (
                'delivery_date',
                'is_urgent'
            )
        }),
        ('Статус и цена', {
            'fields': (
                'status',
                'total_price'
            )
        }),
        ('Дополнительно', {
            'fields': (
                'created_at',
            )
        }),
    )

    def save_model(self, request, obj, form, change):
        obj.total_price = obj.calculate_price()
        super().save_model(request, obj, form, change)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__telegram_id',)
    readonly_fields = ('created_at', 'updated_at', 'total_amount')
    filter_horizontal = ('cakes',)


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('id',
                    'order',
                    'address',
                    'delivery_date',
                    'delivery_time',
                    'status')
    list_filter = ('status', 'delivery_date')
    search_fields = ('order__id', 'address')
    readonly_fields = ('created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
