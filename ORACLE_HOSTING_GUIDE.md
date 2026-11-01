# 🌊 BeatWave — Oracle Cloud Free Tier Hosting Guide

This step-by-step guide will walk you through hosting **BeatWave** 24/7 on an **Oracle Cloud Infrastructure (OCI) Always Free** VPS instance.

---

## Step 1: Open Ports in Oracle Cloud Dashboard (Important!)

Oracle Cloud blocks incoming ports by default. You must allow HTTP (80) and HTTPS (443):

1. Log into your **[Oracle Cloud Console](https://cloud.oracle.com/)**.
2. Go to: **Networking** ➔ **Virtual Cloud Networks (VCN)**.
3. Click on your VCN ➔ Click on **Security Lists** (e.g. *Default Security List for vcn-*).
4. Click **Add Ingress Rules**:
   - **Source CIDR**: `0.0.0.0/0`
   - **IP Protocol**: `TCP`
   - **Destination Port Range**: `80,443`
   - **Description**: `Allow HTTP and HTTPS`
5. Click **Add Ingress Rules**.

---

## Step 2: Connect to your Oracle VPS

Open your terminal or PowerShell on your computer and connect to your instance:

```bash
ssh -i /path/to/your-private-key.key ubuntu@<YOUR_ORACLE_PUBLIC_IP>
```
*(Replace `<YOUR_ORACLE_PUBLIC_IP>` with your instance's Public IP)*

---

## Step 3: Transfer or Clone BeatWave to the VPS

### Option A (Upload directly from your PC using SCP/rsync):
From your Windows PowerShell in `c:\Users\Rahul Pachute\Downloads\coding\Beatwave`:
```powershell
scp -i path\to\your-key.key -r . ubuntu@<YOUR_ORACLE_PUBLIC_IP>:~/Beatwave
```

### Option B (Using Git):
If your code is pushed to GitHub/GitLab:
```bash
git clone <YOUR_REPO_URL> Beatwave
cd Beatwave
```

---

## Step 4: Run the 1-Click Auto Deploy Script

On your Oracle VPS terminal, enter the directory and run:

```bash
cd ~/Beatwave
chmod +x deploy-oracle.sh
./deploy-oracle.sh
```

### (Optional) Custom Domain
If you have your own domain (e.g. `beatwave.yourdomain.com`), simply point an **A Record** to your Oracle Public IP, and run:
```bash
DOMAIN=beatwave.yourdomain.com ./deploy-oracle.sh
```
*If you don't have a domain, the script automatically uses `<PUBLIC_IP>.nip.io` with a free Let's Encrypt SSL certificate!*

---

## Step 5: Configure Telegram Mini App in @BotFather

Once the script finishes, it will print your live HTTPS URL (e.g. `https://123.45.67.89.nip.io` or `https://beatwave.yourdomain.com`).

1. Open Telegram and message **`@BotFather`**.
2. Type `/mybots` and select your bot (`@BeatWave_app`).
3. Click **Bot Settings** ➔ **Menu Button** ➔ **Configure menu button**.
4. Send your HTTPS URL:
   ```
   https://<YOUR_DOMAIN_OR_NIP_IO>
   ```
5. Enter button title: `🌊 Open BeatWave`

---

## Verification & Management

### View live logs:
```bash
# Check all containers:
sudo docker compose ps

# View Telegram bot logs:
sudo docker compose logs -f bot

# View Backend API logs:
sudo docker compose logs -f backend

# View Caddy SSL & proxy logs:
sudo docker compose logs -f caddy
```

### Restart or update:
```bash
sudo docker compose restart
```
