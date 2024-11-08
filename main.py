from flask import Flask, request
import requests
import difflib

app = Flask(__name__)

PAGE_ACCESS_TOKEN = 'EAAIJLZBcZAgmcBO8IJZBNQt1k9gK2SjZBHsNpY2MvwyfnD82Nl8gkOsl4hDoeRgrZCPygWoRzuScaSZCIUgYhQ3Xvt70Oyx9ebeuLeSPAdm5ZB023RWhskHkqcmxL4A2t1sktkKl9MCTlmrus7eHeB0cYd92iJ3TzDwGW3jjEZBWM71udRU2W04d2ZAMN9QsIEITZB6QZDZD'
API = f"https://graph.facebook.com/v16.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
VERIFY_TOKEN = "anystring"

user_carts = {}
user_phone_numbers = {}

# Product data
products = [
    {
        "title": "Minecraft Bundle",
        "image_url": "https://www.minecraft.net/content/dam/minecraftnet/games/minecraft/key-art/Homepage_Discover-our-games_MC-Vanilla-KeyArt_864x864.jpg",
        "price": 500,
        "code": "DEMO1"
    },
    {
        "title": "MCPE Personal",
        "image_url": "https://www.minecraft.net/content/dam/minecraftnet/games/minecraft/key-art/Homepage_Discover-our-games_MC-Vanilla-KeyArt_864x864.jpg",
        "price": 700,
        "code": "DEMO2"
    },
    {
        "title": "MCPE Family",
        "image_url": "https://www.minecraft.net/content/dam/minecraftnet/games/minecraft/key-art/Homepage_Discover-our-games_MC-Vanilla-KeyArt_864x864.jpg",
        "price": 900,
        "code": "DEMO3"
    }
]

# Response data for chatbot
response_data = [
    {"patterns": ["dam koto", "price", "how much", 'দাম'], "response": "The price is 500 BDT."},
    {"patterns": ["product er dam", "product price"], "response": "This product costs 500 BDT."},
    {"patterns": ["koto", "rate", "cost"], "response": "The cost is 500 BDT."},
    {"patterns": ["hello", "hi", "hey"], "response": "Hello! How can I help you today?"},
    {"patterns": ["thank you", "thanks"], "response": "You're welcome!"},
    {"patterns": ["delivery time", "kotokhon e delivery", "delivery kotodin e"], "response": "Delivery takes 3-5 business days."},
]

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
            "subtitle": f"Price: {product['price']} BDT",
            "buttons": [
                {"type": "postback", "title": "Add to Cart", "payload": f"ADD_TO_CART_{product['code']}"},
                {"type": "postback", "title": "View Cart", "payload": "VIEW_CART"},
                {"type": "postback", "title": "Checkout", "payload": "CHECKOUT"}
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
        {"type": "postback", "title": "Back to Products", "payload": "VIEW_PRODUCTS"}
    ])

def view_cart(recipient_id):
    if recipient_id not in user_carts or not user_carts[recipient_id]:
        send_message(recipient_id, {"text": "Your cart is empty. Please add items to your cart."})
        return

    cart_items = "\n".join([f"{item['title']}: {item['price']} BDT" for item in user_carts[recipient_id]])
    total_price = sum(item['price'] for item in user_carts[recipient_id])
    send_message(recipient_id, {"text": f"Your Cart:\n{cart_items}\nTotal Price: {total_price} BDT"})

def checkout(recipient_id):
    send_message(recipient_id, {"text": "Please provide your phone number to proceed with checkout."})

def finalize_order(recipient_id):
    phone_number = user_phone_numbers.get(recipient_id, "Unknown")
    cart_summary = "\n".join([f"{item['title']}: {item['price']} BDT" for item in user_carts[recipient_id]])
    total_price = sum(item['price'] for item in user_carts[recipient_id])
    send_message(recipient_id, {
        "text": f"Order Summary:\n{cart_summary}\nTotal: {total_price} BDT\nPhone: {phone_number}\nThank you for your purchase!"
    })

@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        verify_token = request.args.get("hub.verify_token")
        if verify_token == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "Invalid verification token", 403

    data = request.json
    for entry in data['entry']:
        messaging_events = entry['messaging']
        for messaging_event in messaging_events:
            sender_id = messaging_event['sender']['id']

            if 'message' in messaging_event:
                message_text = messaging_event['message'].get('text', '').lower()
                if message_text.isdigit() and len(message_text) == 11:
                    user_phone_numbers[sender_id] = message_text
                    finalize_order(sender_id)
                elif message_text == "start":
                    display_products(sender_id)
                else:
                    response = find_best_response(message_text)
                    if response:
                        send_message(sender_id, {"text": response})
                    else:
                        send_message(sender_id, {"text": "I'm sorry, I didn't understand that."})

            if 'postback' in messaging_event:
                payload = messaging_event['postback']['payload']
                if payload == "VIEW_PRODUCTS":
                    display_products(sender_id)
                elif payload.startswith("ADD_TO_CART_"):
                    product_code = payload.split("_")[-1]
                    add_to_cart(sender_id, product_code)
                elif payload == "VIEW_CART":
                    view_cart(sender_id)
                elif payload == "CHECKOUT":
                    checkout(sender_id)

    return "Message processed", 200

if __name__ == '__main__':
    app.run(port=2020)
