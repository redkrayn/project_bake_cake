from django.contrib import admin
from data.models import User, Cake, Order, Delivery, ReadyCake, PromoCode, LinkTracker


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


@admin.register(ReadyCake)
class ReadyCakeAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_available')
    list_filter = ('is_available',)
    search_fields = ('name', 'description', 'ingredients')
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'ingredients', 'price', 'image', 'is_available')
        }),
    )


@admin.register(PromoCode)  # Регистрируем модель PromoCode с помощью декоратора
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount', 'valid_from', 'valid_to', 'is_valid')  # Поля для отображения в списке
    readonly_fields = ('is_valid',)  # Поля только для чтения

    def is_valid(self, obj):
        """Отображает статус действительности промокода."""
        return obj.is_valid()

    is_valid.boolean = True  # Отображать как иконку (опционально)
    is_valid.short_description = 'Действителен'  # Кастомный заголовок колонки (опционально)


@admin.register(LinkTracker)
class LinkTrackerAdmin(admin.ModelAdmin):
    list_display = ('link', 'click_count')
    search_fields = ('link',)
