# External API Service

The External API Service simulates a third-party API that provides discount calculations and user validation. This service demonstrates unsafe API consumption vulnerabilities.

## Endpoints

### Discount Service
- `POST /discount` - Calculate discount (VULNERABLE: Predictable logic)
- `POST /validate` - Validate user (VULNERABLE: Always returns true)
- `GET /health` - Health check (VULNERABLE: Information disclosure)

## Vulnerabilities

### API10: Unsafe Consumption of APIs
- Predictable discount calculation logic
- Always validates users as legitimate
- Exposes internal system information
- No proper API security

### API8: Security Misconfiguration
- Health endpoint exposes sensitive information
- Debug mode enabled
- Internal system details in responses

## API Responses

### Discount Endpoint
\`\`\`json
{
  "discount_percentage": 0.5,
  "original_total": 1000.00,
  "discounted_total": 500.00,
  "internal_user_score": 85,
  "api_version": "1.0-vulnerable",
  "server_info": "internal-discount-service"
}
\`\`\`

### Validation Endpoint
\`\`\`json
{
  "valid": true,
  "user_id": 123,
  "validation_method": "none",
  "internal_notes": "This API always returns true - security flaw"
}
\`\`\`

### Health Endpoint
\`\`\`json
{
  "status": "healthy",
  "version": "1.0-vulnerable",
  "internal_services": ["discount", "validate"],
  "debug_mode": true,
  "database_status": "connected",
  "secret_key": "super-secret-key-123"
}
\`\`\`

## Security Issues to Test

1. **Predictable discount logic**:
\`\`\`bash
# Test user ID patterns
curl -X POST http://localhost:5006/discount \
  -H "Content-Type: application/json" \
  -d '{"user_id": 10, "order_total": 100}'  # 50% discount

curl -X POST http://localhost:5006/discount \
  -H "Content-Type: application/json" \
  -d '{"user_id": 20, "order_total": 100}'  # 50% discount
\`\`\`

2. **Information disclosure**:
\`\`\`bash
curl http://localhost:5006/health
\`\`\`

3. **Always valid validation**:
\`\`\`bash
curl -X POST http://localhost:5006/validate \
  -H "Content-Type: application/json" \
  -d '{"user_id": 999999}'  # Always returns valid
\`\`\`

## Discount Logic

The discount calculation follows predictable patterns:
- Every 10th user ID gets 50% discount
- Orders over $1000 get 20% discount
- All other orders get 10% discount

This predictability allows attackers to:
- Create accounts with specific user IDs
- Manipulate order totals
- Predict discount amounts

## Integration Points

This service is typically called by:
- Order Service during checkout
- Cart Service for price calculations
- User Service for validation

The consuming services should validate responses but currently trust all data blindly.
\`\`\`

Finally, let's create the folder structure diagram:
