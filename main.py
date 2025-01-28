import os
import requests
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import time

from dotenv import load_dotenv
load_dotenv()


# ========== CONFIGURATIONS ==========

CHECK_INTERVAL = 60  # seconds to wait between checks

PRICE_DIFF_TRIGGER   = 0.1  # Alert if price changes by >= $1 from last_price

# ========== UTILITY FUNCTIONS ==========

def get_xrp_price():
    """
    Fetch the current XRP price in USD using CoinGecko's public API.
    The CoinGecko ID for XRP is 'ripple'.
    """
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "ripple",    # CoinGecko ID for XRP
        "vs_currencies": "usd"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    return data["ripple"]["usd"]

def send_alert_email(subject, content):
    """
    Send an alert email via SendGrid.
    Make sure to set your environment variables for SendGrid credentials and emails:
      - SENDGRID_API_KEY
      - FROM_EMAIL
      - TO_EMAIL
    """
    sendgrid_api_key = os.environ.get("SENDGRID_API_KEY")
    from_email       = os.environ.get("FROM_EMAIL")
    to_email         = os.environ.get("TO_EMAIL")

    if not all([sendgrid_api_key, from_email, to_email]):
        print("Missing SendGrid credentials or email info in environment variables.")
        return

    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        plain_text_content=content
    )

    try:
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        print(f"Email alert sent! Status Code: {response.status_code}")
    except Exception as e:
        print(f"Error sending email via SendGrid: {e}")

# ========== MAIN SCRIPT ==========

def main():
    print("Starting XRP price monitor...")

    last_price = None

    while True:
        try:
            current_price = get_xrp_price()
        except Exception as e:
            print(f"Error fetching XRP price: {e}")
            time.sleep(CHECK_INTERVAL)
            continue

        if last_price is not None:
            # 1) Check if the absolute difference is >= 1 dollar
            if abs(current_price - last_price) >= PRICE_DIFF_TRIGGER:
                subject = f"XRP Price Changed by ${PRICE_DIFF_TRIGGER}+"
                body = (
                    f"Previous price: ${last_price:.2f}\n"
                    f"Current price:  ${current_price:.2f}\n"
                    f"Difference is ${abs(current_price - last_price):.2f}, which is >= ${PRICE_DIFF_TRIGGER}.\n"
                )
                send_alert_email(subject, body)

        # Update last_price for next loop
        last_price = current_price

        print(f"[INFO] Current XRP price: ${current_price:.3f}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
