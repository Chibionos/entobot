# Entobot Enterprise Deployment Guide

## Production Deployment Architectures

### 1. Standalone Server (< 50 users)

**Infrastructure:**
- Single VM: 4 CPU, 8GB RAM, 50GB SSD
- Ubuntu 22.04 LTS or similar
- Public IP with firewall

**Components:**
- Backend server (Python)
- Dashboard (FastAPI)
- PostgreSQL database
- Nginx reverse proxy
- Let's Encrypt TLS

**Setup:**
```bash
# Install dependencies
sudo apt update && sudo apt install -y python3.11 postgresql nginx certbot

# Clone repository
git clone https://github.com/HKUDS/nanobot.git entobot
cd entobot && pip install -e .

# Configure database
sudo -u postgres createdb entobot_prod

# Setup systemd service
sudo cp deploy/entobot.service /etc/systemd/system/
sudo systemctl enable entobot && sudo systemctl start entobot

# Configure Nginx with TLS
sudo certbot --nginx -d entobot.yourcompany.com
```

**Cost:** $50-100/month (cloud VM)

### 2. High Availability Cluster (50-500 users)

**Infrastructure:**
- 3x backend servers (4 CPU, 8GB RAM each)
- 1x PostgreSQL primary + replica
- 1x load balancer
- Redis for session cache

**Features:**
- Zero-downtime deployments
- Automatic failover
- Horizontal scaling
- Database replication

**Cost:** $300-500/month

### 3. Kubernetes Cloud Native (500+ users)

**Infrastructure:**
- Kubernetes cluster (EKS/GKE/AKS)
- Managed PostgreSQL
- Managed Redis
- Autoscaling (2-20 pods)
- Multi-region support

**Cost:** $500-2000/month (depending on scale)

### 4. Air-Gapped Deployment

**Requirements:**
- Complete offline capability
- Local LLM (vLLM with Llama/Mistral)
- On-premises servers
- No internet required

**Components:**
- Backend server (offline mode)
- Local vLLM inference server
- PostgreSQL database
- Internal CA for TLS

**Use Cases:**
- Government/defense
- Healthcare (HIPAA strict mode)
- Financial institutions
- Research facilities

## Security Hardening Checklist

### Pre-Production Security

