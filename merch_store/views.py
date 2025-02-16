from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

# Импорт моделей и сериализаторов (используем организации-специфичные импорты)
from merch_store.models import User, Transaction, Inventory, Merch
from merch_store.serializers import CreateUserSerializer


class AuthAPIView(APIView):
    """
    Эндпойнт для аутентификации и получения JWT-токена.

    URL: /api/auth
    Метод: POST

    Ожидаемые параметры (в теле запроса, application/json):
      - username: строка (на самом деле email, т.к. модель не использует username)
      - password: строка

    Ответ 200: { "token": "JWT-токен" }
    """
    def post(self, request, *args, **kwargs):
        # Согласно OpenAPI схеме, ожидается поле "username"
        email = request.data.get('username')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {"errors": "Both username and password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            user = User.objects.get(email=email)
            if not user.check_password(password):
                return Response(
                    {"errors": "Неверный пароль."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except User.DoesNotExist:
            serializer = CreateUserSerializer(data={'email': email, 'password': password})
            serializer.is_valid(raise_exception=True)
            user = serializer.save()

        token = CreateUserSerializer().get_token(user)
        return Response({'token': token}, status=status.HTTP_200_OK)


class SendCoinAPIView(APIView):
    """
    Эндпойнт для передачи монет от одного пользователя другому.

    URL: /api/sendCoin
    Метод: POST

    Ожидаемые данные в теле запроса (application/json):
      - toUser: строка (email пользователя-получателя)
      - amount: число (количество монет)

    Ответ 200: Успешный ответ, содержащий данные транзакции.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        sender = request.user
        recipient_email = request.data.get('toUser')
        amount = request.data.get('amount')

        if not recipient_email or amount is None:
            return Response(
                {"errors": "Поля 'toUser' и 'amount' обязательны."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            amount = int(amount)
            if amount <= 0:
                return Response(
                    {"errors": "Количество монет должно быть положительным числом."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {"errors": "Поле 'amount' должно быть целым числом."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if sender.coins < amount:
            return Response(
                {"errors": "Недостаточно монет для выполнения транзакции."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            recipient = User.objects.get(email=recipient_email)
        except User.DoesNotExist:
            return Response(
                {"errors": "Пользователь с указанным email не найден."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Выполнение транзакции: обновляем балансы пользователей
        sender.coins -= amount
        recipient.coins += amount
        sender.save()
        recipient.save()

        transaction_record = Transaction.objects.create(sender=sender,
                                                        recipient=recipient, amount=amount)
        response_data = {
            "Отправитель": sender.email,
            "Получатель": recipient.email,
            "Сумма": amount,
            "ID транзакции": transaction_record.id,
            "Время совершения": transaction_record.maked_at
        }
        return Response(response_data, status=status.HTTP_200_OK)


class InfoAPIView(APIView):
    """
    Эндпойнт для получения информации об авторизованном пользователе.

    URL: /api/info
    Метод: GET

    Ответ 200 (application/json):
    {
        "coins": <integer>,
        "inventory": [
            {
                "type": <string>,      # Наименование товара
                "quantity": <integer>
            },
            ...
        ],
        "coinHistory": {
            "received": [
                {
                    "fromUser": <string>,
                    "amount": <integer>
                },
                ...
            ],
            "sent": [
                {
                    "toUser": <string>,
                    "amount": <integer>
                },
                ...
            ]
        }
    }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        coins = user.coins

        # Формирование инвентаря: используем название мерча как "type"
        inventory_items = []
        for item in user.inventory.all():
            inventory_items.append({
                "type": item.merch.name,
                "quantity": item.quantity
            })

        # Формирование истории транзакций отдельно для отправленных и полученных монет
        sent_transactions = user.sent_transactions.all()
        received_transactions = user.received_transactions.all()

        sent_history = []
        for tx in sent_transactions:
            sent_history.append({
                "toUser": tx.recipient.email,
                "amount": tx.amount
            })

        received_history = []
        for tx in received_transactions:
            received_history.append({
                "fromUser": tx.sender.email,
                "amount": tx.amount
            })

        data = {
            "coins": coins,
            "inventory": inventory_items,
            "coinHistory": {
                "received": received_history,
                "sent": sent_history
            }
        }
        return Response(data)


class BuyItemAPIView(APIView):
    """
    Эндпункт для покупки товара по его имени.

    URL: /api/buy/{item}
    Метод: GET

    Логика:
      1. Поиск товара (Merch) по его имени, передаваемому в путевом параметре.
      2. Проверка, хватает ли у пользователя монет для покупки.
      3. Списание монет с баланса пользователя.
      4. Добавление или обновление записи в инвентаре пользователя.

    Ответ 200 (application/json):
    {
        "info": "Покупка успешно совершена. Ваш инвентарь пополнился новыми вещами.",
        "Товар": {
            "Название товара": <string>,
            "Цена за товар": <integer>
        }
    }
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def get(self, request, item_name):
        user = request.user

        try:
            merch_item = Merch.objects.get(name=item_name)
        except Merch.DoesNotExist:
            return Response(
                {"errors": "Товар не найден."},
                status=status.HTTP_404_NOT_FOUND
            )

        if user.coins < merch_item.price:
            return Response(
                {"errors": "Недостаточно монет для покупки данного товара."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.coins -= merch_item.price
        user.save()

        inventory_item, created = Inventory.objects.get_or_create(
            user=user, merch=merch_item, defaults={'quantity': 1}
        )
        if not created:
            inventory_item.quantity += 1
            inventory_item.save()

        response_data = {
            "info": "Покупка успешно совершена. Ваш инвентарь пополнился новыми вещами.",
            "Товар": {
                "Название товара": merch_item.name,
                "Цена за товар": merch_item.price
            }
        }
        return Response(response_data, status=status.HTTP_200_OK)
