# Deployment Guide: Development Server & CI/CD

This guide explains how to deploy **YouTube Uploader Pro** to your Linux VPS (Ubuntu/Debian) using Docker Compose and automated GitHub Actions.

---

## 1. Prerequisites on your Linux VPS

Ensure Docker and Docker Compose are installed on your server:

```bash
# Update packages
sudo apt update && sudo apt upgrade -y

# Install Docker & Docker Compose plugin
sudo apt install -y curl git docker.io docker-compose-v2

# Start and enable Docker service
sudo systemctl enable --now docker

# (Optional) Add your user to the docker group so you don't need sudo:
sudo usermod -aG docker $USER
newgrp docker
```

---

## 2. Initial Server Setup (One-Time)

SSH into your development server and clone the repository:

```bash
cd ~
git clone https://github.com/parkkyonghun0510/u-uploader-pro.git
cd u-uploader-pro
```

### Configure Environment Variables
Copy `.env.example` to `.env` and fill in your secrets:

```bash
cp .env.example .env
nano .env
```

Ensure your `.env` contains:
```env
SECRET_KEY=your-secure-secret-key-here
FLASK_ENV=production
FLASK_DEBUG=0
PORT=8080

# Supabase configuration (if using remote sync)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key
```

### Build & Start the Container
```bash
docker compose build
docker compose up -d
```

Verify the service is running:
```bash
docker compose ps
docker compose logs -f
```

You can now access the web dashboard at `http://<YOUR_SERVER_IP>:8080`.

---

## 3. Persistent Data & YouTube Login

The container mounts the following directories from the host:
- `./profiles`: Channel Firefox profiles and saved YouTube session cookies
- `./profile`: Default profile directory
- `./logs`: Application logs
- `./queue`: Local upload queue data

### Handling YouTube Sign-in on a Remote Headless VPS

To sign in a YouTube channel and save session cookies:

#### Option A: Copying an Existing Logged-in Profile from Local (Recommended)
If you already completed the sign-in on your local machine:
```bash
# From your local machine, copy the profile folder to the server:
scp -r ./profiles/<channel_name> user@<server_ip>:~/u-uploader-pro/profiles/
```

#### Option B: Interactive Login inside Container via Xvfb + VNC (or local port forward)
Alternatively, you can run the login command inside the container:
```bash
docker compose exec uploader python upload.py --login --profile channel_1
```

---

## 4. Setting up Automated GitHub Actions CI/CD

When you push code to `main`, GitHub Actions will test your code and automatically deploy to your VPS via SSH.

### Step 1: Generate an SSH Key Pair for GitHub Actions
On your local machine or server:
```bash
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_deploy
```

Add the public key (`~/.ssh/github_deploy.pub`) to your server's `~/.ssh/authorized_keys`:
```bash
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### Step 2: Add Secrets to your GitHub Repository
Go to your GitHub repository:
**Settings > Secrets and variables > Actions > New repository secret**

Add the following repository secrets:

| Secret Name | Value Example | Description |
|---|---|---|
| `VPS_HOST` | `192.0.2.1` or `dev.yourdomain.com` | IP address or hostname of your VPS |
| `VPS_USERNAME` | `ubuntu` or `root` | SSH user |
| `VPS_SSH_KEY` | *(Contents of `github_deploy` private key)* | Private SSH key |
| `VPS_PORT` | `22` | SSH port (default is 22) |
| `VPS_TARGET_DIR` | `/home/ubuntu/u-uploader-pro` | Path to the cloned repository on the VPS |
| `VPS_SSH_PASSPHRASE` | *(Optional)* | Passphrase if your SSH key has one |

---

## 5. Maintenance Commands

```bash
# View live application logs
docker compose logs -f uploader

# Restart services
docker compose restart

# Stop services
docker compose down

# Check container health and resource usage
docker stats
```

---

## 6. Deploying via Coolify (Self-Hosted PaaS)

If you prefer a web-based dashboard like Vercel/Render with automated SSL certificates, automatic Git deployments, and custom domain routing, you can run **Coolify** on your server.

### Step 1: Install Coolify on your VPS / Oracle Cloud VM

Connect to your server via SSH and execute the official installer:

```bash
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
```

> **Important for Oracle Cloud Instances:**
> Ensure incoming traffic on ports `80`, `443`, and `8000` is permitted in both:
> 1. The Oracle Cloud Console (VCN Security List / Ingress Rules).
> 2. The host firewall:
>    ```bash
>    sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
>    sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
>    sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT
>    sudo netfilter-persistent save
>    ```

Once installation finishes, visit `http://<YOUR_SERVER_IP>:8000` to set up your Coolify admin account.

### Step 2: Create a New Project in Coolify

1. Go to **Projects** > **+ Add Resource** > **Public / Private Git Repository**.
2. Enter your repository URL: `https://github.com/parkkyonghun0510/u-uploader-pro.git` (or your private repo).
3. Select **Branch**: `main`.
4. Select **Build Pack**: **Docker Compose** (recommended) or **Dockerfile**.

### Step 3: Configure Network and Port

- **Port Exposes**: Set to `8080`.
- **Domain**: Provide your custom domain or subdomain (e.g., `https://uploader.yourdomain.com`). Coolify will automatically provision a free Let's Encrypt SSL certificate and proxy traffic to port `8080`.

### Step 4: Configure Persistent Storage

In your Coolify application settings, go to **Storages** / **Persistent Volumes** and ensure the following mounts exist so that your YouTube authentication cookies and queue state persist across rebuilds:

- `profiles` -> `/app/profiles`
- `profile` -> `/app/profile`
- `logs` -> `/app/logs`
- `queue` -> `/app/queue`

*(If using the Docker Compose build pack, Coolify will detect the volumes defined in `docker-compose.yml` automatically).*

### Step 5: Environment Variables

Under the **Environment Variables** tab, define:
```env
PORT=8080
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=your-secure-random-secret
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key
```

### Step 6: Deploy

Click **Deploy**. Coolify will build the multi-architecture image (supporting both AMD64 and ARM64 / Ampere A1), start the container with persistent volumes, and launch the service with live logs.

