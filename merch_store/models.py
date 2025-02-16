from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True, verbose_name="Email")
    first_name = models.CharField(max_length=50, verbose_name="Имя")
    coins = models.IntegerField(default=1000, verbose_name='Монеты')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.email}: {self.coins}"

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Merch(models.Model):
    name = models.CharField(max_length=15, verbose_name='Name')
    price = models.IntegerField(verbose_name='Price')

    def __str__(self):
        return f'{self.name}: {self.price}'

    class Meta:
        verbose_name = 'Мерч'
        verbose_name_plural = 'Мерчи'


class Inventory(models.Model):
    """Инвентарь пользователя"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="inventory")
    merch = models.ForeignKey(Merch, on_delete=models.CASCADE, related_name="inventory")
    quantity = models.PositiveIntegerField(default=1)  # Количество предметов

    def __str__(self):
        return f"{self.user.username} — {self.merch.name} x{self.quantity}"


class Transaction(models.Model):
    """Запись о транзакции монет между пользователями"""
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_transactions",
        verbose_name="Отправитель"
    )
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="received_transactions",
        verbose_name="Получатель"
    )
    amount = models.PositiveIntegerField(verbose_name="Количество монет")
    maked_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата транзакции")

    def __str__(self):
        return f"{self.sender.email} -> {self.recipient.email}: {self.amount}"

    class Meta:
        verbose_name = 'Транзакция'
        verbose_name_plural = 'Транзакции'
