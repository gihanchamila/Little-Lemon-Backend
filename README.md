

# Little Lemon Backend

This is the backend API for the **Little Lemon** restaurant reservation system, built with Django and Django REST Framework.

---

## Features

* User registration and JWT authentication
* Role-based access (Admin, Manager, Staff, and Users)
* Booking system with table availability checks to avoid double bookings
* Price calculation based on time slots and seating types
* CRUD operations for Admin and Manager on bookings, tables, occasions, payments, etc.
* Read-only endpoints for customers to view occasions, seating types, time slots, and tables
* Users can only manage their own bookings and payments
* Staff can view all bookings

---

## Technologies

* Python 3.x
* Django & Django REST Framework
* SQL database
* JWT Authentication (Simple JWT)

---

## Getting Started

1. Clone the repo:

   ```bash
   git clone https://github.com/gihanchamila/Little-Lemon-Backend.git
   cd Little-Lemon-Backend
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Setup your database and update `settings.py` accordingly.

5. Run migrations:

   ```bash
   python manage.py migrate
   ```

6. Create a superuser for admin access:

   ```bash
   python manage.py createsuperuser
   ```

7. Start the development server:

   ```bash
   python manage.py runserver
   ```

---

## API Endpoints

* **User Registration & Login**
* **Booking Management** (create, view, update user’s bookings)
* **Price Calculation** for bookings (preview price)
* **Admin CRUD** for Tables, Occasions, Seating Types, Time Slots, Payments
* **Read-only lists** for Occasions, Seating Types, Time Slots, Tables

---

## Permissions

* **Admins & Managers** have full or partial CRUD access to backend resources
* **Users** can create and manage their own bookings and payments only
* **Staff** can view all bookings but cannot modify via API

---

## Contact

Gihan Chamila
[GitHub](https://github.com/gihanchamila)


