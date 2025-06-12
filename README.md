# Slide Room Manager

A web application for managing and displaying slides across multiple rooms. Features include:

- Create and manage multiple rooms
- Upload slides (images and PDFs)
- Share slides between rooms
- QR codes for easy room access
- User authentication for room management
- Public view access for rooms

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. **Run with Docker Compose** (requires Docker):
```bash
docker compose up -d
```
This command builds the image and starts the container. Named volumes `uploads` and `rooms` ensure files in `static/uploads` and `rooms.json` persist between container restarts.

## Default Credentials

- Username: admin
- Password: admin123

An `users.db` SQLite database is created automatically on first run with these credentials.

## Environment Variables

- `PORT`: Server port (default: 5006)
- `HOST`: Server host (default: 0.0.0.0)

## Directory Structure

- `/static/uploads/`: Uploaded slides
- `/templates/`: HTML templates
- `app.py`: Main application file
- `rooms.json`: Room data storage
- `users.db`: User credential database (created on first run)

## Testing

Run the test suite with [pytest](https://pytest.org/):

```bash
pytest
```

This command discovers and executes all tests in the `tests/` directory.

## Deployment

### Option 1: Deploy to Render.com (Recommended)

1. Create a new account on [Render.com](https://render.com)
2. Create a new Web Service
3. Connect your GitHub repository
4. Use the following settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Environment Variables:
     - `PORT`: 8000
     - `HOST`: 0.0.0.0

### Option 2: Deploy to VPS (Advanced)

1. SSH into your server
2. Install required packages:
   ```bash
   sudo apt update
   sudo apt install python3-venv nginx certbot python3-certbot-nginx
   ```
3. Clone the repository
4. Set up virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
5. Copy nginx.conf to /etc/nginx/sites-available/
6. Set up SSL with certbot:
   ```bash
   sudo certbot --nginx -d yourdomain.com
   ```
7. Start the application:
   ```bash
   sudo systemctl start slideroom
   sudo systemctl enable slideroom
   ```

The application will be available at https://yourdomain.com

### Option 3: Deploy to AWS EC2

1. **Set up AWS Account and EC2 Instance**:
   - Create an AWS account if you don't have one
   - Launch an EC2 instance (t2.micro is free tier eligible)
   - Choose Ubuntu Server 22.04 LTS
   - Create or select a key pair for SSH access
   - Configure Security Group to allow:
     - HTTP (port 80)
     - HTTPS (port 443)
     - SSH (port 22)

2. **Connect to Your Instance**:
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-public-dns
   ```

3. **Install Required Software**:
   ```bash
   sudo apt update
   sudo apt install -y python3-venv python3-pip nginx certbot python3-certbot-nginx
   ```

4. **Clone and Set Up Application**:
   ```bash
   git clone your-repository
   cd your-repository
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

5. **Set Up Nginx**:
   ```bash
   sudo nano /etc/nginx/sites-available/slideroom
   ```
   Paste the contents of nginx.conf and update the domain
   ```bash
   sudo ln -s /etc/nginx/sites-available/slideroom /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

6. **Set Up SSL with Let's Encrypt**:
   ```bash
   sudo certbot --nginx -d yourdomain.com
   ```

7. **Create Systemd Service**:
   ```bash
   sudo nano /etc/systemd/system/slideroom.service
   ```
   Paste the contents of slideroom.service and update paths
   ```bash
   sudo systemctl start slideroom
   sudo systemctl enable slideroom
   ```

8. **Set Up Domain (Optional)**:
   - Use Route 53 or your domain registrar
   - Create an A record pointing to your EC2 public IP

9. **Monitor Logs**:
   ```bash
   sudo journalctl -u slideroom.service
   ```

The application will be available at your EC2 public IP or domain
