import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


def send_daily_orders_email():
    ORDERS_FILE = "orders.csv"

    print("=== Starting Email Script ===")

    # Always return a string (fixes Pylance errors)
    sender: str = os.getenv("SENDER_EMAIL") or ""
    password: str = os.getenv("SENDER_PASSWORD") or ""
    receiver: str = os.getenv("OWNER_EMAIL") or ""

    print(f"SENDER_EMAIL set? {'YES' if sender else 'NO'}")
    print(f"SENDER_PASSWORD set? {'YES' if password else 'NO'}")
    print(f"OWNER_EMAIL set? {'YES' if receiver else 'NO'}")

    # Validate all secrets
    if not sender or not password or not receiver:
        print("ERROR: Missing required environment variables.")
        return

    # Check file exists
    if not os.path.exists(ORDERS_FILE):
        print(f"ERROR: File not found: {ORDERS_FILE}")
        return

    try:
        print("Preparing email...")

        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = receiver
        msg["Subject"] = "Daily Orders Report - Dhaliwal Food Court"

        msg.attach(MIMEText("Attached is the daily consolidated orders.csv report.", "plain"))

        # Attach file
        with open(ORDERS_FILE, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", 'attachment; filename="orders.csv"')
            msg.attach(part)

        print("Connecting to Gmail SMTP...")
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            print("Logging in...")
            server.login(sender, password)
            print("Sending email...")
            server.send_message(msg)

        print("=== Email sent successfully! ===")

    except Exception as e:
        print("=== ERROR SENDING EMAIL ===")
        print(str(e))


if __name__ == "__main__":
    send_daily_orders_email()
