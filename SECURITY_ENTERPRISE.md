# Entobot Enterprise Security Hardening Guide

## Production Security Checklist

### Pre-Deployment Security

#### 1. Authentication & Authorization

- [ ] **Generate Strong JWT Secret**
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(64))"
  # Min 64 characters, store in environment variable
  ```

- [ ] **JWT Configuration**
  ```json
  {
    "auth": {
      "jwt_secret": "${JWT_SECRET}",
      "jwt_algorithm": "HS256",
      "jwt_expiry_hours": 24,
      "jwt_refresh_enabled": true
    }
  }
  ```

- [ ] **Enable IP Whitelist (if applicable)**
  ```json
  {
    "enterprise": {
      "ip_whitelist": ["10.0.0.0/8", "192.168.1.0/24"]
    }
  }
  ```

- [ ] **Rate Limiting**
  ```json
  {
    "enterprise": {
      "rate_limit_enabled": true,
      "rate_limit_requests": 60,
      "rate_limit_window_seconds": 60
    }
  }
  ```

#### 2. TLS/SSL Configuration

- [ ] **Obtain SSL Certificate**
  ```bash
  # Option A: Let's Encrypt (free)
  sudo certbot certonly --standalone -d entobot.yourcompany.com
  
  # Option B: Corporate CA
  # Request from your IT department
  ```

- [ ] **Configure TLS**
  ```json
  {
    "channels": {
      "mobile": {
        "tls_enabled": true,
        "tls_cert": "/etc/letsencrypt/live/entobot.yourcompany.com/fullchain.pem",
        "tls_key": "/etc/letsencrypt/live/entobot.yourcompany.com/privkey.pem"
      }
    }
  }
  ```

- [ ] **Test TLS Configuration**
  ```bash
  openssl s_client -connect entobot.yourcompany.com:18791 -showcerts
  ```

#### 3. Firewall Rules

- [ ] **Configure UFW (Ubuntu)**
  ```bash
  sudo ufw allow 22/tcp    # SSH
  sudo ufw allow 80/tcp    # HTTP (for cert renewal)
  sudo ufw allow 443/tcp   # HTTPS
  sudo ufw allow 18790/tcp # REST API (or reverse proxy only)
  sudo ufw allow 18791/tcp # WebSocket (or reverse proxy only)
  sudo ufw enable
  ```

- [ ] **Restrict SSH Access**
  ```bash
  # /etc/ssh/sshd_config
  PermitRootLogin no
  PasswordAuthentication no
  PubkeyAuthentication yes
  AllowUsers your-admin-user
  ```

#### 4. Database Security

- [ ] **Strong Database Password**
  ```bash
  # Generate strong password
  openssl rand -base64 32
  ```

- [ ] **PostgreSQL Hardening**
  ```sql
  -- Create dedicated user
  CREATE USER entobot_app WITH PASSWORD 'strong-password';
  CREATE DATABASE entobot_prod OWNER entobot_app;
  
  -- Revoke unnecessary privileges
  REVOKE ALL ON DATABASE entobot_prod FROM PUBLIC;
  GRANT CONNECT ON DATABASE entobot_prod TO entobot_app;
  ```

- [ ] **Enable Database Encryption**
  ```bash
  # PostgreSQL: Enable SSL
  # /etc/postgresql/*/main/postgresql.conf
  ssl = on
  ssl_cert_file = '/path/to/server.crt'
  ssl_key_file = '/path/to/server.key'
  ```

#### 5. Audit Logging

- [ ] **Enable Audit Logging**
  ```json
  {
    "enterprise": {
      "audit_log_enabled": true,
      "audit_log_path": "/var/log/entobot/audit.log",
      "audit_log_level": "INFO"
    }
  }
  ```

- [ ] **Log Rotation**
  ```bash
  # /etc/logrotate.d/entobot
  /var/log/entobot/*.log {
    daily
    rotate 90
    compress
    delaycompress
    notifempty
    create 0640 entobot entobot
    sharedscripts
  }
  ```

- [ ] **Secure Log Storage**
  ```bash
  sudo mkdir -p /var/log/entobot
  sudo chown entobot:entobot /var/log/entobot
  sudo chmod 750 /var/log/entobot
  ```

#### 6. Workspace Sandboxing

- [ ] **Enable Workspace Restriction**
  ```json
  {
    "tools": {
      "restrictToWorkspace": true,
      "workspace": "/opt/entobot/workspace"
    }
  }
  ```

- [ ] **Set Workspace Permissions**
  ```bash
  sudo mkdir -p /opt/entobot/workspace
  sudo chown entobot:entobot /opt/entobot/workspace
  sudo chmod 700 /opt/entobot/workspace
  ```

---

### Post-Deployment Security

#### 7. Intrusion Detection

- [ ] **Install fail2ban**
  ```bash
  sudo apt install fail2ban
  ```

- [ ] **Configure fail2ban for Entobot**
  ```bash
  # /etc/fail2ban/jail.local
  [entobot]
  enabled = true
  port = 18790,18791
  filter = entobot
  logpath = /var/log/entobot/access.log
  maxretry = 5
  bantime = 3600
  ```

- [ ] **Create fail2ban filter**
  ```bash
  # /etc/fail2ban/filter.d/entobot.conf
  [Definition]
  failregex = ^.*Authentication failed.*<HOST>.*$
  ignoreregex =
  ```

#### 8. Security Monitoring

- [ ] **Set up monitoring alerts**
  ```bash
  # Monitor authentication failures
  tail -f /var/log/entobot/audit.log | grep "auth_failed"
  ```

- [ ] **Configure email alerts**
  ```json
  {
    "monitoring": {
      "alerts_enabled": true,
      "alert_email": "security@yourcompany.com",
      "alert_on": ["auth_failed", "rate_limit_exceeded"]
    }
  }
  ```

#### 9. Regular Security Audits

- [ ] **Weekly checks**
  - Review audit logs
  - Check for failed login attempts
  - Monitor rate limiting events
  - Review active sessions

- [ ] **Monthly checks**
  - Update dependencies
  - Review user access
  - Test backup restoration
  - Security vulnerability scan

- [ ] **Quarterly checks**
  - Full security audit
  - Penetration testing
  - Access review
  - Disaster recovery drill

---

### Reverse Proxy (Nginx)

#### 10. Nginx Configuration

- [ ] **Install Nginx**
  ```bash
  sudo apt install nginx
  ```

- [ ] **Configure reverse proxy**
  ```nginx
  # /etc/nginx/sites-available/entobot
  
  server {
      listen 443 ssl http2;
      server_name entobot.yourcompany.com;
      
      ssl_certificate /etc/letsencrypt/live/entobot.yourcompany.com/fullchain.pem;
      ssl_certificate_key /etc/letsencrypt/live/entobot.yourcompany.com/privkey.pem;
      
      # SSL hardening
      ssl_protocols TLSv1.2 TLSv1.3;
      ssl_ciphers HIGH:!aNULL:!MD5;
      ssl_prefer_server_ciphers on;
      
      # Security headers
      add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
      add_header X-Frame-Options "SAMEORIGIN" always;
      add_header X-Content-Type-Options "nosniff" always;
      add_header X-XSS-Protection "1; mode=block" always;
      
      # REST API
      location /api/ {
          proxy_pass http://localhost:18790;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      }
      
      # WebSocket
      location /ws {
          proxy_pass http://localhost:18791;
          proxy_http_version 1.1;
          proxy_set_header Upgrade $http_upgrade;
          proxy_set_header Connection "upgrade";
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_read_timeout 86400;
      }
      
      # Dashboard
      location / {
          proxy_pass http://localhost:8080;
          proxy_set_header Host $host;
      }
  }
  
  # HTTP to HTTPS redirect
  server {
      listen 80;
      server_name entobot.yourcompany.com;
      return 301 https://$server_name$request_uri;
  }
  ```

- [ ] **Enable site**
  ```bash
  sudo ln -s /etc/nginx/sites-available/entobot /etc/nginx/sites-enabled/
  sudo nginx -t
  sudo systemctl reload nginx
  ```

---

### Environment Variables

#### 11. Secrets Management

- [ ] **Use environment variables**
  ```bash
  # /etc/systemd/system/entobot.service
  [Service]
  Environment="JWT_SECRET=your-secret-here"
  Environment="DATABASE_URL=postgresql://user:pass@localhost/entobot"
  Environment="OPENROUTER_API_KEY=sk-or-xxx"
  ```

- [ ] **Never commit secrets to git**
  ```bash
  # .gitignore
  config.json
  .env
  *.key
  *.pem
  ```

---

### Backup Security

#### 12. Encrypted Backups

- [ ] **Encrypt backups**
  ```bash
  # Backup with encryption
  pg_dump entobot_prod | gpg --encrypt --recipient admin@yourcompany.com > backup.sql.gpg
  
  # Restore
  gpg --decrypt backup.sql.gpg | psql entobot_prod
  ```

- [ ] **Secure backup storage**
  ```bash
  # Upload to encrypted S3 bucket
  aws s3 cp backup.sql.gpg s3://company-backups/entobot/ --sse AES256
  ```

---

### Compliance Checklists

#### SOC2 Compliance

- [ ] Access controls implemented
- [ ] Audit logging enabled
- [ ] Encryption in transit (TLS)
- [ ] Encryption at rest (database)
- [ ] Backup and recovery tested
- [ ] Incident response plan documented
- [ ] Regular security reviews

#### GDPR Compliance

- [ ] Data residency controls
- [ ] User data export capability
- [ ] Right to deletion implemented
- [ ] Privacy policy published
- [ ] Data retention policies set
- [ ] Breach notification procedures

#### HIPAA Compliance

- [ ] Access controls (RBAC)
- [ ] Audit trails complete
- [ ] Encryption (transit + rest)
- [ ] PHI handling procedures
- [ ] Business associate agreements
- [ ] Security risk assessment completed

---

### Security Testing

#### 13. Vulnerability Scanning

- [ ] **Run security scan**
  ```bash
  # Install OWASP ZAP or similar
  docker run -t owasp/zap2docker-stable zap-baseline.py \
    -t https://entobot.yourcompany.com
  ```

- [ ] **Check dependencies**
  ```bash
  pip-audit
  safety check
  ```

#### 14. Penetration Testing

- [ ] **Schedule pen test**
  - Internal team or external firm
  - Quarterly or annually
  - Test all attack vectors
  - Document findings
  - Remediate issues

---

## Security Incident Response

### If Breach Suspected

1. **Immediate Actions**
   - [ ] Isolate affected systems
   - [ ] Review audit logs
   - [ ] Identify scope of breach
   - [ ] Preserve evidence

2. **Investigation**
   - [ ] Determine root cause
   - [ ] Assess data exposure
   - [ ] Document timeline
   - [ ] Identify affected users

3. **Remediation**
   - [ ] Patch vulnerabilities
   - [ ] Reset compromised credentials
   - [ ] Update security controls
   - [ ] Test fixes

4. **Communication**
   - [ ] Notify stakeholders
   - [ ] Report to regulators (if required)
   - [ ] Update users
   - [ ] Document lessons learned

5. **Prevention**
   - [ ] Update security policies
   - [ ] Additional training
   - [ ] Enhanced monitoring
   - [ ] Review access controls

---

**Security is ongoing - stay vigilant!**
