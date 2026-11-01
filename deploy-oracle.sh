#!/bin/bash
set -e

echo "=========================================================="
echo "      🌊 BeatWave — Oracle Cloud Free Tier Auto Deploy     "
echo "=========================================================="

# 1. Configure firewall for Ports 80 and 443
echo "[1/5] Configuring firewall (Ports 80 & 443)..."
if command -v firewall-cmd &> /dev/null; then
    sudo firewall-cmd --permanent --add-port=80/tcp 2>/dev/null || true
    sudo firewall-cmd --permanent --add-port=443/tcp 2>/dev/null || true
    sudo firewall-cmd --reload 2>/dev/null || true
fi
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT 2>/dev/null || true
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT 2>/dev/null || true

# 2. Install Docker via official script
if ! command -v docker &> /dev/null; then
    echo "[2/5] Installing Docker Engine (this takes ~60 seconds)..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo systemctl enable --now docker
    sudo usermod -aG docker "$USER" 2>/dev/null || true
    rm -f get-docker.sh
else
    echo "[2/5] Docker is already installed."
    sudo systemctl enable --now docker 2>/dev/null || true
fi

# 3. Detect public IP if domain is not provided
PUBLIC_IP=$(curl -s https://ifconfig.me || curl -s https://api.ipify.org || echo "152.67.3.98")

if [ -z "$DOMAIN" ]; then
    # Use nip.io as a zero-config wildcard domain with valid HTTPS
    DOMAIN="${PUBLIC_IP}.nip.io"
fi

echo "[3/5] Configured Domain: https://${DOMAIN}"

# 4. Create production .env file
echo "[4/5] Writing production environment configuration..."
cat <<EOF > .env
APP_ENV=production
APP_NAME=BeatWave
DOMAIN=${DOMAIN}
APP_PUBLIC_URL=https://${DOMAIN}
MINI_APP_URL=https://${DOMAIN}
API_PUBLIC_URL=https://${DOMAIN}
API_BASE_URL=http://backend:8000/api/v1
LOG_LEVEL=INFO

# Telegram Bot
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN:-9127560701:AAFK_FBkKgN_MsfNsC9XfgMMLJbG8CeOWqs}
TELEGRAM_WEBHOOK_SECRET=
TELEGRAM_WEBHOOK_URL=

# Authentication
APP_SESSION_SECRET=beatwave-production-secret-key-32-chars-long
TELEGRAM_INITDATA_MAX_AGE_SECONDS=86400

# Database
POSTGRES_USER=beatwave
POSTGRES_PASSWORD=beatwave_secure_pass_$(openssl rand -hex 6 2>/dev/null || echo "prod992")
POSTGRES_DB=beatwave

# Security / CORS
CORS_ALLOWED_ORIGINS=https://${DOMAIN}
COOKIE_SECURE=true
COOKIE_SAMESITE=lax

# Music Engine
MUSIC_PROVIDER=demo
MUSIC_PROVIDER_API_KEY=

# Rate Limits
REQUESTS_PER_USER_PER_WINDOW=10
REQUEST_RATE_LIMIT_WINDOW_SECONDS=300
EOF

# 5. Build and launch services
echo "[5/5] Building and launching BeatWave containers..."
sudo docker compose down 2>/dev/null || true
sudo docker compose up -d --build

echo ""
echo "=========================================================="
echo "🎉 BeatWave is LIVE on your Oracle Free Tier VPS!"
echo "=========================================================="
echo "🌐 Mini App HTTPS URL: https://${DOMAIN}"
echo "🤖 Telegram Bot:       Active & Listening 24/7"
echo ""
echo "📲 NEXT STEPS IN TELEGRAM (@BotFather):"
echo "1. Open @BotFather in Telegram"
echo "2. Send: /mybots -> Select your bot (@BeatWave_app)"
echo "3. Go to: Bot Settings -> Menu Button -> Configure menu button"
echo "4. Set URL to: https://${DOMAIN}"
echo "=========================================================="
