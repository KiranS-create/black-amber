# TLS/SSL Termination & Reverse Proxy Hardening

> **Platform Scope**: Production Web Architecture.  
> **Desktop Status**: Standalone native desktop applications (.exe/.dmg) are **DEFERRED TO FUTURE WORKSTREAM**. All traffic security terminates at the web reverse proxy boundary.

---

## 1. Security Invariants

In production deployments, AegisTrace must be accessed exclusively over HTTPS to prevent token interception, watermark stripping during transit, and adversary man-in-the-middle attacks.

The backend automatically enforces:
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Cache-Control: no-store, no-cache, must-revalidate, private` on sensitive evidence routes.

---

## 2. Option A: Caddy Server (Automatic HTTPS & Let's Encrypt)

Caddy automatically provisions, renews, and configures Let's Encrypt certificates with HTTP/3 support:

### `Caddyfile`
```caddy
trace.agency.gov {
    # Automatic TLS with Let's Encrypt
    tls contact@agency.gov

    # Reverse proxy to AegisTrace container
    reverse_proxy aegistrace:8000 {
        header_up Host {host}
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-For {remote_host}
        header_up X-Forwarded-Proto {scheme}
    }

    # Strict transport headers
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        Referrer-Policy "strict-origin-when-cross-origin"
    }

    # Compress static assets
    encode zstd gzip
}
```

---

## 3. Option B: Nginx Reverse Proxy

### `nginx.conf`
```nginx
server {
    listen 80;
    server_name trace.agency.gov;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name trace.agency.gov;

    ssl_certificate /etc/letsencrypt/live/trace.agency.gov/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/trace.agency.gov/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;

    # Maximum upload size for forensic artifact packages (e.g. 100MB)
    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 4. Option C: Cloudflare Edge SSL (Zero Configuration)

When using Cloudflare DNS:
1. Proxy the DNS record (`Orange Cloud` enabled).
2. Set **SSL/TLS encryption mode** to **Full (strict)**.
3. Enable **Always Use HTTPS** and **HTTP Strict Transport Security (HSTS)** in Edge Certificates.
4. Edge SSL termination protects the browser-to-Cloudflare connection automatically.
