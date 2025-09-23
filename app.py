import os
import re
import smtplib
import requests
import time
import urllib.parse
import webbrowser
import base64
from io import BytesIO
from datetime import datetime
import pytz
import qrcode
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText

import pandas as pd
import streamlit as st

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
with st.container():
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.image("Dhaliwal Food court_logo.png", width=100)
    with col2:
        st.image("QR_Code For App.jpg", width=100)
        st.write("Scan the QR code For next order minimum order for delivery should be 200₹")
    with col3:
        st.empty()
# =========================
# PAGE CONFIG & STYLING
# =========================
st.set_page_config(page_title="Dhaliwal's Food Court", layout="wide",page_icon="Dhaliwal Food court_logo.png")

img = ""
try:
    with open("Dhaliwal Food Court.png", "rb") as f:
        img = base64.b64encode(f.read()).decode()
except FileNotFoundError:
    pass

st.markdown(
    f"""
<style>
body {{
    font-size: 16px;
    color: White;
}}
.stApp {{
    background-image: url("data:image/png;base64,{img}");
    background-size: cover;
}}
.main {{ background-color: rgba(0, 0, 0, 0.5); padding: 20px; border-radius: 10px;}}

/* Main Title (Home Header) */
.main-title {{
    font-size: 80px;         /* Bigger */
    font-weight: bold;       /* Bold */
    font-style: italic;      /* Italic */
    color: #895129;          /* Bright Brown */
    transform: scale(2);  /* Scale 2x larger */
    margin-bottom: 20px;
    text-shadow: 3px 3px 6px #000000;
    font-family: 'Garamond', serif;
    text-align: center;
}}

hr {{ border: 0; border-top: 1px solid #ddd; margin: 8px 0 16px; }}
</style>
""",
    unsafe_allow_html=True,
)

# =========================
# CONFIG
# =========================
MENU_EXCEL = "DhalisMenu.xlsx"
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
    "tax_rate": 5.0,
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
    if not os.path.exists(ORDERS_CSV):
        df = pd.DataFrame(columns=[
            "Date", "Time", "OrderID", "CustomerName", "Phone", "Email",
            "Address", "Items", "Subtotal", "TaxRate%", "TaxAmount",
            "Discount", "GrandTotal", "PaymentMethod"
        ])
        df.to_csv(ORDERS_CSV, index=False)

def clean_text(txt):
    if not txt:
        return "-"
    return str(txt).replace("\n", " ").replace("\r", " ").encode("ascii", "ignore").decode()


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
    st.session_state.last_activity = time.time()
    st.session_state.order_finalized_time = None
    # Check if item with same size already exists
    for bill_item in st.session_state.bill:
        if bill_item['item'] == item and bill_item['size'] == size:
            bill_item['quantity'] += quantity
            st.session_state.total += float(price) * quantity
            st.rerun()

    st.session_state.bill.append({"item": str(item), "price": float(price), "size": str(size), "quantity": quantity})
    st.session_state.total += float(price) * quantity
    st.rerun()


def clear_bill():
    st.session_state.bill = []
    st.session_state.total = 0.0
    st.session_state.cust_name = ""
    st.session_state.cust_phone = ""
    st.session_state.cust_addr = ""
    st.session_state.cust_email = ""
    st.session_state.payment_option = None
    st.session_state.last_activity = time.time()
    st.session_state.order_finalized_time = None


