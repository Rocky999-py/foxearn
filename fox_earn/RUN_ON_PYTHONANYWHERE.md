# Deploy on PythonAnywhere

## 1. Upload the project
Open a Bash console on PythonAnywhere and either:
    git clone YOUR_REPO_URL fox_earn
or use the Files tab to upload the fox_earn folder.

## 2. Create virtualenv and install packages
    cd ~/fox_earn
    mkvirtualenv --python=/usr/bin/python3.10 fox_earn_venv
    pip install -r requirements.txt

## 3. Initialize the database
    python scripts/init_db.py

## 4. Create the web app
Web tab -> Add a new web app -> Manual configuration -> Python 3.10

  Source code:       /home/YOUR_USERNAME/fox_earn
  Working directory: /home/YOUR_USERNAME/fox_earn
  Virtualenv:        /home/YOUR_USERNAME/.virtualenvs/fox_earn_venv

## 5. WSGI file
Click the WSGI configuration file link. Delete everything, paste:

    import sys
    path = "/home/YOUR_USERNAME/fox_earn"
    if path not in sys.path:
        sys.path.insert(0, path)
    from app.main import app as application

## 6. Environment variables
Web tab -> Environment variables. Add:

  BOT_TOKEN            = your bot token from @BotFather
  ADMIN_TELEGRAM_IDS   = your numeric Telegram ID
  BOT_USERNAME         = foxxx_con_bot
  FRONTEND_ORIGINS     = https://YOUR_USERNAME.pythonanywhere.com
  DATABASE_URL         = sqlite:////home/YOUR_USERNAME/fox_earn/fox_earn.db
  SESSION_TTL_SECONDS  = 86400
  INITDATA_MAX_AGE_SECONDS = 3600
  MAINTENANCE_MODE     = 0
  DEBUG                = 0

Note the FOUR slashes in DATABASE_URL: sqlite:////home/...

## 7. Enable HTTPS
Web tab -> Security -> Force HTTPS: On.
PythonAnywhere provisions a free Let's Encrypt certificate.

## 8. Reload
Click the green Reload button. Done.

## 9. Point BotFather at it
@BotFather -> /mybots -> your bot -> Bot Settings -> Menu Button
URL: https://YOUR_USERNAME.pythonanywhere.com

## Admin panel
https://YOUR_USERNAME.pythonanywhere.com/admin/

Only opens for Telegram IDs listed in ADMIN_TELEGRAM_IDS.

## Custom domain (optional)
Web tab -> Add a new domain, then set a CNAME from your DNS provider.
Enable a certificate for the custom domain in the same tab.
Update FRONTEND_ORIGINS env var and reload.
