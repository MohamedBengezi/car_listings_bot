import requests
from bs4 import BeautifulSoup
import json
import time
import schedule
import logging
import urllib.parse
from requests.adapters import HTTPAdapter, Retry
# ==========================
# CONFIGURATION
# ==========================
CARS = [
    {"year": 2018, "make": "bmw", "model": "m4", "max_mileage": 100000},
    {"year": 2018, "make": "bmw", "model": "m3", "max_mileage": 100000},
    {"year": 2018, "make": "bmw", "model": "x5%20m", "max_mileage": 100000},
    {"year": 2018, "make": "bmw", "model": "x6%20m", "max_mileage": 100000},
    {"year": 2018, "make": "bmw", "model": "x3%20m", "max_mileage": 100000},

]

BASE_URL = "https://www.autotrader.ca/cars/{make}/{model}/on/?rcp=100&rcs=0&srt=9&yRng={year}%2C&pRng=%2C70000&oRng=%2C{max_mileage}&prx=-2&prv=Ontario&loc=L9C%207R1&hprc=True&wcp=True&sts=New-Used&inMarket=advancedSearch"

SEEN_LISTINGS_FILE = "seen_listings.json"

# ==========================
# TELEGRAM NOTIFICATIONS
# ==========================
TELEGRAM_BOT_TOKEN = "BOT:TOKEN"
TELEGRAM_CHAT_ID = "-1002252818877"


# Create a persistent session with retries
session = requests.Session()
retries = Retry(total=5, backoff_factor=1,
                status_forcelist=[500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retries)
session.mount('https://', adapter)


def send_telegram_message(message):
    """Send a message to Telegram using a persistent session with retries."""
    encoded_message = urllib.parse.quote(message)
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={encoded_message}"
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        print("Telegram message sent successfully.")
    except Exception as e:
        print("Error sending Telegram message:", e)


def load_seen_listings():
    """Load seen listing IDs from file."""
    try:
        with open(SEEN_LISTINGS_FILE, 'r') as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def save_seen_listings(seen):
    """Save seen listing IDs to file."""
    with open(SEEN_LISTINGS_FILE, 'w') as f:
        json.dump(list(seen), f)


def scrape_autotrader():
    """Scrape AutoTrader.ca and check for new listings for multiple cars."""
    print("Checking AutoTrader.ca for new listings...")
    seen = load_seen_listings()

    for car in CARS:
        search_url = BASE_URL.format(
            make=car["make"], model=car["model"], year=car["year"], max_mileage=car["max_mileage"]
        )

        print(
            f"Searching for {car['year']} {car['make']} {car['model']} under {car['max_mileage']} km")

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
            }
            response = requests.get(search_url, headers=headers)
            response.raise_for_status()
        except Exception as e:
            print("Request error:", e)
            continue

        soup = BeautifulSoup(response.content, "html.parser")
        listings = soup.find_all("div", class_="result-item")
        new_listings = []

        for listing in listings:
            listing_id = listing.get(
                "data-listing-id") or listing.find("a", href=True)["href"]
            if listing_id and listing_id not in seen:
                seen.add(listing_id)
                title_tag = listing.find("span", class_="title-with-trim")
                title = title_tag.text.strip() if title_tag else "No title"
                price = listing.find("div", class_="price").text.strip() if listing.find("div", class_="price") else "No price"
                link_tag = listing.find("a", href=True)
                link = link_tag["href"] if link_tag else ""
                if link.startswith("/"):
                    link = "https://www.autotrader.ca" + link

                new_listings.append(f"{title} - {price}\nLink: {link}")

        if new_listings:
            message = f"🚗 **New AutoTrader Listings Found for {car['year']} {car['make']} {car['model']}!**\n\n" + \
                "\n\n".join(new_listings)
            print(message)
            send_telegram_message(message)
        else:
            print(f"No new listings found for {car['year']} {car['make']} {car['model']}.")

    save_seen_listings(seen)
    """Scrape AutoTrader.ca and check for new listings for multiple cars."""
    print("Checking AutoTrader.ca for new listings...")
    seen = load_seen_listings()

    for car in CARS:
        search_url = BASE_URL.format(
            make=car["make"], model=car["model"], year=car["year"], max_mileage=car["max_mileage"]
        )

        print(
            f"Searching for {car['year']} {car['make']} {car['model']} under {car['max_mileage']} km")

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
            }
            response = requests.get(search_url, headers=headers)
            response.raise_for_status()
        except Exception as e:
            print("Request error:", e)
            continue

        soup = BeautifulSoup(response.content, "html.parser")
        listings = soup.find_all("div", class_="result-item")
        new_listings = []

        for listing in listings:
            listing_id = listing.get(
                "data-listing-id") or listing.find("a", href=True)["href"]
            if listing_id and listing_id not in seen:
                seen.add(listing_id)
                title = listing.find("h2", class_="title").text.strip(
                ) if listing.find("h2", class_="title") else "No title"
                price = listing.find("div", class_="price").text.strip(
                ) if listing.find("div", class_="price") else "No price"
                link_tag = listing.find("a", href=True)
                link = link_tag["href"] if link_tag else ""
                if link.startswith("/"):
                    link = "https://www.autotrader.ca" + link

                # Convert price to a number and check if it's below $70,000
                price_value = int(price.replace("$", "").replace(",", "").strip())
                if price_value <= 70000:
                    new_listings.append(f"{title} - {price}\nLink: {link}")


                new_listings.append(f"{title} - {price}\nLink: {link}")

        if new_listings:
            message = f"🚗 **New AutoTrader Listings Found for {car['year']} {car['make']} {car['model']}!**\n\n" + \
                "\n\n".join(new_listings)
            print(message)
            send_telegram_message(message)
        else:
            print(f"No new listings found for {car['year']} {car['make']} {car['model']}.")

    save_seen_listings(seen)


# ==========================
# SCHEDULE THE JOB
# ==========================
scrape_autotrader()
schedule.every(1).hours.do(scrape_autotrader)

print("Starting AutoTrader.ca scraper. Press Ctrl+C to exit.")
while True:
    schedule.run_pending()
    time.sleep(60)