def build_pdf_receipt(order_id: str) -> BytesIO | None:
    if canvas is None or MM is None:
        st.error("ReportLab is not installed. Please run: pip install reportlab")
        return None

    lines = max(1, len(st.session_state.bill))
    thermal_width = 80 * MM
    thermal_height = (70 + 8 * lines + 40) * MM

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(thermal_width, thermal_height))

    y = thermal_height - 10
    c.drawImage("Dhaliwal Food court_logo.png", 2 * MM, y - 5 * MM, width=20 * MM, height=10 * MM)
    c.drawImage("Dhaliwal Food court_logo.png", thermal_width - 22 * MM, y - 5 * MM, width=20 * MM, height=10 * MM)
    y -= 12
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(thermal_width / 2, y, "Dhaliwal's Food Court")
    y -= 12
    c.setFont("Helvetica", 8)
    c.drawCentredString(thermal_width / 2, y, "Meerut, UP | Ph: +91-9259317713")
    y -= 10
    c.line(0, y, thermal_width, y)

    y -= 12
    now_str = get_local_time().strftime("%d %b %Y %H:%M:%S")
    c.setFont("Helvetica", 8)
    c.drawString(2, y, f"Bill Time: {now_str}")
    y -= 10
    c.drawString(2, y, f"Order ID: {order_id}")
    y -= 10
    c.drawString(2, y, f"Customer: {clean_text(st.session_state.cust_name)}")
    y -= 10
    c.drawString(2, y, f"Phone: {clean_text(st.session_state.cust_phone)}")
    y -= 10
    c.drawString(2, y, f"Email: {clean_text(st.session_state.cust_email)}")
    y -= 10
    c.drawString(2, y, f"Address: {clean_text(st.session_state.cust_addr)}")

    y -= 10
    c.line(0, y, thermal_width, y)
    y -= 12

    c.setFont("Helvetica-Bold", 8)
    c.drawString(2, y, "Item")
    c.drawRightString(thermal_width - 2, y, "Price")

    y -= 10
    c.setFont("Helvetica", 8)
    subtotal = 0.0
    for row in st.session_state.bill:
        item_line = clean_text(f"{row['quantity']}x {row['item']} ({row['size']})")
        price_str = f"₹{row['price'] * row['quantity']:.2f}"
        c.drawString(2, y, item_line[:28])
        c.drawRightString(thermal_width - 2, y, price_str)
        y -= 10
        subtotal += float(row["price"]) * row['quantity']

    tax_rate = float(st.session_state.tax_rate)
    discount = float(st.session_state.discount)
    tax = subtotal * tax_rate / 100.0
    grand_total = subtotal + tax - discount

    c.line(0, y, thermal_width, y)
    y -= 12
    c.setFont("Helvetica-Bold", 8)
    c.drawString(2, y, "Subtotal")
    c.drawRightString(thermal_width - 2, y, f"₹{subtotal:.2f}")
    y -= 10
    c.drawString(2, y, f"Tax ({tax_rate:.1f}%)")
    c.drawRightString(thermal_width - 2, y, f"₹{tax:.2f}")
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


