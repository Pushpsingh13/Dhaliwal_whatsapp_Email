import os
import re
import smtplib
import time
import urllib.parse
import base64
import streamlit as st
from zoneinfo import ZoneInfo
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from io import BytesIO
from datetime import datetime,timezone
import pytz
import qrcode
from email.mime.application import MIMEApplication
import pandas as pd
import streamlit.components.v1 as components
import razorpay
from privacy_policy import privacy_policy_component
from send_mail import send_daily_orders_email
import datetime as dt

# --- PATH SETUP ---
APP_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(APP_DIR, "Dhaliwal Food court_logo.png")
QR_CODE_APP_PATH = os.path.join(APP_DIR, "QR_Code For App.jpg")
QR_Review_APP_PATH = os.path.join(APP_DIR, "Review QR.png")
BACKGROUND_PATH = os.path.join(APP_DIR, "Dhaliwal Food Court.png")
GOOGLE_REVIEW_URL = "https://g.page/r/CUkluFmztWfYEBM/review"
APP_DOWNLOAD_URL = "https://dhaliwalsfoodcourt.netlify.app/"
ORDER_TYPE = "Pickup Only"
PICKUP_TIME_SLOTS = [
    "Ready in 20–30 minutes",
    "Ready in 30–45 minutes",
    "Ready in 45–60 minutes",
    "Select specific pickup time",]# --- END PATH SETUP ---

