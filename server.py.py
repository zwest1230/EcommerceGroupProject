from flask import Flask, render_template, redirect, request, session, jsonify
from flask_session import Session
import mysql.connector
import signal
import sys
import hashlib
from collections import defaultdict

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "#HudsonWe2020!",
    "database": "store_db"
}

def db_connect():
    return mysql.connector.connect(**DB_CONFIG)

@app.route("/")
def index():
    db_conn = db_connect()
    cursor = db_conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT p.product_id, p.name, p.price_usd, p.image_url, w.size, w.quantity
        FROM products p
        LEFT JOIN warehouse_has_products w ON p.product_id = w.products_product_id
        WHERE w.warehouse_warehouse_id = 1
    """)

    rows = cursor.fetchall()
    products_dict = defaultdict(lambda: {"sizes": {}})

    for row in rows:
        pid = row['product_id']
        products_dict[pid].update({
            "product_id": pid,
            "name": row['name'],
            "price_usd": row['price_usd'],
            "image_url": row['image_url']
        })
        products_dict[pid]["sizes"][row['size']] = row['quantity']

    products = list(products_dict.values())

    cursor.close()
    db_conn.close()

    return render_template("index.html", products=products)

def hash_and_salt(password):
    salted = password + "store_db"
    encoded = salted.encode(encoding='UTF-8', errors='strict')
    return hashlib.sha256(encoded).hexdigest()

def authenticate_login(email, password):
    hashed = hash_and_salt(password)
    print("Trying to log in with:")
    print("Email:", email)
    print("Password (plain):", password)
    print("Password (hashed):", hashed)

    db_conn = db_connect()
    cursor = db_conn.cursor(dictionary=True)

    sql = """SELECT * FROM users WHERE email = %s AND password_hash = %s LIMIT 1"""
    cursor.execute(sql, (email, hashed))
    users = cursor.fetchall()
    print("Query returned:", users)
    rowsNumber = cursor.rowcount

    cursor.close()
    db_conn.close()

    if rowsNumber != 1:
        raise ValueError('Invalid Credentials')
    return users[0]

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        try:
            user = authenticate_login(email, password)
            if not user:
                raise ValueError("Invalid credentials")

            # Store user session info
            session["user_id"] = user["user_id"]
            session["email"] = user["email"]
            session["user_role_id"] = user["user_role_id"]

            # Redirect based on user role
            if user["user_role_id"] == 2:
                return redirect("/inventory")
            elif user["user_role_id"] == 1:
                return redirect("/order-history")
            else:
                return redirect("/")

        except Exception as error:
            print("🔐 Login failed:", error)
            return redirect("/login", code=401)

    # For GET request
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/signup", methods=["POST", "GET"])
def signup():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        password_hash = hash_and_salt(password)

        db_conn = db_connect()
        cursor = db_conn.cursor(prepared=True)
        try:
            sql = "INSERT INTO users (email, password_hash, user_role_id) VALUES (%s, %s, %s)"
            cursor.execute(sql, (email, password_hash, 1))
            db_conn.commit()
            return redirect("/login")
        except Exception as e:
            return "Signup failed. Try again.", 400
        finally:
            cursor.close()
            db_conn.close()
    return render_template("signup.html")

@app.route("/checkout")
def checkout():
    return render_template("checkout.html")

@app.route("/process-order", methods=["POST"])
def process_order():
    import requests
    data = request.get_json()

    print("📦 RAW REQUEST DATA:", data)

    # Determine mock endpoint
    card_number = data.get("card_number", "")
    if card_number.startswith("4"):
        mock_url = "https://e7642f03-e889-4c5c-8dc2-f1f52461a5ab.mock.pstmn.io/get?authorize=success"
    elif card_number.startswith("5"):
        mock_url = "https://e7642f03-e889-4c5c-8dc2-f1f52461a5ab.mock.pstmn.io/get?authorize=insufficient"
    else:
        mock_url = "https://e7642f03-e889-4c5c-8dc2-f1f52461a5ab.mock.pstmn.io/get?authorize=carddetails"

    try:
        print("📡 Sending to:", mock_url)
        payment_response = requests.get(mock_url, timeout=5)
        print("📥 Response text:", payment_response.text)

        try:
            payment_data = payment_response.json()
            print("🔐 AUTH DATA (raw):", payment_data)
        except Exception as e:
            print("❌ JSON decode error:", e)
            return jsonify({"success": False, "message": "Invalid payment response format"}), 400

        if "Success" not in payment_data:
            return jsonify({
                "success": False,
                "message": "Payment system returned an unexpected response. This may be a bad test card or broken mock endpoint."
            }), 400

        if not payment_data["Success"]:
            return jsonify({
                "success": False,
                "message": payment_data.get("Reason", "Authorization declined.")
            }), 400
        auth_token = payment_data.get("AuthorizationToken")
        auth_amount = payment_data.get("AuthorizedAmount")
        auth_expiration = payment_data.get("TokenExpirationDate")

    except Exception as e:
        print("❌ Request to payment service failed:", e)
        return jsonify({"success": False, "message": "Payment service error"}), 500

    # Calculate tax
    base_amount = float(data.get("amount_usd", 0))
    tax_rate = 0.07
    amount_usd = round(base_amount * (1 + tax_rate), 2)

    print("✅ Total with tax:", amount_usd)

    # Save order info in session
    session["first_name"] = data.get("first_name", "")
    session["last_name"] = data.get("last_name", "")
    session["address"] = data.get("address", "")
    session["city"] = data.get("city", "")
    session["state"] = data.get("state", "")
    session["zip"] = data.get("zip", "")
    session["country"] = data.get("country", "")
    session["shipping_speed"] = data.get("shipping_speed", "")
    session["payment_method"] = data.get("payment_method", "")
    session["email"] = data.get("email", "")
    session["amount_usd"] = amount_usd

    db_conn = db_connect()
    cursor = db_conn.cursor()

    try:
        billing_name = f"{data.get('first_name', '')} {data.get('last_name', '')}"
        billing_address = f"{data.get('address', '')}, {data.get('city', '')}, {data.get('state', '')} {data.get('zip', '')}, {data.get('country', '')}"
        email = data.get("email", "")
        masked_card_number = card_number[-4:] if len(card_number) >= 4 else "XXXX"
        card_ccv = "***"

        insert_order_query = """
            INSERT INTO orders (
                billing_name, billing_address, amount_usd, receipt_email,
                billing_card_number, billing_ccv,
                auth_token, auth_amount, auth_expiration
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        order_values = (
            billing_name,
            billing_address,
            amount_usd,
            email,
            masked_card_number,
            card_ccv,
            f"{data.get('first_name', '')}_{auth_token}",
            auth_amount,
            auth_expiration
        )

        cursor.execute(insert_order_query, order_values)
        order_id = cursor.lastrowid

        cart_items = data.get("cart_items", [])
        for item in cart_items:
            product_id = item["product_id"]
            size = item["size"]
            qty = item["qty"]

            cursor.execute("""
                UPDATE warehouse_has_products
                SET quantity = quantity - %s
                WHERE warehouse_warehouse_id = %s AND products_product_id = %s AND size = %s
            """, (qty, 1, product_id, size))

            cursor.execute("""
                INSERT INTO orders_has_products (orders_order_id, products_product_id, size, quantity, amount_usd)
                VALUES (%s, %s, %s, %s, %s)
            """, (order_id, product_id, size, qty, amount_usd))

        db_conn.commit()
        return jsonify({"success": True})

    except Exception as e:
        db_conn.rollback()
        return jsonify({"success": False, "message": str(e)})

    finally:
        cursor.close()
        db_conn.close()

@app.route("/confirmation")
def confirmation():
    print("SESSION DATA AT CONFIRMATION:", dict(session))
    return render_template("confirmation.html",
        first_name=session.get("first_name", "Customer"),
        last_name=session.get("last_name", ""),
        address=session.get("address", ""),
        city=session.get("city", ""),
        state=session.get("state", ""),
        zip_code=session.get("zip", ""),
        country=session.get("country", ""),
        shipping_speed=session.get("shipping_speed", ""),
        payment_method=session.get("payment_method", ""),
        email=session.get("email", ""),
        amount_usd=session.get("amount_usd", "0.00")
    )

@app.route("/order-history")
def order_history():
    if "email" not in session:
        return redirect("/login")

    user_email = session["email"]
    db_conn = db_connect()
    cursor = db_conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT order_id AS OrderID, billing_name AS CustomerName, billing_address AS Address, amount_usd AS TotalAmount
        FROM orders
        WHERE receipt_email = %s
        ORDER BY order_id DESC
    """, (user_email,))

    orders = cursor.fetchall()
    cursor.close()
    db_conn.close()

    return render_template("orderhistory.html", orders=orders)

@app.route("/inventory")
def inventory():
    return render_template("inventory.html")

@app.route("/api/inventory/update", methods=["POST"])
def update_inventory():
    data = request.get_json()
    product_id = data.get("product_id")
    size = data.get("size")
    quantity = int(data.get("quantity", 0))
    action = data.get("action", "update")

    db_conn = db_connect()
    cursor = db_conn.cursor()

    try:
        if action == "add":
            query = """
                UPDATE warehouse_has_products
                SET quantity = quantity + %s
                WHERE warehouse_warehouse_id = 1 AND products_product_id = %s AND size = %s
            """
        elif action == "remove":
            query = """
                UPDATE warehouse_has_products
                SET quantity = GREATEST(quantity - %s, 0)
                WHERE warehouse_warehouse_id = 1 AND products_product_id = %s AND size = %s
            """
        elif action == "update":
            query = """
                UPDATE warehouse_has_products
                SET quantity = %s
                WHERE warehouse_warehouse_id = 1 AND products_product_id = %s AND size = %s
            """
        else:
            return jsonify({"success": False, "message": "Invalid action."}), 400

        cursor.execute(query, (quantity, product_id, size))
        db_conn.commit()
        return jsonify({"success": True})

    except Exception as e:
        db_conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

    finally:
        cursor.close()
        db_conn.close()

@app.route("/settle-order", methods=["POST"])
def settle_order():
    data = request.get_json()
    order_id = data.get("order_id")
    final_amount = float(data.get("final_amount", 0))

    db_conn = db_connect()
    cursor = db_conn.cursor(dictionary=True)

    try:
        # Look up order info
        cursor.execute("SELECT auth_amount, amount_usd, settled FROM orders WHERE order_id = %s", (order_id,))
        order = cursor.fetchone()

        if not order:
            return jsonify({"success": False, "message": "Order not found."}), 404

        if order["settled"]:
            return jsonify({"success": False, "message": "Order has already been settled."}), 400

        try:
            auth_amount = float(order["auth_amount"])
            order_total = float(order["amount_usd"])
        except (TypeError, ValueError):
            return jsonify({"success": False, "message": "Order amount data is invalid."}), 400

        if final_amount > auth_amount:
            return jsonify({
                "success": False,
                "message": f"Final amount exceeds authorized amount (${auth_amount:.2f})."
            }), 400

        if final_amount > order_total:
            return jsonify({
                "success": False,
                "message": f"Final amount exceeds original order total (${order_total:.2f})."
            }), 400

        cursor.execute("UPDATE orders SET settled = TRUE WHERE order_id = %s", (order_id,))
        print(f"🔍 Settling order_id={order_id}, rows affected: {cursor.rowcount}")
        db_conn.commit()

        return jsonify({"success": True})

    except Exception as e:
        db_conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

    finally:
        cursor.close()
        db_conn.close()

@app.route("/cancel-order", methods=["POST"])
def cancel_order():
    data = request.get_json()
    print("📬 Cancel request received:", data)

    order_id = data.get("order_id")
    email = data.get("email")

    db_conn = db_connect()
    cursor = db_conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM orders WHERE order_id = %s AND receipt_email = %s", (order_id, email))
        order = cursor.fetchone()

        if not order:
            print("❌ No matching order found.")
            return jsonify({"success": False, "message": "Order not found or email mismatch."}), 404

        if order.get("settled"):
            return jsonify({"success": False, "message": "Order already settled, cannot cancel."}), 400

        if order.get("is_cancelled"):
            return jsonify({"success": False, "message": "Order is already cancelled."}), 400

        cursor.execute("UPDATE orders SET is_cancelled = TRUE WHERE order_id = %s", (order_id,))
        print(f"✅ Cancelling order_id={order_id}, rows affected: {cursor.rowcount}")
        db_conn.commit()

        return jsonify({"success": True, "message": f"Order {order_id} cancelled successfully."})

    except Exception as e:
        db_conn.rollback()
        print("❌ Exception:", e)
        return jsonify({"success": False, "message": str(e)}), 500

    finally:
        cursor.close()
        db_conn.close()

    return jsonify({"success": False, "message": "Unexpected error occurred."}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)