def append_order_to_excel(order_id: str, subtotal: float, tax: float, discount: float, grand_total: float, payment_method: str):
    """Logs order to the daily Excel file AND appends to consolidated orders.csv"""
    ensure_orders_dir()
    path = today_orders_path()
    now = get_local_time()
    row = {
        "Date": now.strftime("%Y-%m-%d"),
        "Time": now.strftime("%H:%M:%S"),
        "OrderID": order_id,
        "CustomerName": st.session_state.cust_name,
        "Phone": st.session_state.cust_phone,
        "Email": st.session_state.cust_email,
        "Address": st.session_state.cust_addr,
        "Items": "; ".join([f"{i['quantity']}x {i['item']}({i['size']})-₹{i['price']:.2f}" for i in st.session_state.bill]),
        "Subtotal": subtotal,
        "TaxRate%": st.session_state.tax_rate,
        "TaxAmount": tax,
        "Discount": discount,
        "GrandTotal": grand_total,
        "PaymentMethod": payment_method,
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
        if os.path.exists(ORDERS_CSV):
            df_csv = pd.read_csv(ORDERS_CSV)
            df_csv = pd.concat([df_csv, pd.DataFrame([row])], ignore_index=True)
        else:
            df_csv = pd.DataFrame([row])
        df_csv.to_csv(ORDERS_CSV, index=False)
    except Exception as e:
        st.warning(f"Could not log order to CSV ({ORDERS_CSV}): {e}")


# ==== Messaging helpers (email + WhatsApp) ====

def send_email_with_pdf(to_email: str, pdf_bytes: bytes, order_id: str) -> bool:
    if not to_email:
        st.error("Customer email is empty.")
        return False
    if not st.session_state.sender_email or not st.session_state.sender_password:
        st.error("Sender email credentials are missing. Configure in Admin → Email Settings.")
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = st.session_state.sender_email
        recipients = [to_email, st.session_state.sender_email]
        msg["To"] = to_email
        msg["Subject"] = f"Your Dhaliwal's Food Court Bill (Order {order_id})"

        body = MIMEText(
            f"Dear {st.session_state.cust_name or 'Customer'},\n\n"
            f"Thanks for your order. Your bill is attached as a PDF.\n\n"
            f"Order ID: {order_id}\n"
            f"Date: {get_local_time().strftime('%d %b %Y %H:%M')}\n\n"
            f"Regards,\nDhaliwal's Food Court",
            "plain",
        )
        msg.attach(body)

        part = MIMEApplication(pdf_bytes, Name=f"receipt_{order_id}.pdf")
        part["Content-Disposition"] = f'attachment; filename="receipt_{order_id}.pdf"'
        msg.attach(part)

        server = smtplib.SMTP(st.session_state.smtp_server, st.session_state.smtp_port, timeout=20)
        server.starttls()
        server.login(st.session_state.sender_email, st.session_state.sender_password)
        server.sendmail(st.session_state.sender_email, recipients, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False


def send_whatsapp_message(to_number_raw: str, order_id: str, subtotal: float, tax: float, grand_total: float) -> bool:
    to_digits = "".join([c for c in str(to_number_raw) if c.isdigit()])
    if not to_digits:
        st.error("Invalid customer phone for WhatsApp.")
        return False

    items_str = "\n".join([
        f"- {i['quantity']}x {i['item']} ({i['size']}): ₹{i['price'] * i['quantity']:.2f}"
        for i in st.session_state.bill
    ])

    customer_name = st.session_state.get("cust_name", "").strip()
    cust_name_str = f"Hello {customer_name},\n\n" if customer_name else ""

    message = (
        f"{cust_name_str}Thank you for your order from Dhaliwal's Food Court!\n\n"
        f"*Order ID:* {order_id}\n"
        f"*Date:* {get_local_time().strftime('%d %b %Y %H:%M')}\n\n"
        f"*Items:*\n{items_str}\n\n"
        f"*Subtotal:* ₹{subtotal:.2f}\n"
        f"*Tax:* ₹{tax:.2f}\n"
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
if st.session_state.get("order_finalized_time") and (time.time() - st.session_state.order_finalized_time > 60):
    clear_bill()
    st.toast("Auto-clearing for next order.")
    time.sleep(1)
    st.rerun()
# 2. After 2 minutes of inactivity before finalizing
elif not st.session_state.get("order_finalized_time") and 'last_activity' in st.session_state and (time.time() - st.session_state.last_activity > 900):
    clear_bill()
    st.toast("Bill cleared due to inactivity.")
    time.sleep(1)
    st.rerun()

ensure_orders_csv_exists()
menu_df = load_menu(st.session_state.uploaded_menu_file)


# Top Header (Dhaliwal's Food Court)
st.markdown('<p class="main-title">Dhaliwal\'s Food Court</p>', unsafe_allow_html=True)

st.markdown("*Date:* " + get_local_time().strftime("%d %b %Y %H:%M"))
st.write("---")

with st.sidebar:
    st.header("Admin Panel")
    password = st.text_input("Enter Admin Password", type="password")

    if password == ADMIN_PASSWORD:
        st.success("Logged in as Admin")

        st.subheader("Upload Menu")
        uploaded_menu_file = st.file_uploader("Upload DhalisMenu.xlsx", type=["xlsx"])
        if uploaded_menu_file is not None:
            st.session_state.uploaded_menu_file = uploaded_menu_file
            st.success("Menu file uploaded.")
            st.rerun()

        st.subheader("Menu Editor")
        edited_df = st.data_editor(menu_df, num_rows="dynamic", use_container_width=True, key="menu_editor")
        if st.button("Save Menu Changes"):
            if save_menu(edited_df):
                st.success("Menu saved successfully!")
                st.rerun()

        st.divider()
        st.subheader("Disable Menu Item")
        if not menu_df.empty:
            disable_item = st.selectbox("Select item to disable", menu_df["Item"])
            if st.button("Disable Selected Item"):
                menu_df2 = menu_df[menu_df["Item"] != disable_item]
                if save_menu(menu_df2):
                    st.success(f"'{disable_item}' removed from menu.")
                    st.rerun()
        else:
            st.info("Menu is empty.")

        st.divider()
        st.subheader("Billing Settings")
        st.session_state.tax_rate = st.number_input("Tax Rate (%)", value=float(st.session_state.tax_rate), step=0.5)
        st.session_state.discount = st.number_input("Discount (₹)", value=float(st.session_state.discount), step=1.0)

        st.divider()
        st.subheader("Owner Settings")
        st.session_state.owner_phone = st.text_input("Owner's WhatsApp Number", value=st.session_state.owner_phone, help="e.g., 919876543210", disabled=True)
        st.divider()
        st.subheader("Email Settings (SMTP)")

        if st.session_state.get("edit_smtp", False):
            # If editing is unlocked, show the form with enabled fields and a save button
            with st.form("smtp_edit_form"):
                st.write("You can now edit the SMTP settings below.")
                st.text_input("SMTP Server", key="smtp_server_input", value=st.session_state.smtp_server)
                st.number_input("SMTP Port", key="smtp_port_input", value=int(st.session_state.smtp_port), step=1)
                st.text_input("Sender Email", key="sender_email_input", value=st.session_state.sender_email)
                st.text_input("Sender Password", key="sender_password_input", value=st.session_state.sender_password, type="password")
                
                save_submitted = st.form_submit_button("Save SMTP Settings")
                if save_submitted:
                    st.session_state.smtp_server = st.session_state.smtp_server_input
                    st.session_state.smtp_port = st.session_state.smtp_port_input
                    st.session_state.sender_email = st.session_state.sender_email_input
                    st.session_state.sender_password = st.session_state.sender_password_input

                    st.session_state.edit_smtp = False
                    st.success("SMTP settings updated for the current session.")
                    st.info("Note: On Streamlit Cloud, these settings will reset when the app restarts. For permanent changes, please update the secrets in your Streamlit Cloud dashboard.")
                    time.sleep(5)
                    st.rerun()
        else:
            # If settings are locked, show disabled fields and the unlock form
            st.text_input("SMTP Server", value=st.session_state.smtp_server, disabled=True)
            st.number_input("SMTP Port", value=int(st.session_state.smtp_port), step=1, disabled=True)
            st.text_input("Sender Email", value=st.session_state.sender_email, disabled=True)
            st.text_input("Sender Password", value="********" if st.session_state.sender_password else "", type="password", disabled=True)

            with st.form("smtp_unlock_form"):
                st.info("To edit SMTP settings, you must unlock them with the admin password.")
                unlock_password = st.text_input("Admin Password", type="password")
                unlock_submitted = st.form_submit_button("Unlock to Edit")

                if unlock_submitted:
                    if unlock_password == ADMIN_PASSWORD:
                        st.session_state.edit_smtp = True
                        st.rerun()
                    elif unlock_password:
                        st.error("Incorrect password.")

        st.divider()
        st.subheader("Orders Export")
        if os.path.exists(ORDERS_CSV):
            with open(ORDERS_CSV, "rb") as f:
                st.download_button("Download All Orders (CSV)", f, file_name="orders.csv")
        else:
            st.info("No orders logged yet.")

        # Download today's Excel log
        today_path = today_orders_path()
        if os.path.exists(today_path):
            with open(today_path, "rb") as f:
                st.download_button("Download Today's Orders (Excel)", f, file_name=os.path.basename(today_path))
        else:
            st.caption("Today's Excel log will appear here after the first order is logged.")

    elif password:
        st.error("Incorrect password")

col1, col2 = st.columns([3, 1], gap="large")

with col1:
    st.header("🍴 Dhaliwal's Food Court Menu")

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
    st.image("QR_Code For App.jpg", width=100)
    st.header("Current Bill")
    if st.session_state.bill:
        for i, bill_item in reversed(list(enumerate(st.session_state.bill))):
            col1, col2, col3 = st.columns([4, 2, 1])
            with col1:
                st.text(f"{bill_item['quantity']}x {bill_item['item']} ({bill_item['size']})")
            with col2:
                st.text(f"₹{bill_item['price'] * bill_item['quantity']:.2f}")
            with col3:
                if st.button("🗑️", key=f"delete_{i}"):
                    st.session_state.last_activity = time.time()
                    removed_item = st.session_state.bill.pop(i)
                    st.session_state.total -= removed_item['price'] * removed_item['quantity']
                    st.rerun()
        
        st.markdown("---")
        st.markdown(f"### Total: ₹{st.session_state.total:.2f}")

        st.session_state.cust_name = st.text_input("Customer Name", value=st.session_state.cust_name, disabled=st.session_state.payment_option is not None)
        st.session_state.cust_phone = st.text_input(
            "Customer Phone (with country code for WhatsApp)",
            value=st.session_state.cust_phone,
            help="e.g., 919876543210",
            disabled=st.session_state.payment_option is not None
        )
        st.session_state.cust_email = st.text_input("Customer Email", value=st.session_state.cust_email, disabled=st.session_state.payment_option is not None)
        st.session_state.cust_addr = st.text_input("Customer Address", value=st.session_state.cust_addr, disabled=st.session_state.payment_option is not None)

        order_id = get_local_time().strftime("%Y%m%d-%H%M%S")
        
        st.write("---")
        st.subheader("Payment")

        if st.button("Confirm Order"):
            st.session_state.payment_option = "pending"

        if st.session_state.payment_option == "pending":
            payment_method = st.radio("Select Payment Method", ["UPI", "Cash on Delivery"])

            if payment_method == "UPI":
                upi_id = "9259317713@ybl"
                subtotal = st.session_state.total
                tax_rate = float(st.session_state.tax_rate)
                discount = float(st.session_state.discount)
                tax = subtotal * tax_rate / 100.0
                grand_total = subtotal + tax - discount
                amount = grand_total
                upi_link = f"upi://pay?pa={upi_id}&pn=Dhaliwal's%20Food%20Court&am={amount:.2f}&cu=INR"
                
                # Generate QR code
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(upi_link)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                
                # Save QR code to a BytesIO object
                buf = BytesIO()
                img.save(buf, format="PNG")
                
                st.image(buf, width=200)
                st.markdown(f'<a href="{upi_link}" target="_blank">Click here to pay with UPI</a>', unsafe_allow_html=True)

                if st.button("Payment Done"):
                    st.session_state.payment_option = "done"
                    st.session_state.payment_method = "UPI"
                    st.rerun()

            elif payment_method == "Cash on Delivery":
                if st.button("Confirm Cash on Delivery"):
                    st.session_state.payment_option = "cod_confirmed"
                    st.session_state.payment_method = "Cash on Delivery"
                    st.rerun()

        if st.session_state.payment_option in ["done", "cod_confirmed"]:
            if st.session_state.payment_option == "done":
                st.success("We need to confirm your payment please send your payment details like transaction details on what's app. When we get your payment, we will contact you on call for confirmation of your order.")
            elif st.session_state.payment_option == "cod_confirmed":
                st.success("Your order has been confirmed for Cash on Delivery.")

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

            send_email = st.checkbox("Email PDF to customer", value=bool(st.session_state.cust_email))
            send_whatsapp = st.checkbox("Send Order Details to WhatsApp")

            if st.button("Finalize Order (Log + Selected Sends)"):
                subtotal = st.session_state.total
                tax = subtotal * float(st.session_state.tax_rate) / 100.0
                discount = float(st.session_state.discount)
                grand_total = subtotal + tax - discount

                append_order_to_excel(order_id, subtotal, tax, discount, grand_total, st.session_state.payment_method)
                st.session_state.order_finalized_time = time.time()
                st.success(f"Order {order_id} has been saved to the order logs.")

                if send_email:
                    if not st.session_state.cust_email:
                        st.warning("Customer email is empty — cannot send email.")
                    elif not pdf_buffer:
                        st.warning("Receipt PDF not available — cannot send email.")
                    else:
                        ok_email = send_email_with_pdf(st.session_state.cust_email, pdf_buffer.getvalue(), order_id)
                        if ok_email:
                            st.success(f"Email sent to {st.session_state.cust_email}")
                        else:
                            st.warning("Email failed—check SMTP settings.")

                if send_whatsapp:
                    # Send to customer
                    if not st.session_state.cust_phone:
                        st.warning("Customer phone is empty — cannot send WhatsApp to customer.")
                    else:
                        st.info("Click the link below to send the order details to the customer via WhatsApp.")
                        send_whatsapp_message(st.session_state.cust_phone, order_id, subtotal, tax, grand_total)

                    # Send to owner
                    if not st.session_state.owner_phone:
                        st.warning("Owner phone is empty — cannot send WhatsApp to owner.")
                    else:
                        st.info("Click the link below to send the order details to the owner via WhatsApp.")
                        send_whatsapp_message(st.session_state.owner_phone, order_id, subtotal, tax, grand_total)

                if not (send_email or send_whatsapp):
                    st.info("Order logged. Select Email or WhatsApp to send the receipt.")

        st.button("Clear Bill", on_click=clear_bill)

    else:
        st.info("No items added yet.")
