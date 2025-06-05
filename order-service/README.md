# Order Service

The Order Service handles order creation, management, and tracking. This service contains multiple vulnerabilities related to business logic and authorization.

## Endpoints

### Order Management
- `POST /orders` - Create order (VULNERABLE: No auth, trusts client data)
- `GET /orders/{id}` - Get order details (VULNERABLE: BOLA)
- `GET /orders/user/{user_id}` - Get user's orders (VULNERABLE: BOLA)
- `PUT /orders/{id}/status` - Update order status (VULNERABLE: No auth)
- `DELETE /orders/{id}` - Cancel order (VULNERABLE: Business logic flaw)

### Admin Endpoints
- `GET /admin/orders` - List all orders (VULNERABLE: No admin verification)

## Vulnerabilities

### API1: Broken Object Level Authorization (BOLA)
- Can access any order without authentication
- Can view any user's order history

### API5: Broken Function Level Authorization
- Admin endpoints accessible without verification
- No role-based access control

### API6: Unrestricted Access to Sensitive Business Flows
- Can cancel completed orders
- No stock validation during order creation
- Trusts client-provided prices and quantities
- Can create orders for other users

### API8: Security Misconfiguration
- No authentication required for any operations
- Verbose error messages

## Database Schema

\`\`\`sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    price DECIMAL(10,2) NOT NULL
);
\`\`\`

## Security Issues to Test

1. **BOLA - Access any order**:
\`\`\`bash
curl http://localhost:5004/orders/1
curl http://localhost:5004/orders/user/1
\`\`\`

2. **Create order for another user**:
\`\`\`bash
curl -X POST http://localhost:5004/orders \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 999,
    "items": [
      {"product_id": 1, "quantity": 1, "price": 0.01}
    ]
  }'
\`\`\`

3. **Cancel completed order**:
\`\`\`bash
curl -X DELETE http://localhost:5004/orders/1
\`\`\`

4. **Price manipulation**:
\`\`\`bash
curl -X POST http://localhost:5004/orders \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "items": [
      {"product_id": 1, "quantity": 100, "price": 0.01}
    ]
  }'
\`\`\`

5. **Access admin endpoint**:
\`\`\`bash
curl http://localhost:5004/admin/orders
\`\`\`

## RabbitMQ Integration

Publishes `order.created` events when orders are placed.

## Order Statuses

- `pending` - Order created, awaiting processing
- `processing` - Order being prepared
- `shipped` - Order shipped
- `completed` - Order delivered
- `cancelled` - Order cancelled
