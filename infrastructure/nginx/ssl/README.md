# SSL Certificates for Agent47

This directory contains SSL certificates for the Agent47 platform.

## Development Certificates

For development, you can generate self-signed certificates using the following commands:

```bash
# Generate private key
openssl genrsa -out agent47.key 2048

# Generate certificate signing request
openssl req -new -key agent47.key -out agent47.csr

# Generate self-signed certificate
openssl x509 -req -days 365 -in agent47.csr -signkey agent47.key -out agent47.crt

# Clean up CSR file
rm agent47.csr
```

## Production Certificates

For production, you should use certificates from a trusted Certificate Authority (CA) such as:

- Let's Encrypt (free)
- DigiCert
- Comodo
- GlobalSign

### Let's Encrypt Setup

```bash
# Install certbot
sudo apt-get install certbot

# Generate certificate
sudo certbot certonly --standalone -d agent47.com -d www.agent47.com -d api.agent47.com -d admin.agent47.com

# Copy certificates to this directory
sudo cp /etc/letsencrypt/live/agent47.com/fullchain.pem agent47.crt
sudo cp /etc/letsencrypt/live/agent47.com/privkey.pem agent47.key
sudo chown $USER:$USER agent47.crt agent47.key
```

## File Structure

```
ssl/
├── README.md          # This file
├── agent47.crt        # SSL certificate
├── agent47.key        # SSL private key
└── dhparam.pem        # Diffie-Hellman parameters (optional)
```

## Security Notes

- Never commit private keys to version control
- Use strong passphrases for private keys
- Regularly rotate certificates
- Monitor certificate expiration dates
- Use HSTS headers in production

## Certificate Renewal

For Let's Encrypt certificates, set up automatic renewal:

```bash
# Add to crontab
0 12 * * * /usr/bin/certbot renew --quiet
```

## Troubleshooting

### Certificate not found
- Ensure `agent47.crt` and `agent47.key` exist in this directory
- Check file permissions (should be readable by nginx user)

### Certificate expired
- Renew the certificate using the appropriate method
- Restart nginx after updating certificates

### SSL handshake failed
- Verify certificate and key match
- Check certificate chain is complete
- Ensure certificate is valid for the domain