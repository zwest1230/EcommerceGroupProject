# 🧾 E-Commerce Payment & Inventory System

## 📦 Project Overview
This project simulates an online storefront and warehouse management system, created for a capstone team project in an IS 4880 course. It supports guest and registered checkout, secure payment API interactions, and real-time warehouse inventory updates — all backed by a MySQL database and powered by Flask.

---

## 🛍️ Customer Features
- Add products to cart with size and quantity
- Checkout as a **guest** or **logged-in user**
- Enter billing and shipping details
- Simulated **payment processing** (Success, Insufficient Funds, Invalid Card)
- Receive confirmation and view **order history**
- Cancel unfulfilled orders (if not settled)

---

## 🏭 Warehouse/Admin Features
- Role-based login system (admin, customer)
- Inventory UI to **add, remove, or update** stock
- View and **settle/cancel** customer orders
- Prevents over-settling based on authorized amounts
- Real-time sync with product availability

---

## 🧰 Technologies Used
- **Flask** for backend and routing
- **HTML/CSS/JS** for dynamic UI
- **MySQL** for persistent data storage
- **Mocky.io API** to simulate payment processing
- **SHA-256 password hashing with salting**
- **Bootstrap/Custom CSS** for responsive design

---

## ⚙️ Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone https://github.com/zwest1230/EcommerceGroupProject
   cd payment-inventory-system
Install Python Dependencies

bash
Copy
Edit
pip install flask mysql-connector-python
Database Setup

Use the store_db.mwb or SQL dump to initialize the schema

Create default users:

admin@examples.com (warehouse)

warehouse@examples.com (warehouse)

test@examples.com (customer)

All default passwords are: password123

Run the Flask App

bash
Copy
Edit
python server.py
Access Pages

http://localhost:5000/ – Storefront

http://localhost:5000/login – Admin Login

http://localhost:5000/inventory – Warehouse UI

📁 Folder Structure
pgsql
Copy
Edit
/static
  ├── css/
  ├── js/
  └── images/
  
/templates
  ├── index.html
  ├── checkout.html
  ├── confirmation.html
  └── inventory.html

server.py       ← Flask backend
store_db.mwb    ← Database model


👥 Team Roles

Frontend & UI Logic – Grayson Glazier, Alan Hardeman

Database & Backend Integration – Lance West

Testing & Validation – Grayson Glazier, Alan Hardeman, Lance West, Ryan Schultz

Warehouse Functionality & API Design – Ryan Schultz

✅ Completed Milestones
Guest checkout and session handling

Live order/stock management

Admin order settlement and cancellation

Real-time product availability and validation

Final milestone testing passed all 23 cases

📌 Notes
This system uses session storage for guest data

Payment mocks simulate 3 scenarios: success, failure, insufficient funds

Orders are masked: only last 4 digits of cards are stored; CVV is hidden
