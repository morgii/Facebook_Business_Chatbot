from flask import Flask, request
import requests
import difflib
import json
import os
from datetime import datetime



app = Flask(__name__)

PAGE_ACCESS_TOKEN = 'EAAIJLZBcZAgmcBO8IJZBNQt1k9gK2SjZBHsNpY2MvwyfnD82Nl8gkOsl4hDoeRgrZCPygWoRzuScaSZCIUgYhQ3Xvt70Oyx9ebeuLeSPAdm5ZB023RWhskHkqcmxL4A2t1sktkKl9MCTlmrus7eHeB0cYd92iJ3TzDwGW3jjEZBWM71udRU2W04d2ZAMN9QsIEITZB6QZDZD'
API = f"https://graph.facebook.com/v16.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
VERIFY_TOKEN = "anystring"

user_carts = {}
user_payment_methods = {}
user_phone_numbers = {}
ORDERS_FILE = 'data\\orders.json'
INVOICE_NUMBER_COUNTER = 1000  # Start from any number you like



# Load product data from JSON file
with open('data\\products.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

# Load response data from JSON file
with open('data\\responses.json', 'r', encoding='utf-8') as f:
    response_data = json.load(f)



def save_json(file_name, data):
    try:
        with open(file_name, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving file: {str(e)}")

# Helper function to load JSON data
def load_json(file_name):
    if os.path.exists(file_name):
        try:
            with open(file_name, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            print(f"Error loading file: {str(e)}")
    return []






# Helper functions
def send_message(recipient_id, message):
    payload = {"recipient": {"id": recipient_id}, "message": message}
    requests.post(API, json=payload)

def send_button_message(recipient_id, text, buttons):
    message = {
        "attachment": {
            "type": "template",
            "payload": {
                "template_type": "button",
                "text": text,
                "buttons": buttons
            }
        }
    }
    send_message(recipient_id, message)

def send_generic_message(recipient_id, elements):
    message = {
        "attachment": {
            "type": "template",
            "payload": {
                "template_type": "generic",
                "elements": elements
            }
        }
    }
    send_message(recipient_id, message)

def display_products(recipient_id):
    elements = []
    for product in products:
        element = {
            "title": product["title"],
            "image_url": product["image_url"],
            "subtitle": f"Price: {product['price']} BDT\n{product['details']}",
            "buttons": [
                {"type": "postback", "title": "Add to Cart", "payload": f"ADD_TO_CART_{product['code']}"},
                {"type": "postback", "title": "Details", "payload": f"DETAILS_{product['code']}"},
                {"type": "web_url", "title": "View on Web", "url": product["web_url"]}
            ]
        }
        elements.append(element)
    send_generic_message(recipient_id, elements)

def match_score(user_message, pattern):
    return difflib.SequenceMatcher(None, user_message, pattern).ratio()

def find_best_response(user_message):
    best_match = None
    best_score = 0

    for entry in response_data:
        for pattern in entry["patterns"]:
            score = match_score(user_message.lower(), pattern.lower())
            if score > best_score:
                best_score = score
                best_match = entry["response"]
    return best_match

def add_to_cart(recipient_id, code):
    product = next((item for item in products if item["code"] == code), None)
    if not product:
        send_message(recipient_id, {"text": "Product not found."})
        return

    if recipient_id not in user_carts:
        user_carts[recipient_id] = []
    user_carts[recipient_id].append(product)
    send_message(recipient_id, {"text": f"{product['title']} added to your cart."})

    send_button_message(recipient_id, "What would you like to do next?", [
        {"type": "postback", "title": "View Cart", "payload": "VIEW_CART"},
        {"type": "postback", "title": "Checkout", "payload": "CHECKOUT"},
        {"type": "postback", "title": "Continue Shopping", "payload": "VIEW_PRODUCTS"}
    ])

def view_cart(recipient_id):
    if recipient_id not in user_carts or not user_carts[recipient_id]:
        send_message(recipient_id, {"text": "Your cart is empty. Please add items to your cart."})
        return

    cart_items = "\n".join([f"{item['title']}: {item['price']} BDT" for item in user_carts[recipient_id]])
    total_price = sum(item['price'] for item in user_carts[recipient_id])
    send_message(recipient_id, {"text": f"Your Cart:\n{cart_items}\nTotal Price: {total_price} BDT"})


user_selected_payment_method = {}  # Dictionary to track selected payment methods (Bkash/Nagad)


def handle_payment_method(recipient_id, method):
    if method == "PAYMENT_BKASH":
        user_payment_methods[recipient_id] = "Bkash"
        send_message(recipient_id, {
            "text": "Please pay the advance payment via Bkash. You can pay using this link:\n\nhttps://shop.bkash.com/ma-babar-dowa-gaming-ghor01601/paymentlink/default-payment"})
        send_message(recipient_id,
                     {"text": "After making the payment, please provide your phone number to finalize the order."})

    elif method == "PAYMENT_NAGAD":
        user_payment_methods[recipient_id] = "Nagad"
        send_message(recipient_id,
                     {"text": "Please pay the advance payment via Nagad. The payment number is: 0177906626"})
        send_message(recipient_id,
                     {"text": "After making the payment, please provide your phone number to finalize the order."})

    elif method == "PAYMENT_COD":
        user_payment_methods[recipient_id] = "Cash on Delivery"
        send_message(recipient_id, {"text": "Please provide your phone number to confirm the order."})


def checkout(recipient_id):
    # First ask for payment method if not set
    if recipient_id not in user_payment_methods:
        send_button_message(recipient_id, "Please choose your payment method:", [
            {"type": "postback", "title": "Bkash", "payload": "PAYMENT_BKASH"},
            {"type": "postback", "title": "Nagad", "payload": "PAYMENT_NAGAD"},
            {"type": "postback", "title": "Cash on Delivery", "payload": "PAYMENT_COD"}
        ])
    else:
        if user_payment_methods[recipient_id] == "Cash on Delivery":
            send_message(recipient_id, {"text": "Please provide your phone number to confirm the order."})
        else:
            # Ask for phone number after payment method selection
            send_message(recipient_id, {"text": "Please provide your phone number to finalize the order."})


def get_user_name(user_id):
    url = f"https://graph.facebook.com/{user_id}?fields=first_name,last_name&access_token={PAGE_ACCESS_TOKEN}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        return f"{first_name} {last_name}".strip()
    return "Unknown User"

def get_user_profile(user_id):
    url = f"https://graph.facebook.com/{user_id}?fields=first_name,last_name,profile_pic&access_token={PAGE_ACCESS_TOKEN}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return {
            "name": f"{data.get('first_name', '')} {data.get('last_name', '')}".strip(),
            "profile_pic": data.get('profile_pic', '')
        }
    return {"name": "Unknown User", "profile_pic": ""}




def finalize_order(recipient_id):
    global INVOICE_NUMBER_COUNTER  # To modify the global counter

    phone_number = user_phone_numbers.get(recipient_id, "Unknown")
    payment_method = user_payment_methods.get(recipient_id, "Unknown")

    # Check for advanced payment methods (Bkash or Nagad)
    if payment_method == "Advanced Payment":
        payment_method = user_selected_payment_method.get(recipient_id, "Unknown")

    cart_items = [{"title": item['title'], "price": item['price']} for item in user_carts.get(recipient_id, [])]
    total_price = sum(item['price'] for item in user_carts.get(recipient_id, []))

    # Fetch user profile details
    user_profile = get_user_profile(recipient_id)
    customer_name = user_profile["name"]
    profile_pic = user_profile["profile_pic"]

    # Generate invoice number
    invoice_number = INVOICE_NUMBER_COUNTER
    INVOICE_NUMBER_COUNTER += 1  # Increment for the next order

    # Order summary message
    cart_summary = "\n".join([f"{item['title']}: {item['price']} BDT" for item in user_carts.get(recipient_id)])
    send_message(recipient_id, {
        "text": f"Order Summary:\nInvoice No: {invoice_number}\n{cart_summary}\nTotal: {total_price} BDT\nPhone: {phone_number}\nPayment Method: {payment_method}\nThank you for your purchase, {customer_name}! Your order has been confirmed!"
    })

    # Get current date and time
    order_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Updated order_data
    order_data = {
        "invoice_number": invoice_number,
        "customer_id": recipient_id,
        "customer_name": customer_name,
        "profile_pic": profile_pic,
        "phone_number": phone_number,
        "payment_method": payment_method,
        "order_status": "pending",
        "cart_items": cart_items,
        "total_price": total_price,
        "order_date": order_date  # Add order date and time
    }

    # Load existing orders and append the new order
    orders = load_json(ORDERS_FILE)
    orders.append(order_data)

    # Save updated orders
    save_json(ORDERS_FILE, orders)
    print(f"Order saved for user {recipient_id} with invoice {invoice_number}")

    # Reset payment method and cart data
    user_payment_methods.pop(recipient_id, None)
    user_selected_payment_method.pop(recipient_id, None)
    user_phone_numbers.pop(recipient_id, None)
    user_carts.pop(recipient_id, None)



def save_order(recipient_id):
    phone_number = user_phone_numbers.get(recipient_id, "Unknown")
    payment_method = user_payment_methods.get(recipient_id, "Unknown")

    # Check for advanced payment methods (Bkash or Nagad)
    if payment_method == "Advanced Payment":
        payment_method = user_selected_payment_method.get(recipient_id, "Unknown")

    cart_items = [{"title": item['title'], "price": item['price']} for item in user_carts.get(recipient_id, [])]
    total_price = sum(item['price'] for item in user_carts.get(recipient_id, []))

    # Order data
    order_data = {
        "customer_id": recipient_id,
        "phone_number": phone_number,
        "payment_method": payment_method,
        "cart_items": cart_items,
        "total_price": total_price
    }

    # Load existing orders and append the new order
    orders = load_json(ORDERS_FILE)
    orders.append(order_data)

    # Save updated orders
    save_json(ORDERS_FILE, orders)
    print(f"Order saved for user {recipient_id}")



def find_product_by_name_or_code(user_message):
    user_message = user_message.lower()

    # Check for exact or partial matches in product titles or codes
    for product in products:
        product_title = product["title"].lower()
        product_code = product["code"].lower()

        # Check if the product title or code is in the user message
        if product_title in user_message or product_code in user_message:
            return product

    # Use difflib for fuzzy matching if no exact match is found
    best_match = None
    best_score = 0
    for product in products:
        score = max(
            match_score(user_message, product["title"].lower()),
            match_score(user_message, product["code"].lower())
        )
        if score > best_score:
            best_score = score
            best_match = product

    # Return the best match if the score is above a threshold (e.g., 0.5)
    return best_match if best_score >= 0.5 else None




def send_product_details(recipient_id, product):
    element = {
        "title": product["title"],
        "image_url": product["image_url"],
        "subtitle": f"Price: {product['price']} BDT\n{product['details']}",
        "buttons": [
            {"type": "postback", "title": "Add to Cart", "payload": f"ADD_TO_CART_{product['code']}"},
            {"type": "postback", "title": "Details", "payload": f"DETAILS_{product['code']}"},
            {"type": "web_url", "title": "View on Web", "url": product["web_url"]}
        ]
    }
    send_generic_message(recipient_id, [element])



import os

def save_image(image_url, sender_id):
    try:
        # Ensure the directory exists
        save_directory = "data/images/temporary"
        os.makedirs(save_directory, exist_ok=True)

        # Create a unique filename using timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{save_directory}/{sender_id}_{timestamp}.png"

        # Download the image
        response = requests.get(image_url)
        if response.status_code == 200:
            with open(filename, 'wb') as image_file:
                image_file.write(response.content)
            print(f"Image saved as {filename}")
            send_message(sender_id, {"text": "Image received and saved successfully!"})
        else:
            print(f"Failed to download image: {response.status_code}")
            send_message(sender_id, {"text": "Failed to save the image. Please try again."})

    except Exception as e:
        print(f"Error saving image: {str(e)}")
        send_message(sender_id, {"text": "An error occurred while saving the image."})



@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        verify_token = request.args.get("hub.verify_token")
        if verify_token == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "Invalid verification token", 403

    data = request.json
    if 'entry' not in data:
        return "No entry found", 400

    for entry in data['entry']:
        messaging_events = entry.get('messaging', [])
        for messaging_event in messaging_events:
            sender_id = messaging_event['sender']['id']

            # Handle text messages
            if 'message' in messaging_event:
                message_text = messaging_event['message'].get('text', '').strip()

                # Detect phone number
                if message_text.isdigit() and len(message_text) == 11:
                    user_phone_numbers[sender_id] = message_text
                    finalize_order(sender_id)
                elif message_text.lower() == "start":
                    display_products(sender_id)
                else:
                    # Check if the message matches a product title or code
                    product = find_product_by_name_or_code(message_text)
                    if product:
                        send_product_details(sender_id, product)
                    else:
                        # Fallback to finding the best response
                        response = find_best_response(message_text)
                        send_message(sender_id, {"text": response or "I'm sorry, I didn't understand that."})

            # Handle image attachments
            if 'message' in messaging_event and 'attachments' in messaging_event['message']:
                attachments = messaging_event['message']['attachments']
                for attachment in attachments:
                    if attachment['type'] == 'image':
                        image_url = attachment['payload']['url']
                        save_image(image_url, sender_id)

            # Handle postbacks
            elif 'postback' in messaging_event:
                payload = messaging_event['postback']['payload']

                # Routing based on postback payload
                if payload == "VIEW_PRODUCTS":
                    display_products(sender_id)
                elif payload.startswith("ADD_TO_CART_"):
                    product_code = payload.split("_")[-1]
                    add_to_cart(sender_id, product_code)
                elif payload.startswith("DETAILS_"):
                    product_code = payload.split("_")[-1]
                    product = next((item for item in products if item["code"] == product_code), None)
                    if product:
                        send_message(sender_id, {"text": f"{product['title']} Details:\n{product['details']}"})
                elif payload == "VIEW_CART":
                    view_cart(sender_id)
                elif payload == "CHECKOUT":
                    checkout(sender_id)
                elif payload in ["PAYMENT_BKASH", "PAYMENT_NAGAD"]:
                    handle_payment_method(sender_id, payload)
                elif payload == "PAYMENT_COD":
                    handle_payment_method(sender_id, payload)

    return "EVENT_RECEIVED", 200




if __name__ == '__main__':
    app.run(port=2020)
