# send_mail.py
def send_daily_orders_email():
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email.mime.text import MIMEText
    from email import encoders
    import os

    ORDERS_FILE = "orders.csv"

    # FIX: Prevent None values
    sender = os.getenv("SENDER_EMAIL") or ""
    password = os.getenv("SENDER_PASSWORD") or ""
    receiver = os.getenv("OWNER_EMAIL") or ""

    if not sender or not password or not receiver:
        print("ERROR: Missing environment variables.")
        return

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = "Daily Orders Report - Dhaliwal Food Court"

    msg.attach(MIMEText("Attached is the daily consolidated orders.csv report.", "plain"))

    with open(ORDERS_FILE, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", "attachment; filename=orders.csv")
        msg.attach(part)

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender, password)
    server.send_message(msg)
    server.quit()

    print("Email sent successfully!")
# .github/workflows/send_daily_orders.yml
# Place this file under: .github/workflows/send_daily_orders.yml

"""
name: Send Daily Orders Report

on:
  schedule:
    - cron: "0 18 * * *"   # 11:30 PM IST daily
  workflow_dispatch:

jobs:
  send-report:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout repo
      uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.10"

    - name: Install dependencies
      run: |
        pip install pandas

    - name: Send Orders CSV Email
      env:
        SENDER_EMAIL: ${{ secrets.SENDER_EMAIL }}
        SENDER_PASSWORD: ${{ secrets.SENDER_PASSWORD }}
        OWNER_EMAIL: ${{ secrets.OWNER_EMAIL }}
      run: |
        python send_mail.py
"""
