import os
import re
import smtplib
import requests
import time
import urllib.parse
import webbrowser
import pyautogui  # pip install pyautogui
from io import BytesIO
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText

import pandas as pd
import streamlit as st
import threading
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

# =========================
# CONFIG
# =========================
MENU_EXCEL = "DhalisMenu.xlsx"
ORDERS_DIR = "Orders"  # daily order logs
ADMIN_PASSWORD = "admin123"  # change after first run

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
    "tax_rate": 18.0,
    "discount": 0.0,
    "smtp_server": DEFAULT_SMTP_SERVER,
    "smtp_port": DEFAULT_SMTP_PORT,
    "sender_email": DEFAULT_SENDER_EMAIL,
    "sender_password": DEFAULT_SENDER_PASSWORD,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.set_page_config(page_title="Dhaliwal's Food Court POS", layout="wide")
st.markdown(
    """
<style>
.main { background: #fffaf0; padding: 20px; }
.title { font-size: 34px; font-weight: 800; color: #2c2c2c; margin-bottom: 6px; }
.menu-card { padding: 15px; border-radius: 12px; background: white; text-align: center; margin-bottom: 12px; box-shadow: 0 2px 6px rgba(0,0,0,0.15); }
hr { border: 0; border-top: 1px solid #ddd; margin: 8px 0 16px; }
</style>
""",
    unsafe_allow_html=True,
)

def clean_text(txt):
    if not txt:
        return "-"
    return str(txt).replace("\n", " ").replace("\r", " ").encode("ascii", "ignore").decode()

def ensure_orders_dir():
    if not os.path.exists(ORDERS_DIR):
        os.makedirs(ORDERS_DIR, exist_ok=True)

def today_orders_path():
    ensure_orders_dir()
    return os.path.join(ORDERS_DIR, f"Orders_{datetime.now().strftime('%Y-%m-%d')}.xlsx")

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

def load_menu():
    try:
        if not os.path.exists(MENU_EXCEL):
            create_default_menu()
        df = pd.read_excel(MENU_EXCEL, engine="openpyxl")
        for col in ["Item", "Half", "Full"]:
            if col not in df.columns:
                raise ValueError("Excel must have 'Item', 'Half', and 'Full' columns")
        if "Image" not in df.columns:
            df["Image"] = ""
        df["Half"] = pd.to_numeric(df["Half"], errors="coerce").fillna(0)
        df["Full"] = pd.to_numeric(df["Full"], errors="coerce").fillna(0)
        df["Item"] = df["Item"].fillna("").astype(str)
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

def add_to_bill(item, price, size):
    st.session_state.bill.append({"item": str(item), "price": float(price), "size": str(size)})
    st.session_state.total += float(price)

