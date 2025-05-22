# Web Server Security Response Checklist

## Immediate Actions (Do Today)

### 1. Check for phpMyAdmin
```bash
# Search for phpMyAdmin on your server
find / -name "*phpmyadmin*" -type d 2>/dev/null
find /var/www -name "*phpmyadmin*" -type d 2>/dev/null
```

### 2. If phpMyAdmin Exists:
- **Move it to a non-standard path** (e.g., `/admin-db-2024-secret/`)
- **Add IP whitelisting** - only allow your IP addresses
- **Enable strong authentication** (2FA if possible)
- **Update to latest version** immediately

### 3. Server Hardening
```bash
# Update your system
sudo apt update && sudo apt upgrade -y

# Check for suspicious processes
ps aux | grep -E "(php|mysql|apache|nginx)"

# Review recent logins
last -n 20
```

## Network Security

### 4. Firewall Configuration
```bash
# Basic UFW setup (Ubuntu/Debian)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 5. Nginx/Apache Security Headers
Add to your web server config:
```nginx
# Nginx security headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;

# Hide server version
server_tokens off;
```

## Monitoring & Detection

### 6. Fail2Ban Setup
```bash
# Install fail2ban
sudo apt install fail2ban

# Configure for web attacks
sudo nano /etc/fail2ban/jail.local
```

### 7. Log Monitoring
- **Set up log alerts** for unusual patterns
- **Monitor 404 errors** - high volume indicates scanning
- **Track geographic access patterns**

### 8. Rate Limiting
```nginx
# Nginx rate limiting
http {
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    server {
        location / {
            limit_req zone=api burst=20 nodelay;
        }
    }
}
```

## Database Security

### 9. MySQL/PostgreSQL Hardening
- **Change default ports** (3306 → custom port)
- **Disable remote root login**
- **Use strong passwords** for all database users
- **Regular security updates**

### 10. Database Access Control
```sql
-- Remove anonymous users
DELETE FROM mysql.user WHERE User='';

-- Remove test database
DROP DATABASE IF EXISTS test;

-- Flush privileges
FLUSH PRIVILEGES;
```

## Application Security

### 11. Web Application Security
- **Keep all software updated** (CMS, plugins, frameworks)
- **Use HTTPS everywhere** with valid SSL certificates
- **Implement CSP headers**
- **Regular security scans**

### 12. Backup Security
- **Encrypted backups** stored off-site
- **Test restore procedures** regularly
- **Secure backup access credentials**

## Ongoing Monitoring

### 13. Regular Security Audits
- **Weekly log reviews**
- **Monthly vulnerability scans**
- **Quarterly penetration testing**

### 14. Incident Response Plan
- **Document security contacts**
- **Prepare incident response procedures**
- **Test backup and recovery processes**

## Warning Signs to Watch For

- **Unusual 404 patterns** (like the phpMyAdmin scanning)
- **Failed login attempts** from foreign IPs
- **Unexpected database connections**
- **Unusual server resource usage**
- **Modified system files**

## Emergency Contacts

Keep these ready:
- Your hosting provider's security team
- Database administrator contacts
- Incident response team (if you have one)
- Legal/compliance team (for data breach requirements)

---

**Remember**: This type of scanning happens constantly on the internet. The key is ensuring your systems are hardened and monitored so these automated attacks can't succeed.
