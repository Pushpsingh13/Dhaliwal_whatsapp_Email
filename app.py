# =========================================================
# Dhaliwals Food Court – Pickup Only Ordering App
# Unit of Param Mehar Enterprise
# =========================================================

import os, re, time, base64, urllib.parse, smtplib
import streamlit as st
import pandas as pd
import pytz, qrcode
from datetime import datetime, timezone
from io import BytesIO
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# =========================================================
# BASIC CONFIG
# =========================================================
APP_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(APP_DIR, "Dhaliwal Food court_logo.png")
QR_CODE_APP_PATH = os.path.join(APP_DIR, "QR_Code For App.jpg")
MENU_EXCEL = os.path.join(APP_DIR, "DhalisMenu.xlsx")
ORDERS_DIR = "Orders"
ORDERS_CSV = "orders.csv"

PICKUP_TIME_SLOTS = [
    "Ready in 20–30 minutes",
    "Ready in 30–45 minutes",
    "Ready in 45–60 minutes",
    "Select specific pickup time"
]

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Dhaliwals Food Court – Pickup Only",
    page_icon=LOGO_PATH,
    layout="wide"
)

# =========================================================
# SESSION STATE
# =========================================================
defaults = {
    "bill": [],
    "total": 0.0,
    "cust_name": "",
    "cust_phone": "",
    "cust_email": "",
    "pickup_time": "",
    "gst_rate": 0.0,
    "discount": 0.0,
    "payment_stage": None,
    "payment_method": "",
    "last_activity": time.time(),
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =========================================================
# HELPERS
# =========================================================
def local_time():
    return datetime.now(pytz.timezone("Asia/Kolkata"))

def ensure_dirs():
    os.makedirs(ORDERS_DIR, exist_ok=True)

def load_menu():
    if not os.path.exists(MENU_EXCEL):
        df = pd.DataFrame({
            "Item": ["Veg Biryani"],
            "Half": [80],
            "Full": [150],
            "Image": [""]
        })
        df.to_excel(MENU_EXCEL, index=False)
    return pd.read_excel(MENU_EXCEL)

def add_to_bill(item, price, size, qty):
    for i in st.session_state["bill"]:
        if i["item"] == item and i["size"] == size:
            i["qty"] += qty
            st.session_state["total"] += price * qty
            return
    st.session_state["bill"].append({
        "item": item, "price": price, "size": size, "qty": qty
    })
    st.session_state["total"] += price * qty

def clear_bill():
    for k in defaults:
        st.session_state[k] = defaults[k]

# =========================================================
# HEADER
# =========================================================
col1, col2, col3 = st.columns([1,2,1])
with col1:
    st.image(LOGO_PATH, width=120)
with col2:
    st.markdown("## Dhaliwals Food Court")
    st.markdown("🛍️ **Pickup Only | No Delivery Available**")
    st.markdown("⏰ 10:00 AM – 10:00 PM")
with col3:
    st.image(QR_CODE_APP_PATH, width=120)

st.divider()

# =========================================================
# MENU
# =========================================================
menu_df = load_menu()

st.header("🍴 Menu")

cols = st.columns(3)
for idx, row in menu_df.iterrows():
    with cols[idx % 3]:
        if row["Image"] and os.path.exists(row["Image"]):
            st.image(row["Image"], width=160)
        st.subheader(row["Item"])
        qty = st.number_input(
            "Qty", 1, 10, 1, key=f"qty_{idx}"
        )
        if row["Half"] > 0:
            if st.button(f"Half ₹{row['Half']}", key=f"h_{idx}"):
                add_to_bill(row["Item"], row["Half"], "Half", qty)
        if st.button(f"Full ₹{row['Full']}", key=f"f_{idx}"):
            add_to_bill(row["Item"], row["Full"], "Full", qty)

# =========================================================
# BILL
# =========================================================
st.sidebar.header("🧾 Current Bill")

if st.session_state["bill"]:
    for i, b in enumerate(st.session_state["bill"]):
        st.sidebar.write(
            f"{b['qty']}x {b['item']} ({b['size']}) – ₹{b['price']*b['qty']:.2f}"
        )

    st.sidebar.divider()
    st.sidebar.write(f"**Subtotal:** ₹{st.session_state['total']:.2f}")

    st.session_state["cust_name"] = st.sidebar.text_input("Name")
    st.session_state["cust_phone"] = st.sidebar.text_input("Phone")
    st.session_state["cust_email"] = st.sidebar.text_input("Email")

    st.sidebar.subheader("🕒 Pickup Time")
    choice = st.sidebar.selectbox("Select", PICKUP_TIME_SLOTS)
    if choice == "Select specific pickup time":
        t = st.sidebar.time_input("Pickup Time")
        st.session_state["pickup_time"] = t.strftime("%H:%M")
    else:
        st.session_state["pickup_time"] = choice

    st.sidebar.divider()

    if st.sidebar.button("Confirm Order"):
        st.session_state["payment_stage"] = "pay"

# =========================================================
# PAYMENT
# =========================================================
if st.session_state["payment_stage"] == "pay":
    st.sidebar.subheader("💳 Payment Method")
    method = st.sidebar.radio(
        "Choose",
        ["Cash on Pickup", "UPI"]
    )

    subtotal = st.session_state["total"]
    gst = subtotal * st.session_state["gst_rate"] / 100
    total = subtotal + gst - st.session_state["discount"]

    st.sidebar.write(f"**Total Payable:** ₹{total:.2f}")

    if method == "Cash on Pickup":
        if st.sidebar.button("Confirm Pickup Order"):
            st.session_state["payment_method"] = method
            st.session_state["payment_stage"] = "done"

    if method == "UPI":
        upi_id = "9259317713@ybl"
        upi_link = f"upi://pay?pa={upi_id}&pn=DhaliwalsFoodCourt&am={total:.2f}&cu=INR"
        qr = qrcode.make(upi_link)
        buf = BytesIO()
        qr.save(buf)
        st.sidebar.image(buf, width=200)
        st.sidebar.markdown(f"[Pay via UPI]({upi_link})")
        if st.sidebar.button("Payment Done"):
            st.session_state["payment_method"] = "UPI"
            st.session_state["payment_stage"] = "done"

# =========================================================
# FINALIZE
# =========================================================
if st.session_state["payment_stage"] == "done":
    ensure_dirs()
    order_id = local_time().strftime("%Y%m%d%H%M%S")

    row = {
        "OrderID": order_id,
        "Date": local_time().strftime("%d-%m-%Y %H:%M"),
        "Customer": st.session_state["cust_name"],
        "Phone": st.session_state["cust_phone"],
        "Items": "; ".join(
            [f"{i['qty']}x {i['item']}({i['size']})" for i in st.session_state["bill"]]
        ),
        "OrderType": "Pickup Only",
        "PickupTime": st.session_state["pickup_time"],
        "Payment": st.session_state["payment_method"],
        "Total": total,
    }

    df = pd.DataFrame([row])
    df.to_csv(ORDERS_CSV, mode="a", header=not os.path.exists(ORDERS_CSV), index=False)

    st.success("✅ Order Confirmed!")
    st.write("🛍️ **Pickup Only**")
    st.write(f"🕒 **Pickup Time:** {st.session_state['pickup_time']}")
    st.write(f"💳 **Payment:** {st.session_state['payment_method']}")
    st.write(f"💰 **Total:** ₹{total:.2f}")

    if st.button("New Order"):
        clear_bill()
        st.rerun()
