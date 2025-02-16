from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from merch_store.models import Merch, Inventory, Transaction

User = get_user_model()


class AuthAPITests(APITestCase):
    def setUp(self):
        self.url = reverse("merch_store:auth")
        self.user_data = {
            "username": "testuser@example.com",
            "password": "testpassword"
        }

    def test_auth_missing_fields(self):
        # No data provided
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_auth_register_new_user(self):
        # User does not exist, should be created and token returned
        response = self.client.post(self.url, self.user_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertTrue(User.objects.filter(email=self.user_data["username"]).exists())

    def test_auth_wrong_password(self):
        # Create a user first and try to login with wrong password
        user = User.objects.create(email=self.user_data["username"])
        user.set_password(self.user_data["password"])
        user.save()

        wrong_data = {"username": self.user_data["username"], "password": "wrongpassword"}
        response = self.client.post(self.url, wrong_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("errors", response.data)

    def test_auth_correct_login(self):
        # Create a user and login with correct credentials
        user = User.objects.create(email=self.user_data["username"])
        user.set_password(self.user_data["password"])
        user.save()

        response = self.client.post(self.url, self.user_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)


class SendCoinAPITests(APITestCase):
    def setUp(self):
        # Set up sender and recipient users
        self.sender = User.objects.create(email="sender@example.com")
        self.sender.set_password("password123")
        self.sender.save()

        self.recipient = User.objects.create(email="recipient@example.com", coins=500)
        self.recipient.set_password("password123")
        self.recipient.save()

        self.url = reverse("merch_store:send_coin")
        self.client.force_authenticate(user=self.sender)

    def test_send_coin_missing_fields(self):
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_send_coin_invalid_amount(self):
        # Negative amount
        data = {"toUser": self.recipient.email, "amount": -100}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Non integer amount
        data = {"toUser": self.recipient.email, "amount": "notanumber"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_send_coin_insufficient(self):
        # Sender does not have enough coins
        data = {"toUser": self.recipient.email, "amount": 2000}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_send_coin_success(self):
        transfer_amount = 300
        data = {"toUser": self.recipient.email, "amount": transfer_amount}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Refresh from database to verify updated coins
        self.sender.refresh_from_db()
        self.recipient.refresh_from_db()
        self.assertEqual(self.sender.coins, 1000 - transfer_amount)
        self.assertEqual(self.recipient.coins, 500 + transfer_amount)

        # Verify a transaction record is created
        transaction_obj = Transaction.objects.filter(
            sender=self.sender, recipient=self.recipient, amount=transfer_amount
        ).first()
        self.assertIsNotNone(transaction_obj)

    def test_send_coin_non_existing_recipient(self):
        data = {"toUser": "nonexistent@example.com", "amount": 100}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class InfoAPITests(APITestCase):
    def setUp(self):
        # Create a test user with coins, inventory items and transactions.
        self.user = User.objects.create(email="user@example.com", coins=800)
        self.user.set_password("password123")
        self.user.save()

        # Create merch items for inventory.
        merch_item1 = Merch.objects.create(name="T-Shirt", price=200)
        merch_item2 = Merch.objects.create(name="Cap", price=150)
        Inventory.objects.create(user=self.user, merch=merch_item1, quantity=2)
        Inventory.objects.create(user=self.user, merch=merch_item2, quantity=1)

        # Create transaction history.
        self.other_user = User.objects.create(email="other@example.com", coins=500)
        self.other_user.set_password("password123")
        self.other_user.save()

        # Transaction: user sends coins to other_user.
        Transaction.objects.create(sender=self.user, recipient=self.other_user, amount=100)
        # Transaction: other_user sends coins to user.
        Transaction.objects.create(sender=self.other_user, recipient=self.user, amount=50)

        self.url = reverse("merch_store:user_info")
        self.client.force_authenticate(user=self.user)

    def test_info_data_structure(self):
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertIn("coins", data)
        self.assertIn("inventory", data)
        self.assertIn("coinHistory", data)
        self.assertIn("sent", data["coinHistory"])
        self.assertIn("received", data["coinHistory"])
        self.assertIsInstance(data["inventory"], list)


class BuyItemAPITests(APITestCase):
    def setUp(self):
        # Create user and set initial coin balance.
        self.user = User.objects.create(email="buyer@example.com", coins=1000)
        self.user.set_password("password123")
        self.user.save()

        # Create a merchandise item.
        self.merch_item = Merch.objects.create(name="hoody", price=300)
        self.url = reverse("merch_store:buy_item",
                           kwargs={"item_name": self.merch_item.name})
        self.client.force_authenticate(user=self.user)

    def test_buy_item_not_found(self):
        url = reverse("merch_store:buy_item", kwargs={"item_name": "NonExisting"})
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_buy_item_insufficient_coins(self):
        # Update user's coin balance to below item price.
        self.user.coins = 100
        self.user.save()
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_buy_item_new_purchase(self):
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        # Check that coins are deducted.
        self.assertEqual(self.user.coins, 1000 - self.merch_item.price)

        # Verify inventory record is created.
        inventory = Inventory.objects.filter(user=self.user, merch=self.merch_item).first()
        self.assertIsNotNone(inventory)
        self.assertEqual(inventory.quantity, 1)

    def test_buy_item_update_inventory(self):
        # First purchase.
        self.client.get(self.url, format="json")
        # Second purchase.
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        expected_coins = 1000 - 2 * self.merch_item.price
        self.assertEqual(self.user.coins, expected_coins)

        inventory = Inventory.objects.filter(user=self.user, merch=self.merch_item).first()
        self.assertIsNotNone(inventory)
        self.assertEqual(inventory.quantity, 2)
