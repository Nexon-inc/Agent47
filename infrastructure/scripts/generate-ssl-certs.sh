#!/bin/bash

# Generate SSL certificates for Agent47 development
# This script creates self-signed certificates for local development

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔐 Generating SSL certificates for Agent47 development...${NC}"

# Create SSL directory if it doesn't exist
SSL_DIR="$(dirname "$0")/../nginx/ssl"
mkdir -p "$SSL_DIR"

cd "$SSL_DIR"

# Generate private key
echo -e "${YELLOW}📝 Generating private key...${NC}"
openssl genrsa -out agent47.key 2048

# Generate certificate signing request
echo -e "${YELLOW}📝 Generating certificate signing request...${NC}"
openssl req -new -key agent47.key -out agent47.csr -subj "/C=US/ST=CA/L=San Francisco/O=Agent47/OU=Development/CN=agent47.com"

# Generate self-signed certificate
echo -e "${YELLOW}📝 Generating self-signed certificate...${NC}"
openssl x509 -req -days 365 -in agent47.csr -signkey agent47.key -out agent47.crt

# Generate Diffie-Hellman parameters for better security
echo -e "${YELLOW}📝 Generating Diffie-Hellman parameters...${NC}"
openssl dhparam -out dhparam.pem 2048

# Clean up CSR file
rm agent47.csr

# Set appropriate permissions
chmod 600 agent47.key
chmod 644 agent47.crt
chmod 644 dhparam.pem

echo -e "${GREEN}✅ SSL certificates generated successfully!${NC}"
echo -e "${GREEN}📁 Files created in: $SSL_DIR${NC}"
echo -e "${GREEN}   - agent47.crt (certificate)${NC}"
echo -e "${GREEN}   - agent47.key (private key)${NC}"
echo -e "${GREEN}   - dhparam.pem (DH parameters)${NC}"
echo ""
echo -e "${YELLOW}⚠️  Note: These are self-signed certificates for development only.${NC}"
echo -e "${YELLOW}   For production, use certificates from a trusted CA.${NC}"
echo ""
echo -e "${GREEN}🚀 You can now start the Agent47 platform with SSL support!${NC}"
