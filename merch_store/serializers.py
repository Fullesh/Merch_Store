from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from merch_store.models import User, Transaction


class CreateUserSerializer(serializers.ModelSerializer):
    token = serializers.SerializerMethodField()  # Поле для передачи токена

    class Meta:
        model = User
        fields = ('email', 'password', 'token')
        extra_kwargs = {'password': {'write_only': True}}

    def get_token(self, user):
        """Выдает токен пользователю"""
        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

    def create(self, validated_data):
        """Создает пользователя и сразу выдает ему токен"""
        # Проверка, существует ли пользователь с таким email
        email = validated_data['email']
        password = validated_data['password']

        # Создание пользователя, если его нет
        user, created = User.objects.get_or_create(
            email=email,
            defaults={'password': password}
        )

        if created:
            user.set_password(password)  # Хеширование пароля
            user.save()

        return user


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        # Предполагается, что поле created_at существует в модели.
        # Если поле называется maked_at, замените на него.
        fields = ('id', 'sender', 'recipient', 'amount', 'created_at')


class UserSerializer(serializers.ModelSerializer):
    # Добавляем поле для истории транзакций.
    transactions = serializers.SerializerMethodField()

    class Meta:
        model = User
        # Можно включить все поля или только необходимые.
        fields = '__all__'

    def get_transactions(self, user):
        # Получаем транзакции, где пользователь является отправителем и получателем
        sent = user.sent_transactions.all()
        received = user.received_transactions.all()

        # Объединяем и сортируем транзакции по дате (от новых к старым)
        all_transactions = list(sent) + list(received)
        sorted_transactions = sorted(all_transactions, key=lambda t: t.created_at, reverse=True)
        return TransactionSerializer(sorted_transactions, many=True).data