- [ ] Generate strong JWT secret (64+ characters)
- [ ] Configure TLS/SSL certificates (Let's Encrypt or corporate CA)
- [ ] Enable rate limiting (recommended: 60 req/min)
- [ ] Configure IP whitelist (if applicable)
- [ ] Set up audit logging to persistent storage
- [ ] Enable workspace sandboxing (`restrictToWorkspace: true`)
- [ ] Configure CORS for production domains
- [ ] Use environment variables for secrets (not config files)
- [ ] Set strong database password
- [ ] Configure firewall rules (allow only 443, 80, SSH)
- [ ] Disable debug mode
- [ ] Enable secure session cookies
- [ ] Configure CSP headers
- [ ] Set up log rotation
- [ ] Enable database encryption at rest

### Post-Production Security

- [ ] Monitor audit logs daily
- [ ] Set up intrusion detection (fail2ban)
- [ ] Configure security alerts
- [ ] Regular security audits
- [ ] Patch management process
- [ ] Backup verification
- [ ] Disaster recovery drills
- [ ] Access review (quarterly)

## Corporate Network Integration

### SSO/SAML Setup

```python
# config.json
{
  "auth": {
    "provider": "saml",
    "saml_idp_url": "https://sso.yourcompany.com/saml",
    "saml_entity_id": "entobot-enterprise",
    "saml_cert": "/path/to/cert.pem"
  }
}
```

### LDAP/Active Directory

```python
{
  "auth": {
    "provider": "ldap",
    "ldap_server": "ldap://ad.yourcompany.com",
    "ldap_base_dn": "dc=yourcompany,dc=com",
    "ldap_bind_dn": "cn=entobot,ou=services,dc=yourcompany,dc=com"
  }
}
```

### VPN Compatibility

Works seamlessly behind:
- Cisco AnyConnect
- Palo Alto GlobalProtect
- FortiClient
- OpenVPN
- WireGuard

**Configuration:** No special settings required - uses standard ports (443/18791)

## Monitoring and Alerting

### Prometheus Metrics

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'entobot'
    static_configs:
      - targets: ['localhost:18790']
```

### Key Metrics to Monitor

- WebSocket connection count
- Message throughput (msg/sec)
- API response time (p50, p95, p99)
- Error rate
- JWT token generation/validation rate
- Database query time
- Memory usage
- CPU usage

### Grafana Dashboards

Import dashboard template: `deploy/grafana-dashboard.json`

### Alerts

```yaml
# alerts.yml
- alert: HighErrorRate
  expr: rate(http_errors_total[5m]) > 0.05
  annotations:
    summary: "High error rate detected"

- alert: HighMemoryUsage
  expr: memory_usage_percent > 85
  annotations:
    summary: "Memory usage above 85%"
```

## Backup and Disaster Recovery

### Backup Strategy

**Daily Backups:**
- PostgreSQL database
- Configuration files
- Audit logs
- User data

**Backup Script:**
```bash
#!/bin/bash
# /opt/entobot/backup.sh

BACKUP_DIR="/backup/entobot/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Database backup
pg_dump entobot_prod > $BACKUP_DIR/database.sql

# Config backup
cp ~/.nanobot/config.json $BACKUP_DIR/

# Audit logs
cp -r /var/log/entobot/audit/ $BACKUP_DIR/

# Upload to S3 (or other storage)
aws s3 sync $BACKUP_DIR s3://company-backups/entobot/

# Retention: 30 days
find /backup/entobot -mtime +30 -delete
```

**Cron:** `0 2 * * * /opt/entobot/backup.sh`

### Disaster Recovery

**RTO (Recovery Time Objective):** 4 hours
**RPO (Recovery Point Objective):** 24 hours (daily backups)

**Recovery Steps:**
1. Provision new server
2. Install Entobot Enterprise
3. Restore database from backup
4. Restore configuration
5. Update DNS
6. Verify functionality
7. Notify users

## Compliance Considerations

### SOC2 Requirements

- [ ] Audit logging enabled
- [ ] Access controls configured
- [ ] Encryption in transit (TLS)
- [ ] Encryption at rest (database)
- [ ] Backup and recovery tested
- [ ] Incident response plan
- [ ] Regular security reviews

### GDPR Requirements

- [ ] Data residency controls
- [ ] User data export capability
- [ ] Right to deletion
- [ ] Privacy policy
- [ ] Data processing agreements
- [ ] Breach notification process

### HIPAA Requirements

- [ ] Audit trails
- [ ] Access controls (RBAC)
- [ ] Encryption (transit + rest)
- [ ] PHI handling procedures
- [ ] Business associate agreements
- [ ] Security risk assessment

## Performance Optimization

### Database Tuning

```sql
-- PostgreSQL settings for production
ALTER SYSTEM SET shared_buffers = '2GB';
ALTER SYSTEM SET effective_cache_size = '6GB';
ALTER SYSTEM SET work_mem = '50MB';
ALTER SYSTEM SET maintenance_work_mem = '512MB';
SELECT pg_reload_conf();
```

### Caching with Redis

```python
{
  "cache": {
    "enabled": true,
    "backend": "redis",
    "redis_url": "redis://localhost:6379/0",
    "ttl": 3600
  }
}
```

### Connection Pooling

```python
{
  "database": {
    "pool_size": 20,
    "max_overflow": 10,
    "pool_timeout": 30
  }
}
```

## Deployment Automation

### Docker Deployment

```bash
# Build image
docker build -t entobot-enterprise:v1.0 .

# Run container
docker run -d \
  -p 18790:18790 \
  -p 18791:18791 \
  -v ~/.nanobot:/root/.nanobot \
  --name entobot \
  entobot-enterprise:v1.0
```

### Docker Compose

```yaml
version: '3.8'
services:
  entobot:
    build: .
    ports:
      - "18790:18790"
      - "18791:18791"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/entobot
    volumes:
      - ./config:/root/.nanobot
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: entobot
      POSTGRES_USER: entobot
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    
volumes:
  pgdata:
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: entobot-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: entobot
  template:
    metadata:
      labels:
        app: entobot
    spec:
      containers:
      - name: entobot
        image: entobot-enterprise:v1.0
        ports:
        - containerPort: 18790
        - containerPort: 18791
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: entobot-secrets
              key: database-url
---
apiVersion: v1
kind: Service
metadata:
  name: entobot-service
spec:
  selector:
    app: entobot
  ports:
  - name: api
    port: 18790
  - name: websocket
    port: 18791
  type: LoadBalancer
```

## Enterprise Support

Contact: enterprise@entobot.ai (example)

Services available:
- Installation and setup
- Custom development
- Integration services
- Training and onboarding
- 24/7 support
- SLA agreements

