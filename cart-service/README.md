# Cart Service

The Cart Service manages shopping cart functionality using Redis for storage. This service demonstrates multiple API security vulnerabilities.

## Endpoints

### Cart Management
- `GET /cart/{user_id}` - Get user's cart (VULNERABLE: BOLA)
- `POST /cart/{user_id}/add` - Add item to cart (VULNERABLE: No rate limiting)
- `POST /cart/{user_id}/remove` - Remove item from cart (VULNERABLE: No auth)
- `POST /cart/{user_id}/clear` - Clear cart (VULNERABLE: No auth)
- `GET /cart/{user_id}/total` - Get cart total (VULNERABLE: Business logic flaw)

### Debug Endpoints
- `GET /debug/carts` - View all carts (VULNERABLE: Information disclosure)

## Vulnerabilities

### API1: Broken Object Level Authorization (BOLA)
- Can access any user's cart without authentication
- No user verification for cart operations

### API4: Unrestricted Resource Consumption
- No rate limiting on cart operations
- Can spam add/remove requests

### API6: Unrestricted Access to Sensitive Business Flows
- Can add negative quantities
- Cart total calculation trusts client-provided prices
- No stock validation

### API8: Security Misconfiguration
- Debug endpoint exposes all user carts
- No input validation

## Data Storage

Uses Redis with keys in format: `cart:{user_id}`

Example cart data:
\`\`\`json
{
  "1": 2,    // product_id: quantity
  "3": 1,
  "5": 4
}
\`\`\`

## Security Issues to Test

1. **BOLA - Access other users' carts**:
\`\`\`bash
curl http://localhost:5003/cart/1
curl http://localhost:5003/cart/999
\`\`\`

2. **Negative Quantities**:
\`\`\`bash
curl -X POST http://localhost:5003/cart/1/add \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "quantity": -10}'
\`\`\`

3. **Price Manipulation**:
\`\`\`bash
curl "http://localhost:5003/cart/1/total?price_1=0.01&price_2=0.01"
\`\`\`

4. **Information Disclosure**:
\`\`\`bash
curl http://localhost:5003/debug/carts
\`\`\`

5. **Rate Limiting Test**:
\`\`\`bash
# Spam cart operations
for i in {1..1000}; do
  curl -X POST http://localhost:5003/cart/1/add \
    -H "Content-Type: application/json" \
    -d '{"product_id": 1, "quantity": 1}' &
done
\`\`\`

## RabbitMQ Integration

Listens for `product.deleted` events to remove deleted products from all carts.