RAZORPAY_KEY_ID = st.secrets.get("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = st.secrets.get("RAZORPAY_KEY_SECRET")

razorpay_client = None
if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
else:
    st.warning("Razorpay API keys are not configured in secrets.toml.")

# ReportLab for PDF
canvas = None
MM = 1
try:
    from reportlab.pdfgen import canvas as canvas_
    from reportlab.lib.units import mm as mm_
    canvas = canvas_
    MM = mm_
except ImportError:
    pass
# Show a JPEG banner/image at the very top
st.markdown(
    """
    <style>
    .logo-container {
        display: flex;
        justify-content: center;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# --- HEADER SECTION ---
st.markdown('<div class="header-card">', unsafe_allow_html=True)
c1, c2, c3 = st.columns([1, 4, 1])

# LOGO
with c1:
    if os.path.exists(LOGO_PATH): 
        st.image(LOGO_PATH, width=100)

# TITLE & DETAILS
with c2:
    st.markdown("<h1>Dhaliwals Food Court</h1>", unsafe_allow_html=True)
    st.markdown("Unit of Param Mehar Enterprise Prop Pushpinder Singh Dhaliwal")
    st.markdown("***Timming 🕒 10:00 AM – 10:00 PM • For any enquiry📞 +91-9259317713*** \n\n  **-"Pickup Only • Freshly Prepared Orders required time as per order item._**")
    
    # Download Button and Review Link (Stacked)
    st.markdown(
        f"""
        <div style="display: flex; flex-direction: column; align-items: center; gap: 8px;">
            <a href="{APP_DOWNLOAD_URL}" target="_blank" style="text-decoration:none;">
                <button style="padding:10px 24px; border-radius:8px; background:#ff5722; color:white; border:none; font-weight:600; cursor:pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    📲 Download Our App
                </button>
            </a>
            <a href="{GOOGLE_REVIEW_URL}" target="_blank" style="color:#222; background-color:#fff; padding:6px 12px; border-radius:6px; font-weight:700; font-size:12px; text-decoration:none; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                ⭐ Rate Us on Google
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )

# APP DOWNLOAD QR (Clickable)
with c3:
    if os.path.exists(QR_CODE_APP_PATH):
        # Image wrapped in a link to be clickable
        try:
            with open(QR_CODE_APP_PATH, "rb") as f:
                qr_b64 = base64.b64encode(f.read()).decode()
            
            st.markdown(f"""
                <a href="{APP_DOWNLOAD_URL}" target="_blank">
                    <img src="data:image/png;base64,{qr_b64}" width="100" style="border-radius:10px; cursor:pointer; border: 2px solid white;" alt="Download App">
                </a>
                <div style="margin-top:5px; color:#ddd; font-size:11px;">
                    Scan to Download
                </div>
            """, unsafe_allow_html=True)
        except Exception:
             st.warning("QR Error")
    else:
        # Fallback if image missing
        st.info("App QR Missing")

st.markdown('</div>', unsafe_allow_html=True)

st.info("🛍️ Pickup Only | No Delivery Available. Please collect your order from the counter.")
# =========================
# PAGE CONFIG & STYLING
# =========================
st.set_page_config(page_title="Dhaliwals Food Court Unit of Param Mehar Enterprise Prop Pushpinder Singh Dhaliwal", layout="wide", page_icon=LOGO_PATH)

img = ""
try:
    with open(BACKGROUND_PATH, "rb") as f:
        img = base64.b64encode(f.read()).decode()
except FileNotFoundError:
    pass

st.markdown(
    f"""
<style>
/* ===== GLOBAL ===== */
html, body, [class*="css"] {{
    font-family: 'Segoe UI', sans-serif;
}}

.stApp {{
    background-image: url("data:image/png;base64,{img}");
    background-size: cover;
    background-attachment: fixed;
}}

.block-container {{
    padding-top: 1rem;
}}

/* ===== HEADER ===== */
.header-card {{
    background: rgba(0,0,0,0.65);
    border-radius: 14px;
    padding: 20px;
    margin-bottom: 20px;
    text-align: center;
}}

.header-card h1 {{
    font-size: 48px;
    color: #ffcc80;
    margin-bottom: 5px;
}}

.header-card p {{
    color: #f5f5f5;
    font-size: 16px;
}}

/* ===== MENU CARD ===== */
st.markdown('<div class="menu-card">', unsafe_allow_html=True)
.menu-card {{
    background: white;
    border-radius: 14px;
    padding: 15px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.15);
    transition: transform 0.2s ease;
    height: 100%;
}}

.menu-card:hover {{
    transform: translateY(-4px);
}}

.menu-title {{
    font-size: 18px;
    font-weight: 600;
    margin-top: 10px;
}}

.menu-price {{
    color: #d32f2f;
    font-weight: bold;
    margin-bottom: 8px;
}}

/* ===== BUTTONS ===== */
.stButton > button {{
    border-radius: 10px;
    font-weight: 600;
    padding: 8px;
}}

.stButton > button:hover {{
    opacity: 0.9;
    
}}st.markdown('</div>', unsafe_allow_html=True)

/* ===== BILL PANEL ===== */
st.markdown('<div class="bill-card">', unsafe_allow_html=True)
.bill-card {{
    background: rgba(255,255,255,0.95);
    border-radius: 14px;
    padding: 15px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.15);
}}

.bill-item {{
    display: flex;
    justify-content: space-between;
    font-size: 14px;
    margin-bottom: 4px;
}}

.total-amount {{
    font-size: 20px;
    font-weight: bold;
    color: #2e7d32;
    }}st.markdown('</div>', unsafe_allow_html=True)

/* ===== MOBILE ===== */
@media (max-width: 768px) {{
    .header-card h1 {{
        font-size: 32px;
    }}
}}
</style>
""",
    unsafe_allow_html=True,
)

# =========================
# CONFIG
# =========================
MENU_EXCEL = os.path.join(APP_DIR, "DhalisMenu.xlsx")
ORDERS_DIR = "Orders"  # daily order logs
ADMIN_PASSWORD = "admin123"  # change after first run

# Consolidated CSV path (same directory as this app.py)
ORDERS_CSV = os.path.join(os.path.dirname(__file__), "orders.csv")


def get_secret(key: str, default: str = "") -> str:
    try:
        return st.secrets[key]
    except Exception:
        return os.environ.get(key, default)


DEFAULT_SMTP_SERVER = get_secret("SMTP_SERVER", "smtp.gmail.com")
DEFAULT_SMTP_PORT = int(get_secret("SMTP_PORT", "587"))
DEFAULT_SENDER_EMAIL = get_secret("SENDER_EMAIL", "")
DEFAULT_SENDER_PASSWORD = get_secret("SENDER_PASSWORD", "")

_defaults = {
    "bill": [],
    "total": 0.0,
    "cust_name": "",
    "cust_phone": "",
    "cust_addr": "",
    "cust_email": "",
    "gst_rate": 0.0,
    "delivery_charge_rate": 0,
    "discount": 0.0,
    "smtp_server": DEFAULT_SMTP_SERVER,
    "smtp_port": DEFAULT_SMTP_PORT,
    "sender_email": DEFAULT_SENDER_EMAIL,
    "sender_password": DEFAULT_SENDER_PASSWORD,
    "owner_phone": "919259317713",
    "uploaded_menu_file": None,
    "edit_smtp": False,
    "payment_option": None,
    "last_activity": time.time(),
    "order_finalized_time": None,
    "show_upi": False,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =========================
# HELPERS
# =========================

def get_local_time():
    return datetime.now(pytz.timezone('Asia/Calcutta'))

def ensure_orders_csv_exists():
    """Creates the orders.csv file with headers if it doesn't exist."""
    if not os.path.exists(ORDERS_CSV):
        try:
            df = pd.DataFrame(columns=[
                "Date", "Time", "OrderID", "CustomerName", "Phone", "Email",
                "Address", "Items", "Subtotal", "DeliveryChargeAmount", "GST",
                "PaymentMethod", "Discount", "razorpay_fee", "GrandTotal"
            ])
            df.to_csv(ORDERS_CSV, index=False, mode='w')
        except Exception as e:
            st.error(f"Failed to create {ORDERS_CSV}: {e}")

def clean_text(txt):
    if not txt:
        return "-"
    return str(txt).replace("\n", " ").replace("\r", " ")


def ensure_orders_dir():
    if not os.path.exists(ORDERS_DIR):
        os.makedirs(ORDERS_DIR, exist_ok=True)


def today_orders_path():
    ensure_orders_dir()
    return os.path.join(ORDERS_DIR, f"Orders_{get_local_time().strftime('%Y-%m-%d')}.xlsx")


def only_digits(s: str) -> str:
    return re.sub(r"\D", "", s or "")


def create_default_menu():
    df = pd.DataFrame(
        {
            "Item": ["Veg Biryani", "Paneer Butter Masala", "Dal Makhani"],
            "Half": [80, 120, 90],
            "Full": [150, 200, 170],
            "Image": ["", "", ""],
        }
    )
    df.to_excel(MENU_EXCEL, index=False, engine="openpyxl")


def load_menu(uploaded_file=None):
    try:
        source = None
        if uploaded_file:
            source = uploaded_file
        elif os.path.exists(MENU_EXCEL):
            source = MENU_EXCEL
        else:
            create_default_menu()
            source = MENU_EXCEL

        df = pd.read_excel(source, engine="openpyxl")

        for col in ["Item", "Half", "Full", "Image"]:
            if col not in df.columns:
                raise ValueError("Excel must have 'Item', 'Half', 'Full' and 'Image' columns")
        df["Half"] = pd.to_numeric(df["Half"], errors="coerce").fillna(0)
        df["Full"] = pd.to_numeric(df["Full"], errors="coerce").fillna(0)
        df["Item"] = df["Item"].fillna("").astype(str)
        df["Image"] = df["Image"].fillna("").astype(str)
        return df
    except Exception as e:
        st.error(f"Error loading menu: {e}")
        return pd.DataFrame(columns=["Item", "Half", "Full", "Image"])


def save_menu(df):
    try:
        df.to_excel(MENU_EXCEL, index=False, engine="openpyxl")
        return True
    except Exception as e:
        st.error(f"Failed to save menu: {e}")
        return False


def add_to_bill(item, price, size, quantity=1):
    st.session_state["last_activity"] = time.time()
    st.session_state["order_finalized_time"] = None
    # Check if item with same size already exists
    for bill_item in st.session_state["bill"]:
        if bill_item['item'] == item and bill_item['size'] == size:
            bill_item['quantity'] += quantity
            st.session_state["total"] += float(price) * quantity
            st.rerun()

    st.session_state["bill"].append({"item": str(item), "price": float(price), "size": str(size), "quantity": quantity})
    st.session_state["total"] += float(price) * quantity
    st.rerun()


def clear_bill():
    st.session_state["bill"] = []
    st.session_state["total"] = 0.0
    st.session_state["cust_name"] = ""
    st.session_state["cust_phone"] = ""
    st.session_state["cust_addr"] = ""
    st.session_state["cust_email"] = ""
    st.session_state["payment_option"] = None
    st.session_state["last_activity"] = time.time()
    st.session_state["order_finalized_time"] = None


def build_pdf_receipt(order_id: str) -> BytesIO | None:
    if canvas is None or MM is None:
        st.error("ReportLab is not installed. Please run: pip install reportlab")
        return None

    # --- FONT SETUP FOR RUPEE SYMBOL ---
    FONT_NAME = 'Helvetica'
    FONT_NAME_BOLD = 'Helvetica-Bold'
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        font_path = os.path.join(APP_DIR, "DejaVuSans.ttf")
        pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
        FONT_NAME = 'DejaVuSans'
        FONT_NAME_BOLD = 'DejaVuSans'  # Using regular for bold as well, as bold version might not be available
    except Exception as e:
        st.warning(f"Could not load a font that supports the Rupee symbol (₹). Please add 'DejaVuSans.ttf' to the app directory. Error: {e}")
    # --- END FONT SETUP ---

    lines = max(1, len(st.session_state["bill"]))
    thermal_width = 80 * MM
    thermal_height = (70 + 8 * lines + 40) * MM

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(thermal_width, thermal_height))

    y = thermal_height - 10
    c.drawImage(LOGO_PATH, 2 * MM, y - 5 * MM, width=20 * MM, height=10 * MM)
    c.drawImage(LOGO_PATH, thermal_width - 22 * MM, y - 5 * MM, width=20 * MM, height=10 * MM)
    y -= 12
    c.setFont(FONT_NAME_BOLD, 10)
    c.drawCentredString(thermal_width / 2, y, "Dhaliwals Food Court")
    y -= 5
    c.setFont(FONT_NAME, 4)
    c.drawCentredString(thermal_width / 2, y, "Unit of Param Mehar Enterprise Prop Pushpinder Singh Dhaliwal")
    y -= 7
    c.setFont(FONT_NAME, 4)
    c.drawCentredString(thermal_width / 2, y, "Meerut, UP | Ph: +91-9259317713")
    y -= 10
    c.line(0, y, thermal_width, y)

    y -= 12
    now_str = get_local_time().strftime("%d %b %Y %H:%M:%S")
    c.setFont(FONT_NAME, 8)
    c.drawString(2, y, f"Bill Time: {now_str}")
    y -= 10
    c.drawString(2, y, f"Order ID: {order_id}")
    y -= 10
    c.drawString(2, y, f"Customer: {clean_text(st.session_state['cust_name'])}")
    y -= 10
    c.drawString(2, y, f"Phone: {clean_text(st.session_state['cust_phone'])}")
    y -= 10
    c.drawString(2, y, f"Email: {clean_text(st.session_state['cust_email'])}")
    y -= 10
    c.drawString(2, y, f"Address: {clean_text(st.session_state['cust_addr'])}")
    y -= 10
    c.drawString(2, y, f"Payment Method: {st.session_state.get('payment_method', 'N/A')}")

    y -= 10
    c.line(0, y, thermal_width, y)
    y -= 12

    c.setFont(FONT_NAME_BOLD, 8)
    c.drawString(2, y, "Item")
    c.drawRightString(thermal_width - 2, y, "Price")

    y -= 10
    c.setFont(FONT_NAME, 8)
    subtotal = 0.0
    for row in st.session_state["bill"]:
        item_line = clean_text(f"{row['quantity']}x {row['item']} ({row['size']})")
        price_str = f"₹{row['price'] * row['quantity']:.2f}"
        c.drawString(2, y, item_line[:28])
        c.drawRightString(thermal_width - 2, y, price_str)
        y -= 10
        subtotal += float(row["price"]) * row['quantity']

    delivery_charge_rate = float(st.session_state.get("delivery_charge_rate", 0.0))
    gst_rate = float(st.session_state.get("gst_rate", 0.0))
    discount = float(st.session_state["discount"])
    delivery_charge = subtotal * delivery_charge_rate / 100.0
    gst_amount = subtotal * gst_rate / 100.0
    razorpay_fee = 0.0
    if st.session_state.get("payment_method") == "Razorpay":
        razorpay_fee = subtotal * 0.026
    grand_total = subtotal + delivery_charge + gst_amount - discount + razorpay_fee

    c.line(0, y, thermal_width, y)
    y -= 12
    c.setFont(FONT_NAME_BOLD, 8)
    c.drawString(2, y, "Subtotal")
    c.drawRightString(thermal_width - 2, y, f"₹{subtotal:.2f}")
    y -= 10
    c.drawString(2, y, "Delivery Charge")
    c.drawRightString(thermal_width - 2, y, f"₹{delivery_charge:.2f}")
    y -= 10
    c.drawString(2, y, f"GST ({gst_rate}%)")
    c.drawRightString(thermal_width - 2, y, f"₹{gst_amount:.2f}")
    y -= 10
    if razorpay_fee > 0:
        c.drawString(2, y, "Razorpay Fee")
        c.drawRightString(thermal_width - 2, y, f"₹{razorpay_fee:.2f}")
        y -= 10
    c.drawString(2, y, "Discount")
    c.drawRightString(thermal_width - 2, y, f"-₹{discount:.2f}")
    y -= 10
    c.drawString(2, y, "Grand Total")
    c.drawRightString(thermal_width - 2, y, f"₹{grand_total:.2f}")

    y -= 14
    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(thermal_width / 2, y, "Thank you for visiting!")

    c.showPage()
    c.save()
    buf.seek(0)
    return buf
def save_order_log(order_id: str, subtotal: float, delivery_charge: float, gst_amount: float, discount: float, grand_total: float, payment_method: str, razorpay_fee: float = 0.0):
    """Logs order to the daily Excel file AND appends to consolidated orders.csv"""
    ensure_orders_dir()
    path = today_orders_path()
    now = get_local_time()
    row = {
        "Date": now.strftime("%d-%m-%Y"),
        "Time": now.strftime("%H:%M:%S"),
        "OrderID": order_id,
        "CustomerName": st.session_state["cust_name"],
        "Phone": st.session_state["cust_phone"],
        "Email": st.session_state["cust_email"],
        "Address": st.session_state["cust_addr"],
        "Items": "; ".join([f"{i['quantity']}x {i['item']}({i['size']})-₹{i['price']:.2f}" for i in st.session_state["bill"]]),
        "Subtotal": subtotal,
        "DeliveryChargeAmount": delivery_charge,
        "GST": gst_amount,
        "PaymentMethod": payment_method,
        "Discount": discount,
        "razorpay_fee": razorpay_fee,
        "GrandTotal": grand_total,
    }

    # Save to daily Excel
    try:
        if os.path.exists(path):
            df = pd.read_excel(path, engine="openpyxl")
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        else:
            df = pd.DataFrame([row])
        df.to_excel(path, index=False, engine="openpyxl")
    except Exception as e:
        st.warning(f"Could not log order to Excel ({path}): {e}")

    # Save to consolidated CSV
    try:
        # Convert the row dictionary to a DataFrame
        df_new_row = pd.DataFrame([row])
        
        # Check if the file exists to decide whether to write headers
        header = not os.path.exists(ORDERS_CSV)
        
        # Append to the CSV file
        df_new_row.to_csv(ORDERS_CSV, mode='a', header=header, index=False)
        
    except Exception as e:
        st.warning(f"Could not log order to CSV ({ORDERS_CSV}): {e}")


# ==== Messaging helpers (email + WhatsApp) ====

def send_email_with_pdf(to_email: str, pdf_bytes: bytes, order_id: str) -> bool:
    if not to_email:
        st.error("Customer email is empty.")
        return False
    if not st.session_state["sender_email"] or not st.session_state["sender_password"]:
        st.error("Sender email credentials are missing. Configure in Admin → Email Settings.")
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = st.session_state["sender_email"]
        recipients = [to_email, st.session_state["sender_email"]]
        msg["To"] = to_email
        msg["Subject"] = f"Your Dhaliwals Food Court Bill (Order {order_id})"

        body = MIMEText(
            f"Dear {st.session_state['cust_name'] or 'Customer'},\n\n"
            f"Thanks for your order. Your bill is attached as a PDF.\n\n"
            f"Order ID: {order_id}\n"
            f"Date: {get_local_time().strftime('%d %b %Y %H:%M')}\n\n"
            f"Regards,\nDhaliwals Food Court.",
            "plain",
        )
        msg.attach(body)

        part = MIMEApplication(pdf_bytes, Name=f"receipt_{order_id}.pdf")
        part["Content-Disposition"] = f'attachment; filename="receipt_{order_id}.pdf"'
        msg.attach(part)

        server = smtplib.SMTP(st.session_state["smtp_server"], st.session_state["smtp_port"], timeout=20)
        server.starttls()
        server.login(st.session_state["sender_email"], st.session_state["sender_password"])
        server.sendmail(st.session_state["sender_email"], recipients, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False


def send_email_to_owner(pdf_bytes: bytes, order_id: str) -> bool:
    owner_email = st.session_state["sender_email"]
    if not owner_email:
        st.error("Owner email (sender email) is not configured.")
        return False
    if not st.session_state["sender_password"]:
        st.error("Sender email password is missing.")
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = st.session_state["sender_email"]
        msg["To"] = owner_email
        msg["Subject"] = f"New Order Received: {order_id}"

        body = MIMEText(
            f"A new order has been placed.\n\n"
            f"Order ID: {order_id}\n"
            f"Customer: {st.session_state['cust_name']}\n"
            f"Phone: {st.session_state['cust_phone']}\n"
            f"Address: {st.session_state['cust_addr']}\n"
            f"Date: {get_local_time().strftime('%d %b %Y %H:%M')}\n\n"
            f"The bill is attached as a PDF.",
            "plain",
        )
        msg.attach(body)

        part = MIMEApplication(pdf_bytes, Name=f"receipt_{order_id}.pdf")
        part["Content-Disposition"] = f'attachment; filename="receipt_{order_id}.pdf"'
        msg.attach(part)

        server = smtplib.SMTP(st.session_state["smtp_server"], st.session_state["smtp_port"], timeout=20)
        server.starttls()
        server.login(st.session_state["sender_email"], st.session_state["sender_password"])
        server.sendmail(st.session_state["sender_email"], owner_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Failed to send email to owner: {e}")
        return False


def send_whatsapp_message(to_number_raw: str, order_id: str, subtotal: float, delivery_charge: float, gst_amount: float, grand_total: float, razorpay_fee: float = 0.0) -> bool:
    to_digits = "".join([c for c in str(to_number_raw) if c.isdigit()])
    if not to_digits:
        st.error("Invalid customer phone for WhatsApp.")
        return False

    items_str = "\n".join([
        f"- {i['quantity']}x {i['item']} ({i['size']}): ₹{i['price'] * i['quantity']:.2f}"
        for i in st.session_state["bill"]
    ])

    customer_name = st.session_state.get("cust_name", "").strip()
    cust_name_str = f"Hello {customer_name},\n\n" if customer_name else ""

    razorpay_fee_str = f"*Razorpay Fee:* ₹{razorpay_fee:.2f}\n" if razorpay_fee > 0 else ""
    gst_rate = float(st.session_state.get("gst_rate", 0.0))

    message = (
        f"{cust_name_str}Thank you for your order from Dhaliwals Food Court!\n\n"
        f"*Order ID:* {order_id}\n"
        f"*Date:* {get_local_time().strftime('%d %b %Y %H:%M')}\n\n"
        f"*Items:*\n{items_str}\n\n"
        f"*Subtotal:* ₹{subtotal:.2f}\n"
        f"*Delivery Charge:* ₹{delivery_charge:.2f}\n"
        f"*GST ({gst_rate}%):* ₹{gst_amount:.2f}\n"
        f"{razorpay_fee_str}"
        f"*Grand Total:* ₹{grand_total:.2f}\n\n"
        f"We hope you enjoy your meal!"
    )

    url = f"https://wa.me/{to_digits}?text={urllib.parse.quote(message)}"
    st.markdown(f'<a href="{url}" target="_blank">Click here to send WhatsApp message</a>', unsafe_allow_html=True)
    return True


# =========================
# APP LAYOUT
# =========================
# Auto-clear logic
# 1. After 1 minute of finalizing an order
if st.session_state.get("order_finalized_time") and (time.time() - st.session_state["order_finalized_time"] > 60):
    clear_bill()
    st.toast("Auto-clearing for next order.")
    time.sleep(1)
    st.rerun()
# 2. After 2 minutes of inactivity before finalizing
elif not st.session_state.get("order_finalized_time") and 'last_activity' in st.session_state and (time.time() - st.session_state["last_activity"] > 900):
    clear_bill()
    st.toast("Bill cleared due to inactivity.")
    time.sleep(1)
    st.rerun()

ensure_orders_csv_exists()
menu_df = load_menu(st.session_state["uploaded_menu_file"])


# Top Header (Dhaliwals Food Court Unit of Param Mehar Enterprise Prop Pushpinder Singh Dhaliwal)
st.markdown('<p class="main-title">Dhaliwals Food Court</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Unit of Param Mehar Enterprise Prop Pushpinder Singh Dhaliwal</p>', unsafe_allow_html=True)

st.markdown("*Date:* " + get_local_time().strftime("%d %b %Y %H:%M"))
st.write("---")

# ------------------------------
# ADMIN PANEL (FULL MERGED VERSION)
# ------------------------------

# -----------------------------
# CONSTANTS / SECRETS
# -----------------------------
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
OWNER_EMAIL = st.secrets["OWNER_EMAIL"]
SENDER_EMAIL = st.secrets["SENDER_EMAIL"]
SENDER_PASSWORD = st.secrets["SENDER_PASSWORD"]
SEND_TIME = st.secrets.get("SEND_TIME", "23:30")   # HH:MM IST
ORDERS_CSV = "orders.csv"
LAST_RUN_FILE = "last_run_date.txt"



# ======================================================
# 📌 EMAIL SCHEDULER HELPER FUNCTIONS
# ======================================================

def send_end_of_day_orders():
    """Send today's orders.csv to the owner via email."""
    if not os.path.exists(ORDERS_CSV):
        st.warning("orders.csv not found — skipping send.")
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = OWNER_EMAIL
        msg["Subject"] = "End of Day Orders"
        msg.attach(MIMEText("Today's orders are attached.", "plain"))

        with open(ORDERS_CSV, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", "attachment; filename=orders.csv")
            msg.attach(part)

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True

    except Exception as e:
        st.error(f"Email send failed: {e}")
        return False

def get_server_utc_now():
    return datetime.now(timezone.utc)

def get_local_now(tz_name):
    tz = pytz.timezone(tz_name)
    utc_now = get_server_utc_now()
    return utc_now.astimezone(tz)

# Example usage
local_now = get_local_now("Asia/Kolkata")

def read_last_run_date():
    if not os.path.exists(LAST_RUN_FILE):
        return None
    try:
        with open(LAST_RUN_FILE, "r") as f:
            return dt.date.fromisoformat(f.read().strip())
    except:
        return None

def write_last_run_date(d: dt.date):
    with open(LAST_RUN_FILE, "w") as f:
        f.write(d.isoformat())

# ======================================================
# 📌 ADMIN PANEL SIDEBAR
# ======================================================
with st.sidebar:
    st.header("Admin Panel")

    password = st.text_input("Enter Admin Password", type="password")

    if password == ADMIN_PASSWORD:
        st.success("Logged in as Admin")
        

        # -----------------------
        # MENU UPLOAD
        # -----------------------
        st.subheader("Upload Menu")
        uploaded_menu_file = st.file_uploader("Upload DhalisMenu.xlsx", type=["xlsx"])
        if uploaded_menu_file:
            st.session_state["uploaded_menu_file"] = uploaded_menu_file
            st.success("Menu file uploaded.")
            st.rerun()

        # -----------------------
        # MENU EDITOR
        # -----------------------
        st.subheader("Menu Editor")
        edited_df = st.data_editor(
            menu_df, num_rows="dynamic", use_container_width=True, key="menu_editor"
        )

        if st.button("Save Menu Changes"):
            if save_menu(edited_df):
                st.success("Menu saved successfully!")
                st.rerun()

        st.divider()

        # -----------------------
        # DISABLE MENU ITEM
        # -----------------------
        st.subheader("Disable Menu Item")

        if not menu_df.empty:
            disable_item = st.selectbox("Select item to disable", menu_df["Item"])
            if st.button("Disable Selected Item"):
                menu_df2 = menu_df[menu_df["Item"] != disable_item]
                if save_menu(menu_df2):
                    st.success(f"{disable_item} removed from menu.")
                    st.rerun()
        else:
            st.info("Menu is empty.")

        st.divider()

        # -----------------------
        # BILLING SETTINGS
        # -----------------------
        st.subheader("Billing Settings")
        st.session_state["gst_rate"] = st.number_input(
            "GST Rate (%)",
            value=float(st.session_state.get("gst_rate", 0.0)),
            step=0.5,
        )
        st.session_state["discount"] = st.number_input(
            "Discount (₹)",
            value=float(st.session_state.get("discount", 0.0)),
            step=1.0,
        )
        st.session_state["show_upi"] = st.checkbox(
            "Show UPI Payment Option",
            value=st.session_state.get("show_upi", True),
        )

        st.divider()

        # -----------------------
        # OWNER SETTINGS
        # -----------------------
        st.subheader("Owner Settings")
        st.text_input(
            "Owner WhatsApp Number",
            value=st.session_state.get("owner_phone", ""),
            disabled=True,
        )

        st.divider()

        # -----------------------
        # SMTP SETTINGS (LOCK/UNLOCK)
        # -----------------------
        st.subheader("Email Settings (SMTP)")

        if st.session_state.get("edit_smtp", False):
            with st.form("smtp_edit_form"):
                st.text_input("SMTP Server", key="smtp_server_input", value=st.session_state["smtp_server"])
                st.number_input("SMTP Port", key="smtp_port_input", value=int(st.session_state["smtp_port"]))
                st.text_input("Sender Email", key="sender_email_input", value=st.session_state["sender_email"])
                st.text_input("Sender Password", key="sender_password_input", value=st.session_state["sender_password"], type="password")

                save_submitted = st.form_submit_button("Save SMTP Settings")

                if save_submitted:
                    st.session_state["smtp_server"] = st.session_state["smtp_server_input"]
                    st.session_state["smtp_port"] = st.session_state["smtp_port_input"]
                    st.session_state["sender_email"] = st.session_state["sender_email_input"]
                    st.session_state["sender_password"] = st.session_state["sender_password_input"]

                    st.session_state["edit_smtp"] = False
                    st.success("SMTP settings updated.")
                    time.sleep(1)
                    st.rerun()

        else:
            st.text_input("SMTP Server", value=st.session_state["smtp_server"], disabled=True)
            st.number_input("SMTP Port", value=int(st.session_state["smtp_port"]), disabled=True)
            st.text_input("Sender Email", value=st.session_state["sender_email"], disabled=True)
            st.text_input("Sender Password", value="********", type="password", disabled=True)

            with st.form("smtp_unlock_form"):
                unlock_password = st.text_input("Enter Admin Password", type="password")
                unlock_submit = st.form_submit_button("Unlock to Edit")
                if unlock_submit:
                    if unlock_password == ADMIN_PASSWORD:
                        st.session_state["edit_smtp"] = True
                        st.rerun()
                    else:
                        st.error("Incorrect password.")

        st.divider()

        # -----------------------
        # EXPORT ORDERS
        # -----------------------
        st.subheader("Orders Export")

        if os.path.exists(ORDERS_CSV):
            with open(ORDERS_CSV, "rb") as f:
                st.download_button("Download Orders (CSV)", f, file_name="orders.csv")
        else:
            st.info("No orders yet.")

        today_file = today_orders_path()
        if os.path.exists(today_file):
            with open(today_file, "rb") as f:
                st.download_button(
                    "Download Today's Orders (Excel)",
                    f,
                    file_name=os.path.basename(today_file),
                )
        else:
            st.caption("Today's Excel log will appear after the first order is logged.")

        st.divider()

    # -----------------------
        # AUTO SEND END-OF-DAY MAIL
        # -----------------------
        st.subheader("Admin Controls")

        # Manual Send Button
        if st.button("Send Orders Email Now"):
            try:
                send_daily_orders_email()
                st.success("Email sent successfully!")
            except Exception as e:
                st.error(f"Error sending email: {e}")

        # -----------------------
        # DAILY EMAIL AUTOMATION
        # -----------------------
        st.subheader("Daily Email Automation")

        local_now = get_local_now("Asia/Kolkata")
        st.write("Local time:", local_now.strftime("%Y-%m-%d %H:%M:%S"))

        send_hour, send_minute = map(int, SEND_TIME.split(":"))
        send_time_today = local_now.replace(hour=send_hour, minute=send_minute, second=0)

        last_run = read_last_run_date()
        today = local_now.date()

        if local_now >= send_time_today and last_run != today:
            st.info(f"Time reached ({SEND_TIME}). Sending email…")
            success = send_end_of_day_orders()
            if success:
                write_last_run_date(today)
                st.success("Email sent!")
        else:
            if last_run == today:
                st.write("Email already sent today.")
            else:
                st.write(f"Waiting for {SEND_TIME}…")
    # WRONG PASSWORD
    elif password:
        st.error("Incorrect password")


col1, col2 = st.columns([3, 1], gap="large")

with col1:
    st.header("🍴 Dhaliwals Food Court Menu")

    if not menu_df.empty:
        # Display menu in a grid (3 items per row)
        cols_per_row = 3
        for i in range(0, len(menu_df), cols_per_row):
            cols = st.columns(cols_per_row)
            for idx, col in enumerate(cols):
                if i + idx < len(menu_df):
                    row = menu_df.iloc[i + idx]
                    item = row["Item"]
                    half_price = row["Half"]
                    full_price = row["Full"]
                    image_path = str(row["Image"]).strip() if pd.notna(row["Image"]) else None

                    with col:
                        # Show item image
                        if image_path and os.path.exists(image_path):
                            st.image(image_path, width=150)
                        elif image_path and image_path.startswith("http"):
                            st.image(image_path, width=150)

                        # Item name
                        st.markdown(f"### {item}")

                        # Quantity selector and buttons
                        item_index = i + idx
                        qty = st.number_input("Quantity", min_value=1, max_value=10, value=1, step=1, key=f"qty_{item_index}_{item}")

                        if half_price > 0:
                            col1_btn, col2_btn = st.columns(2)
                            with col1_btn:
                                if st.button(f"Half ₹{half_price}", key=f"half_{item_index}_{item}"):
                                    add_to_bill(item, half_price, "Half", qty)
                            with col2_btn:
                                if st.button(f"Full ₹{full_price}", key=f"full_{item_index}_{item}"):
                                    add_to_bill(item, full_price, "Full", qty)
                        else:
                            if st.button(f"Full ₹{full_price}", key=f"full_{item_index}_{item}", use_container_width=True):
                                add_to_bill(item, full_price, "Full", qty)
    else:
        st.warning("Menu is empty. Please add items via Admin Panel.")

with col2:
    
    st.header("Current Bill")
    if st.session_state["bill"]:
        for i, bill_item in reversed(list(enumerate(st.session_state["bill"]))):
            col1, col2, col3 = st.columns([4, 2, 1])
            with col1:
                st.text(f"{bill_item['quantity']}x {bill_item['item']} ({bill_item['size']})")
            with col2:
                st.text(f"₹{bill_item['price'] * bill_item['quantity']:.2f}")
            with col3:
                if st.button("🗑️", key=f"delete_{i}"):
                    st.session_state["last_activity"] = time.time()
                    removed_item = st.session_state["bill"].pop(i)
                    st.session_state["total"] -= removed_item['price'] * removed_item['quantity']
                    st.rerun()
                            
        st.markdown("---")
        st.markdown(
    f'<div class="total-amount">Total: ₹{st.session_state["total"]:.2f}</div>',
    unsafe_allow_html=True
)

        st.session_state["cust_name"] = st.text_input("Customer Name", value=st.session_state["cust_name"], disabled=st.session_state["payment_option"] is not None)
        st.session_state["cust_phone"] = st.text_input(
            "Customer Phone (with country code for WhatsApp)",
            value=st.session_state["cust_phone"],
            help="e.g., 919876543210",
            disabled=st.session_state["payment_option"] is not None
        )
        st.session_state["cust_email"] = st.text_input("Customer Email", value=st.session_state["cust_email"], disabled=st.session_state["payment_option"] is not None)
        st.session_state["cust_addr"] = st.text_input("Customer Address", value=st.session_state["cust_addr"], disabled=st.session_state["payment_option"] is not None)

        order_id = get_local_time().strftime("%Y%m%d-%H%M%S")
        
        st.write("---")
        st.subheader("Payment")

        if st.button("Confirm Order"):
            if not st.session_state["cust_name"] or not st.session_state["cust_phone"] or not st.session_state["cust_addr"]:
                st.error("Customer Name, Phone, and Address are required.")
            else:
                st.session_state["payment_option"] = "pending"

        if st.session_state["payment_option"] == "pending":
            payment_options = ["Cash on Pick up", "Online Payment (Card/Netbanking)"]
            if st.session_state.get("show_upi", True):
                payment_options.insert(0, "UPI")
            
            payment_method = st.radio(
                "Select Payment Method",
                payment_options,
            )

            if payment_method == "UPI":
                upi_id = "9259317713@ybl"
                subtotal = st.session_state["total"]
                delivery_charge_rate = float(
                    st.session_state.get("delivery_charge_rate", 0.0)
                )
                gst_rate = float(st.session_state.get("gst_rate", 0.0))
                discount = float(st.session_state["discount"])
                delivery_charge = subtotal * delivery_charge_rate / 100.0
                gst_amount = subtotal * gst_rate / 100.0
                grand_total = subtotal + delivery_charge + gst_amount - discount
                amount = grand_total
                upi_link = f"upi://pay?pa={upi_id}&pn=Dhaliwal's%20Food%20Court&am={amount:.2f}&cu=INR"

                # Generate QR code
                qr_img = qrcode.make(upi_link)

                # Save QR code to a BytesIO object
                buf = BytesIO()
                qr_img.save(buf)

                st.image(buf, width=200)
                st.markdown(
                    f'<a href="{upi_link}" target="_blank">Click here to pay via UPI</a>',
                    unsafe_allow_html=True,
                )

                if st.button("Payment Done"):
                    subtotal = st.session_state["total"]
                    delivery_charge_rate = float(
                        st.session_state.get("delivery_charge_rate", 0.0)
                    )
                    gst_rate = float(st.session_state.get("gst_rate", 0.0))
                    discount = float(st.session_state["discount"])
                    delivery_charge = subtotal * delivery_charge_rate / 100.0
                    gst_amount = subtotal * gst_rate / 100.0
                    grand_total = subtotal + delivery_charge + gst_amount - discount
                    order_id = get_local_time().strftime("%Y%m%d-%H%M%S")
                    save_order_log(order_id, subtotal, delivery_charge, gst_amount, discount, grand_total, "UPI", razorpay_fee=0)
                    st.session_state["payment_option"] = "done"
                    st.session_state["payment_method"] = "UPI"
                    st.session_state["order_finalized_time"] = time.time()
                    st.rerun()

            elif payment_method == "Cash on Pick up":
                if st.button("Confirm Cash on Pick up"):
                    subtotal = st.session_state["total"]
                    delivery_charge_rate = float(
                        st.session_state.get("delivery_charge_rate", 0.0)
                    )
                    gst_rate = float(st.session_state.get("gst_rate", 0.0))
                    discount = float(st.session_state["discount"])
                    delivery_charge = subtotal * delivery_charge_rate / 100.0
                    gst_amount = subtotal * gst_rate / 100.0
                    grand_total = subtotal + delivery_charge + gst_amount - discount
                    order_id = get_local_time().strftime("%Y%m%d-%H%M%S")
                    save_order_log(order_id, subtotal, delivery_charge, gst_amount, discount, grand_total, "Cash on Delivery", razorpay_fee=0)
                    st.session_state["payment_option"] = "cod_confirmed"
                    st.session_state["payment_method"] = "Cash on Delivery"
                    st.session_state["order_finalized_time"] = time.time()
                    st.rerun()

            elif payment_method == "Online Payment (Card/Netbanking)":
                if not razorpay_client:
                    st.error("Razorpay is not configured.")
                else:
                    subtotal = st.session_state["total"]
                    delivery_charge_rate = float(
                        st.session_state.get("delivery_charge_rate", 0.0)
                    )
                    gst_rate = float(st.session_state.get("gst_rate", 0.0))
                    discount = float(st.session_state["discount"])
                    delivery_charge = subtotal * delivery_charge_rate / 100.0
                    gst_amount = subtotal * gst_rate / 100.0
                    razorpay_fee = subtotal * 0.026
                    grand_total = subtotal + delivery_charge + gst_amount - discount + razorpay_fee


                    order_currency = "INR"
                    order_receipt = f"receipt_{order_id}"

                    try:
                        payment_link = razorpay_client.payment_link.create({ # type: ignore
                            "amount": int(grand_total * 100),
                            "currency": "INR",
                            "description": f"Payment for Order {order_id}",
                            "customer": {
                                "name": st.session_state['cust_name'],
                                "email": st.session_state['cust_email'],
                                "contact": st.session_state['cust_phone']
                            },
                        })

                        st.success("Payment link created successfully! After Successful payment click payment done")
                        st.markdown(f'<a href="{payment_link["short_url"]}" target="_blank" style="background-color: #F37254; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">Pay ₹{grand_total:.2f} with Razorpay</a>', unsafe_allow_html=True)

                        if st.button("Payment Done"):
                            subtotal = st.session_state["total"]
                            delivery_charge_rate = float(
                                st.session_state.get("delivery_charge_rate", 0.0)
                            )
                            gst_rate = float(st.session_state.get("gst_rate", 0.0))
                            discount = float(st.session_state["discount"])
                            delivery_charge = subtotal * delivery_charge_rate / 100.0
                            gst_amount = subtotal * gst_rate / 100.0
                            razorpay_fee = subtotal * 0.026
                            grand_total = subtotal + delivery_charge + gst_amount - discount + razorpay_fee
                            order_id = get_local_time().strftime("%Y%m%d-%H%M%S")
                            save_order_log(order_id, subtotal, delivery_charge, gst_amount, discount, grand_total, "Razorpay", razorpay_fee=razorpay_fee)
                            st.session_state["payment_option"] = "done"
                            st.session_state["payment_method"] = "Razorpay"
                            st.session_state["order_finalized_time"] = time.time()
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error creating Razorpay payment link: {e}")
                        if "Authentication failed" in str(e):
                            st.warning(
                                "Authentication failed. Please check if your Razorpay Key ID and Key Secret in `.streamlit/secrets.toml` are correct and belong to your account."
                            )

        if st.session_state["payment_option"] in ["done", "cod_confirmed"]:
            if st.session_state["payment_option"] == "done":
                st.success("We need to confirm your payment please send your payment details like transaction details on what's app. When we get your payment, we will contact you on call for confirmation of your order.")
            elif st.session_state["payment_option"] == "cod_confirmed":
                st.success("Your order has been confirmed for Cash on Pick up.")

            pdf_buffer = build_pdf_receipt(order_id)
            if pdf_buffer:
                st.download_button(
                    label="Download Receipt PDF",
                    data=pdf_buffer.getvalue(),
                    file_name=f"receipt_{order_id}.pdf",
                    mime="application/pdf",
                )

            st.write("---")
            st.subheader("Finalize & Send")

            send_email = st.checkbox("Email PDF to customer", value=bool(st.session_state["cust_email"]))
            send_whatsapp = st.checkbox("Send Order Details to WhatsApp")

            if st.button("Finalize Order (Log + Selected Sends)"):
                subtotal = st.session_state["total"]
                delivery_charge_rate = float(st.session_state.get("delivery_charge_rate", 0.0))
                delivery_charge = subtotal * delivery_charge_rate / 100.0
                gst_rate = float(st.session_state.get("gst_rate", 0.0))
                gst_amount = subtotal * gst_rate / 100.0
                discount = float(st.session_state["discount"])
                razorpay_fee = 0.0
                if st.session_state.get("payment_method") == "Razorpay":
                    razorpay_fee = subtotal * 0.026
                grand_total = subtotal + delivery_charge + gst_amount - discount + razorpay_fee

                st.success(f"Order {order_id} has been saved to the order logs.")

                if pdf_buffer:
                    send_email_to_owner(pdf_buffer.getvalue(), order_id)

                if send_email:
                    if not st.session_state["cust_email"]:
                        st.warning("Customer email is empty — cannot send email.")
                    elif not pdf_buffer:
                        st.warning("Receipt PDF not available — cannot send email.")
                    else:
                        ok_email = send_email_with_pdf(st.session_state["cust_email"], pdf_buffer.getvalue(), order_id)
                        if ok_email:
                            st.success(f"Email sent to {st.session_state['cust_email']}")
                        else:
                            st.warning("Email failed—check SMTP settings.")

                if send_whatsapp:
                    # Send to customer
                    if not st.session_state["cust_phone"]:
                        st.warning("Customer phone is empty — cannot send WhatsApp to customer.")
                    else:
                        st.info("Click the link below to send the order details to the customer via WhatsApp.")
                        send_whatsapp_message(st.session_state["cust_phone"], order_id, subtotal, delivery_charge, gst_amount, grand_total, razorpay_fee)

                    # Send to owner
                    if not st.session_state["owner_phone"]:
                        st.warning("Owner phone is empty — cannot send WhatsApp to owner.")
                    else:
                        st.info("Click the link below to send the order details to the owner via WhatsApp.")
                        send_whatsapp_message(st.session_state["owner_phone"], order_id, subtotal, delivery_charge, gst_amount, grand_total, razorpay_fee)

                if not (send_email or send_whatsapp):
                    st.info("Order logged. Select Email or WhatsApp to send the receipt.")
                    

        st.button("Clear Bill", on_click=clear_bill)

    else:
        st.info("No items added yet.")

st.write("---")
st.subheader("Policy Links")
st.markdown("[Shipping](https://merchant.razorpay.com/policy/Rfv4unI68N8m7V/shipping)")
st.markdown("[Terms and Conditions](https://merchant.razorpay.com/policy/Rfv4unI68N8m7V/terms)")
st.markdown("[Cancellation & Refunds](https://merchant.razorpay.com/policy/Rfv4unI68N8m7V/refund)")

with st.expander("Privacy Policy - Dhaliwals Food Court Unit of Param Mehar Enterprise Prop Pushpinder Singh Dhaliwal"):
    privacy_policy_component("privacy_policy.html")


