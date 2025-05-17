from django.test import TestCase
from decimal import Decimal
from .models import Menu, Booking

# Create your tests here.
class MenuModelTest(TestCase):
    def test_get_item(self):
        # Create a menu item
        menu_item = Menu.objects.create(
            Title="Test Item",
            Price=10.99,
            Inventory=100
        )

        # Retrieve the item from the database
        retrieved_item = Menu.objects.get(id=menu_item.id)

        # Check if the retrieved item matches the created item
        self.assertEqual(retrieved_item.Title, "Test Item")
        self.assertEqual(retrieved_item.Price, Decimal('10.99'))
        self.assertEqual(retrieved_item.Inventory, 100)

    def test_update_item(self):
        # Create a menu item
        menu_item = Menu.objects.create(
            Title="Test Item",
            Price=10.99,
            Inventory=100
        )

        #update the item
        menu_item.Title = "Updated Item",
        menu_item.Price = 12.99
        menu_item.Inventory = 50
        menu_item.save()

        # Retrieve the updated item from the database
        updated_item = Menu.objects.get(id=menu_item.id)

        # Check if the updated item matches the expected values
        self.assertEqual(updated_item.Title, "Updated Item")
        self.assertEqual(updated_item.Price, Decimal('12.99'))
        self.assertEqual(updated_item.Inventory, 50)

    def test_delete_item(self):
    # Create a menu item
        menu_item = Menu.objects.create(
            Title="Test Item",
            Price=10.99,
            Inventory=100
        )

        # Delete the item
        menu_item.delete()

        # Check if the item no longer exists in the database   
        with self.assertRaises(Menu.DoesNotExist):
            Menu.objects.get(id=menu_item.id)