def clear_bill():
    st.session_state.bill = []
    st.session_state.total = 0.0
    st.session_state.cust_name = ""
    st.session_state.cust_phone = ""
    st.session_state.cust_addr = ""
    st.session_state.cust_email = ""

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
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(thermal_width / 2, y, "Dhaliwal's Food Court")
    y -= 12
    c.setFont("Helvetica", 8)
    c.drawCentredString(thermal_width / 2, y, "Meerut, UP | Ph: +91-9259317713")
    y -= 10
    c.line(0, y, thermal_width, y)

    y -= 12
    now_str = datetime.now().strftime("%d %b %Y %H:%M:%S")
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
        item_line = clean_text(f"{row['item']} ({row['size']})")
        c.drawString(2, y, item_line[:28])
        c.drawRightString(thermal_width - 2, y, f"₹{row['price']:.2f}")
        y -= 10
        subtotal += float(row["price"])

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
        msg["To"] = to_email
        msg["Subject"] = f"Your Dhaliwal's Food Court Bill (Order {order_id})"

        body = MIMEText(
            f"Dear {st.session_state.cust_name or 'Customer'},\n\n"
            f"Thanks for your order. Your bill is attached as a PDF.\n\n"
            f"Order ID: {order_id}\n"
            f"Date: {datetime.now().strftime('%d %b %Y %H:%M')}\n\n"
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
        server.sendmail(st.session_state.sender_email, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False

# =========================
# NEW WHATSAPP FUNCTION
# =========================
def send_whatsapp_message(to_number_raw: str, order_id: str, grand_total: float) -> bool:
    to_digits = only_digits(to_number_raw)
    if not to_digits:
        st.error("Invalid customer phone for WhatsApp.")
        return False

    items_str = "\n".join([f"- {i['item']} ({i['size']}): ₹{i['price']:.2f}" for i in st.session_state.bill])
    message = (
        f"Thank you for your order from Dhaliwal's Food Court!\n\n"
        f"*Order ID:* {order_id}\n"
        f"*Date:* {datetime.now().strftime('%d %b %Y %H:%M')}\n\n"
        f"*Items:*\n{items_str}\n\n"
        f"*subtotal:*\n{subtotal}\n\n"
        f"*Tax:*\n{tax}\n\n"
        f"*Grand Total:* ₹{grand_total:.2f}\n\n"
        f"We hope you enjoy your meal!"
    )

    try:
        url = f"https://web.whatsapp.com/send?phone={to_digits}&text={urllib.parse.quote(message)}"
        webbrowser.open(url)
        time.sleep(10)  # wait for WhatsApp Web to load
        pyautogui.press("enter")
        return True
    except Exception as e:
        st.error(f"WhatsApp send error: {e}")
        return False

def append_order_to_excel(order_id: str, subtotal: float, tax: float, discount: float, grand_total: float):
    ensure_orders_dir()
    path = today_orders_path()
    row = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "OrderID": order_id,
        "CustomerName": st.session_state.cust_name,
        "Phone": st.session_state.cust_phone,
        "Email": st.session_state.cust_email,
        "Address": st.session_state.cust_addr,
        "Items": "; ".join([f"{i['item']}({i['size']})-₹{i['price']:.2f}" for i in st.session_state.bill]),
        "Subtotal": subtotal,
        "TaxRate%": st.session_state.tax_rate,
        "TaxAmount": tax,
        "Discount": discount,
        "GrandTotal": grand_total,
    }

    try:
        if os.path.exists(path):
            df = pd.read_excel(path, engine="openpyxl")
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        else:
            df = pd.DataFrame([row])
        df.to_excel(path, index=False, engine="openpyxl")
    except Exception as e:
        st.warning(f"Could not log order to Excel ({path}): {e}")

menu_df = load_menu()
st.markdown('<p class="title">Dhaliwal\'s Food Court POS</p>', unsafe_allow_html=True)
st.markdown("*Date:* " + datetime.now().strftime("%d %b %Y %H:%M"))
st.write("---")

with st.sidebar:
    st.header("Admin Panel")
    password = st.text_input("Enter Admin Password", type="password")

    if password == ADMIN_PASSWORD:
        st.success("Logged in as Admin")

        st.subheader("Menu Editor")
        edited_df = st.data_editor(menu_df, num_rows="dynamic", use_container_width=True, key="menu_editor")
        if st.button("Save Menu Changes"):
            if save_menu(edited_df):
                st.success("Menu saved successfully!")
                st.rerun()

        st.divider()
        st.subheader("Delete Menu Item")
        if not menu_df.empty:
            delete_item = st.selectbox("Select item to delete", menu_df["Item"])
            if st.button("Delete Selected Item"):
                menu_df2 = menu_df[menu_df["Item"] != delete_item]
                if save_menu(menu_df2):
                    st.success(f"'{delete_item}' removed from menu.")
                    st.rerun()
        else:
            st.info("Menu is empty.")

        st.divider()
        st.subheader("Billing Settings")
        st.session_state.tax_rate = st.number_input("Tax Rate (%)", value=float(st.session_state.tax_rate), step=0.5)
        st.session_state.discount = st.number_input("Discount (₹)", value=float(st.session_state.discount), step=1.0)

        st.divider()
        st.subheader("Email Settings (SMTP)")
        st.session_state.smtp_server = st.text_input("SMTP Server", value=st.session_state.smtp_server)
        st.session_state.smtp_port = st.number_input("SMTP Port", value=int(st.session_state.smtp_port), step=1)
        st.session_state.sender_email = st.text_input("Sender Email", value=st.session_state.sender_email)
        st.session_state.sender_password = st.text_input("Sender Password / App Password", type="password", value=st.session_state.sender_password)

        st.caption(
            "Tip: Use `.streamlit/secrets.toml` for security:\n"
            'SMTP_SERVER="smtp.gmail.com"\nSMTP_PORT="587"\nSENDER_EMAIL="your@gmail.com"\nSENDER_PASSWORD="your-app-password"'
        )

    elif password:
        st.error("Incorrect password")

col1, col2 = st.columns([2, 1], gap="large")

with col1:
    st.header("Menu")
    if not menu_df.empty:
        num_columns = 3
        cols = st.columns(num_columns)
        for idx in menu_df.index:
            row = menu_df.loc[idx]
            with cols[idx % num_columns]:
                image_path = row["Image"] if "Image" in row and pd.notna(row["Image"]) and str(row["Image"]).strip() else None
                if image_path and os.path.exists(image_path):
                    st.image(image_path, use_column_width=True)

                st.markdown(f'<h4>{row["Item"]}</h4>', unsafe_allow_html=True)

                half = float(row.get("Half", 0))
                full = float(row.get("Full", 0))
                if half > 0:
                    if st.button(f"Half - ₹{half:.2f}", key=f"half_{idx}"):
                        add_to_bill(row["Item"], half, "Half")
                if full > 0:
                    if st.button(f"Full - ₹{full:.2f}", key=f"full_{idx}"):
                        add_to_bill(row["Item"], full, "Full")
    else:
        st.warning("Menu is empty. Please add items via Admin Panel.")

with col2:
    st.header("Current Bill")
    if st.session_state.bill:
        bill_df = pd.DataFrame(st.session_state.bill)
        st.dataframe(bill_df, use_container_width=True)
        st.markdown(f"### Total: ₹{st.session_state.total:.2f}")

        st.session_state.cust_name = st.text_input("Customer Name", value=st.session_state.cust_name)
        st.session_state.cust_phone = st.text_input("Customer Phone (with country code for WhatsApp)", value=st.session_state.cust_phone, help="e.g., 919876543210")
        st.session_state.cust_email = st.text_input("Customer Email", value=st.session_state.cust_email)
        st.session_state.cust_addr = st.text_area("Customer Address", value=st.session_state.cust_addr)

        order_id = datetime.now().strftime("%Y%m%d-%H")
        order_id = datetime.now().strftime("%Y%m%d-%H%M%S")
        pdf_buffer = build_pdf_receipt(order_id)

        # Download receipt
        if pdf_buffer:
            st.download_button(
                label="Download Receipt PDF",
                data=pdf_buffer.getvalue(),
                file_name=f"receipt_{order_id}.pdf",
                mime="application/pdf",
            )

        # Finalize order (log + email + WhatsApp)
        st.write("---")
        st.subheader("Finalize & Send")

        send_email = st.checkbox("Email PDF to customer", value=bool(st.session_state.cust_email))
        send_whatsapp = st.checkbox("Send Order Details to WhatsApp")

        if st.button("Finalize Order (Log + Selected Sends)"):
            # Compute totals
            subtotal = sum(float(i["price"]) for i in st.session_state.bill)
            tax = subtotal * float(st.session_state.tax_rate) / 100.0
            discount = float(st.session_state.discount)
            grand_total = subtotal + tax - discount

            # Log order
            append_order_to_excel(order_id, subtotal, tax, discount, grand_total)
            st.success(f"Order {order_id} logged.")

            # Email
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

            # WhatsApp
            if send_whatsapp:
                if not st.session_state.cust_phone:
                    st.warning("Customer phone is empty — cannot send WhatsApp.")
                else:
                    # Inform user about the browser requirement
                    st.info(
                        "WhatsApp Web will open in your default browser. "
                        "Make sure you are logged into WhatsApp Web on that browser. "
                        "If running the Streamlit app on a remote server, WhatsApp Web must be accessible from that machine."
                    )
                    ok_wa = send_whatsapp_message(st.session_state.cust_phone, order_id, grand_total)
                    if ok_wa:
                        st.success(f"WhatsApp message opened for {only_digits(st.session_state.cust_phone)}")
                    else:
                        st.warning("WhatsApp send failed — check phone number and ensure WhatsApp Web is logged in.")

            if not (send_email or send_whatsapp):
                st.info("Order logged. Select Email or WhatsApp to send the receipt.")

        # Clear
        if st.button("Clear Bill"):
            clear_bill()
            st.rerun()
    else:
        st.info("No items added yet.")
        
        # --- AUTO OPEN BROWSER (Only once) ---
import streamlit as st
import webbrowser
import threading

import subprocess
import webbrowser
import requests
import time
import sys
import os

# Path to your Streamlit app
script_path = os.path.join(os.getcwd(), "app.py")  # replace with your file name

# Start Streamlit in a subprocess
process = subprocess.Popen([sys.executable, "-m", "streamlit", "run", script_path],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)

# Streamlit default URL
url = "http://localhost:8501"

# Wait until the Streamlit server is up
while True:
    try:
        response = requests.get(url)
        if response.status_code == 200:
            break
    except requests.exceptions.ConnectionError:
        pass
    time.sleep(1)  # check every second



# Optional: wait for the Streamlit process to exit
process.wait()

    # Prevents it from running repeatedly on refresh

# =========================
# NOTE / USAGE
# =========================
# 1) This script uses pyautogui + webbrowser to open WhatsApp Web and send a prefilled message.
#    Install dependencies:
#       pip install streamlit pandas openpyxl reportlab pyautogui
#
# 2) Important operational notes:
#    - pyautogui simulates keyboard input on the machine where this script runs.
#      If you run Streamlit on a headless/remote server, pyautogui may not be able to interact with a desktop browser.
#      For local deployments (your PC), this approach works well: it opens WhatsApp Web in your default browser and
#      presses Enter to send the prefilled message.
#    - If you need server-side, reliable messaging without a local browser, consider using Twilio's WhatsApp API
#      (requires account and API credentials). I can help integrate that if you prefer.
#
# 3) Launch:
#       streamlit run pos_app.py
#
# That's it — WhatsApp sending is now implemented without pywhatkit.