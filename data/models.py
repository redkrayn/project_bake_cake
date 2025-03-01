from django.db import models
from django.utils import timezone
from django.db.models import Sum


class User(models.Model):
    """
    Модель для хранения информации о пользователях.
    """
    telegram_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=32, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    registration_date = models.DateTimeField(auto_now_add=True)
    privacy_agreement = models.FileField(
        upload_to='privacy_agreements/', null=True, blank=True
        )
    privacy_agreement_accepted = models.BooleanField(default=False)

    def __str__(self):
        return f"User {self.telegram_id} ({self.username})"


class Cake(models.Model):
    """
    Модель для хранения информации о тортах.
    """
    LEVEL_CHOICES = [
        (1, '1 уровень (+400р)'),
        (2, '2 уровня (+750р)'),
        (3, '3 уровня (+1100р)'),
    ]
    FORM_CHOICES = [
        ('circle', 'Круг (+400р)'),
        ('square', 'Квадрат (+600р)'),
        ('rectangle', 'Прямоугольник (+1000р)'),
    ]
    TOPPING_CHOICES = [
        ('none', 'Без топпинга'),
        ('white', 'Белый соус (+200р)'),
        ('caramel', 'Карамельный сироп (+180р)'),
        ('maple', 'Кленовый сироп (+200р)'),
        ('strawberry', 'Клубничный сироп (+300р)'),
        ('blueberry', 'Черничный сироп (+350р)'),
        ('chocolate', 'Молочный шоколад (+200р)'),
    ]
    BERRIES_CHOICES = [
        ('none', 'Без ягод'),
        ('blackberry', 'Ежевика (+400р)'),
        ('raspberry', 'Малина (+300р)'),
        ('blueberry', 'Голубика (+450р)'),
        ('strawberry', 'Клубника (+500р)'),
    ]
    DECOR_CHOICES = [
        ('none', 'Без декора'),
        ('pistachio', 'Фисташки (+300р)'),
        ('meringue', 'Безе (+400р)'),
        ('hazelnut', 'Фундук (+350р)'),
        ('pecan', 'Пекан (+300р)'),
        ('marshmallow', 'Маршмеллоу (+200р)'),
        ('marzipan', 'Марципан (+280р)'),
    ]

    user = models.ForeignKey('User', on_delete=models.CASCADE)
    levels = models.IntegerField(choices=LEVEL_CHOICES)
    form = models.CharField(max_length=20, choices=FORM_CHOICES)
    topping = models.CharField(max_length=20, choices=TOPPING_CHOICES)
    berries = models.CharField(max_length=20,
                               choices=BERRIES_CHOICES,
                               default='none')
    decor = models.CharField(max_length=20,
                             choices=DECOR_CHOICES,
                             default='none')
    photo = models.ImageField(
        upload_to='cakes/',
        blank=True,
        null=True,
        verbose_name="Фото торта"
    )
    text = models.TextField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    delivery_date = models.DateTimeField(default=timezone.now)
    is_urgent = models.BooleanField(default=False)
    total_price = models.DecimalField(max_digits=10,
                                      decimal_places=2,
                                      default=0)
    status = models.CharField(max_length=20, default='new')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cake {self.id} for {self.user.telegram_id}"

    def calculate_price(self):
        """
        Рассчитывает стоимость торта на основе выбранных параметров.
        """
        price = {1: 400, 2: 750, 3: 1100}[self.levels]

        price += {'circle': 400, 'square': 600, 'rectangle': 1000}[self.form]

        topping_prices = {
            'none': 0,
            'white': 200,
            'caramel': 180,
            'maple': 200,
            'strawberry': 300,
            'blueberry': 350,
            'chocolate': 200,
        }
        price += topping_prices[self.topping]

        berries_prices = {
            'none': 0,
            'blackberry': 400,
            'raspberry': 300,
            'blueberry': 450,
            'strawberry': 500,
        }
        price += berries_prices[self.berries]

        decor_prices = {
            'none': 0,
            'pistachio': 300,
            'meringue': 400,
            'hazelnut': 350,
            'pecan': 300,
            'marshmallow': 200,
            'marzipan': 280,
        }
        price += decor_prices[self.decor]

        if self.text:
            price += 500

        if self.is_urgent:
            price *= 1.2

        return price

    def save(self, *args, **kwargs):
        """
        Автоматически рассчитывает стоимость торта перед сохранением.
        """
        self.total_price = self.calculate_price()
        super().save(*args, **kwargs)


class Order(models.Model):
    """
    Модель для хранения информации о заказах.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cakes = models.ManyToManyField(Cake)
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} by {self.user.telegram_id}"

    def calculate_total_amount(self):
        """
        Рассчитывает общую сумму заказа на основе стоимости всех тортов.
        """
        if self.pk:  # Проверяем, что объект уже сохранен в базе данных
            total = self.cakes.aggregate(
                total=Sum('total_price')
                )['total'] or 0
            return round(total, 2)
        return 0  # Если объект еще не сохранен, возвращаем 0

    def update_total_amount(self):
        """
        Обновляет общую сумму заказа и сохраняет изменения.
        """
        self.total_amount = self.calculate_total_amount()
        self.save(update_fields=['total_amount'])

    def save(self, *args, **kwargs):
        """
        Автоматически рассчитывает общую сумму заказа перед сохранением.
        """
        if not self.pk:  # Если объект новый, сначала сохраняем его
            super().save(*args, **kwargs)
        self.total_amount = self.calculate_total_amount()
        super().save(*args, **kwargs)


class Delivery(models.Model):
    """
    Модель для хранения информации о доставке.
    """
    DELIVERY_STATUS_CHOICES = [
        ('processing', 'Ожидает обработки'),
        ('in_progress', 'В процессе доставки'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
    ]

    order = models.OneToOneField(Order,
                                 on_delete=models.CASCADE,
                                 related_name='delivery'
                                 )
    address = models.TextField(verbose_name="Адрес доставки")
    delivery_date = models.DateField(verbose_name="Дата доставки")
    delivery_time = models.TimeField(verbose_name="Время доставки")
    status = models.CharField(
        max_length=20,
        choices=DELIVERY_STATUS_CHOICES,
        default='processing',
        verbose_name="Статус доставки"
        )
    comment = models.TextField(
        blank=True,
        null=True,
        verbose_name="Комментарий к доставке"
        )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
        )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
        )

    def __str__(self):
        return f"Доставка для заказа #{self.order.id} ({self.status})"
