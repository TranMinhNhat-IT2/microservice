# Product Service

The Product Service manages the product catalog, inventory, and categories. This service demonstrates several API security vulnerabilities.

## Endpoints

### Product Management
- `GET /products` - List products (VULNERABLE: No pagination)
- `GET /products/{id}` - Get product details (VULNERABLE: SQL injection)
- `POST /products` - Create product (VULNERABLE: No auth)
- `PUT /products/{id}` - Update product (VULNERABLE: No auth)
- `DELETE /products/{id}` - Delete product (VULNERABLE: No auth)
- `PUT /products/{id}/stock` - Update stock (VULNERABLE: No validation)

## Vulnerabilities

### API1: Broken Object Level Authorization
- No authentication required for any operations
- Anyone can create, modify, or delete products

### API4: Unrestricted Resource Consumption
- No pagination on product listings
- Can cause memory exhaustion with large datasets

### API6: Unrestricted Access to Sensitive Business Flows
- No stock validation (can set negative stock)
- No business logic validation

### API8: Security Misconfiguration
- SQL injection in product detail endpoint
- Debug mode enabled
- Verbose error messages

### API9: Improper Inventory Management
- Soft-deleted products accessible via parameters
- No proper data lifecycle management

## Database Schema

\`\`\`sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    stock INTEGER DEFAULT 0,
    category VARCHAR(100),
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
\`\`\`

## Security Issues to Test

1. **SQL Injection**:
\`\`\`bash
curl "http://localhost:5002/products/1'; DROP TABLE products; --"
\`\`\`

2. **Access Deleted Products**:
\`\`\`bash
curl "http://localhost:5002/products?show_deleted=true"
\`\`\`

3. **Negative Stock**:
\`\`\`bash
curl -X PUT http://localhost:5002/products/1/stock \
  -H "Content-Type: application/json" \
  -d '{"stock": -100}'
\`\`\`

4. **Resource Exhaustion**:
\`\`\`bash
# Create thousands of products
for i in {1..1000}; do
  curl -X POST http://localhost:5002/products \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"Product $i\", \"price\": 10.00}"
done
\`\`\`

## Sample Products

The service initializes with sample products:
- Laptop ($999.99)
- Smartphone ($699.99)
- Book ($49.99)
- Headphones ($199.99)
