# 🎸 Guitar Monitor

Get instant phone notifications when vintage guitars are listed on Craigslist. Set up searches by keyword and price range — it checks all major US cities and pings you the moment something new appears.

![Guitar Monitor screenshot](https://i.imgur.com/placeholder.png)

---

## What you'll need

- A Mac or Linux computer (to run the app)
- Python 3.9 or newer
- The free [ntfy app](https://ntfy.sh) on your phone (iOS or Android)

---

## Setup (takes about 5 minutes)

### 1. Download the app

```bash
git clone https://github.com/jkiley129/guitar-monitor.git
cd guitar-monitor
```

### 2. Install dependencies

```bash
python3 -m venv venv
venv/bin/pip install --upgrade pip
venv/bin/pip install Flask Flask-SQLAlchemy APScheduler feedparser python-telegram-bot gunicorn python-dotenv requests pytz
```

### 3. Start the app

```bash
DB_PATH=./data/guitar.db venv/bin/python3 run.py
```

Then open **http://localhost:5000** in your browser.

> The first time you run it, it creates the database automatically. The `data/` folder is where everything gets saved.

---

## Setting up notifications

You'll get a push notification on your phone whenever a new listing is found.

**On your phone:**
1. Download the **ntfy** app — [App Store](https://apps.apple.com/app/ntfy/id1625396347) · [Google Play](https://play.google.com/store/apps/details?id=io.heckel.ntfy)
2. Tap **+** and subscribe to a topic name you make up (e.g. `guitars-yourname-2024`). Make it unique — this is your private channel.

**In Guitar Monitor:**
1. Go to **Settings**
2. Enter your topic name under "Your ntfy topic name"
3. Hit **Save**, then **Send test notification**
4. You should feel your phone buzz within a few seconds ✅

**What a notification looks like:**

```
🎸 Fender Telecaster 1972 - $650
San Francisco Bay  |  Search: Vintage Telecaster
[View on Craigslist →]
```

Tap the notification to open the listing directly.

---

## Creating your first search

1. Go to **Searches → New Search**
2. Fill in:
   - **Name** — just a label, e.g. `Telecaster under $1k`
   - **Keywords** — what to search for, e.g. `fender telecaster vintage`
   - **Min / Max Price** — optional price range
   - **Today only** — leave this checked (avoids getting flooded with old listings)
   - **Cities** — pick which cities to monitor, or leave all checked for nationwide
3. Hit **Save Search**

### Running your first scan

Go to **Settings → Scan now**. It checks every city in your search and shows you exactly what it found:

- ✅ `"Scan complete — no new listings found this time."` — nothing new today yet
- 🎸 `"Found 3 new listings! (3 from Telecaster under $1k) — 3 notifications sent."` — check your phone!

The app automatically re-scans every 15 minutes in the background (you can change this in Settings).

---

## Keeping it running

The app needs to stay running to send notifications. A few options:

### Option A — Run it on a cheap server (best)

A $5/month VPS (like [Hetzner](https://hetzner.com) or [DigitalOcean](https://digitalocean.com)) keeps it running 24/7.

1. SSH into your server and install Docker:
   ```bash
   apt update && apt install -y docker.io docker-compose-plugin
   ```

2. Copy the project to the server:
   ```bash
   scp -r guitar-monitor/ user@your-server:/opt/guitar-monitor
   ```

3. Create a `.env` file:
   ```bash
   cd /opt/guitar-monitor
   cp .env.example .env
   nano .env  # add your SECRET_KEY
   ```

4. Start it:
   ```bash
   docker compose up -d --build
   ```

5. Open `http://your-server-ip:5000` — then go to Settings and add your ntfy topic.

### Option B — Run it on your Mac

Works fine as long as your Mac is on and awake. Just run:

```bash
cd guitar-monitor
DB_PATH=./data/guitar.db venv/bin/python3 run.py
```

---

## Tips

- **"Today only"** on your search is important — without it, the first scan will pull in hundreds of old listings at once
- If you want to monitor **specific cities only**, edit the search and uncheck the ones you don't care about — this makes scans faster
- You can create **multiple searches** for different guitars, price ranges, or cities
- The **Matches** page shows everything found, with a "Dismiss" button to clear listings you've already looked at

---

## Troubleshooting

**Not getting notifications?**
- Go to Settings → Send test notification. If that doesn't work, double-check the topic name matches exactly what you subscribed to in the ntfy app (case-sensitive).

**Scan says "no new listings" every time?**
- Make sure "Today only" is checked on your search — if it's unchecked and you've already scanned once, all historical listings are already in the database.
- Try editing your search and hitting Save, then Scan now again.

**App won't start?**
- Make sure you're using the venv Python: `venv/bin/python3 run.py`, not just `python3 run.py`
- Check that the `data/` folder exists: `mkdir -p data`
