# Vulnerable E-Commerce Microservices Architecture

⚠️ **WARNING: This is an intentionally vulnerable application designed for security testing and education purposes only. Do not deploy this in production or use real personal/financial information.**

## Overview

This project implements a deliberately vulnerable e-commerce platform using microservices architecture to demonstrate the OWASP API Security Top 10 vulnerabilities. The system is designed to run locally using Docker and includes multiple services with various security flaws for educational purposes.

## Architecture

                    ┌─────────────────────────────────────────────────────────┐
                    │                    FRONTEND LAYER                       │
                    │                                                         │
                    │  ┌─────────────────┐         ┌─────────────────┐      │
                    │  │  Customer       │         │  Admin Panel    │      │
                    │  │  Frontend       │         │  (Port 3000)    │      │
                    │  │  (Port 3001)    │         │                 │      │
                    │  │  - Registration │         │  - User Mgmt    │      │
                    │  │  - Product View │         │  - Product Mgmt │      │
                    │  │  - Shopping     │         │  - Order Mgmt   │      │
                    │  │  - Checkout     │         │  - Direct DB    │      │
                    │  └─────────────────┘         └─────────────────┘      │
                    └─────────────────────────────────────────────────────────┘
                                           │
                                           ▼
                    ┌─────────────────────────────────────────────────────────┐
                    │                   GATEWAY LAYER                         │
                    │                                                         │
                    │              ┌─────────────────┐                       │
                    │              │  API Gateway    │                       │
                    │              │  (Port 8000)    │                       │
                    │              │                 │                       │
                    │              │  - Route Reqs   │                       │
                    │              │  - No Auth      │                       │
                    │              │  - Open CORS    │                       │
                    │              │  - No Filters   │                       │
                    │              └─────────────────┘                       │
                    └─────────────────────────────────────────────────────────┘
                                           │
                                           ▼
                    ┌─────────────────────────────────────────────────────────┐
                    │                 MICROSERVICES LAYER                     │
                    │                                                         │
                    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
                    │  │User Service │  │Product Svc  │  │Cart Service │    │
                    │  │(Port 5001)  │  │(Port 5002)  │  │(Port 5003)  │    │
                    │  │             │  │             │  │             │    │
                    │  │- Register   │  │- Catalog    │  │- Add Items  │    │
                    │  │- Login      │  │- Inventory  │  │- Remove     │    │
                    │  │- Profile    │  │- Categories │  │- Calculate  │    │
                    │  │- BOLA Vuln  │  │- SQL Inject │  │- No Auth    │    │
                    │  └─────────────┘  └─────────────┘  └─────────────┘    │
                    │                                                         │
                    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
                    │  │Order Service│  │Upload Svc   │  │External API │    │
                    │  │(Port 5004)  │  │(Port 5005)  │  │(Port 5006)  │    │
                    │  │             │  │             │  │             │    │
                    │  │- Create     │  │- File Upload│  │- Discounts  │    │
                    │  │- Track      │  │- SSRF Vuln  │  │- Validation │    │
                    │  │- Cancel     │  │- Port Scan  │  │- Always True│    │
                    │  │- No Auth    │  │- Internal   │  │- Predictable│    │
                    │  └─────────────┘  └─────────────┘  └─────────────┘    │
                    └─────────────────────────────────────────────────────────┘
                                           │
                                           ▼
                    ┌─────────────────────────────────────────────────────────┐
                    │                   DATA LAYER                            │
                    │                                                         │
                    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
                    │  │PostgreSQL   │  │PostgreSQL   │  │PostgreSQL   │    │
                    │  │User DB      │  │Product DB   │  │Order DB     │    │
                    │  │(Port 5432)  │  │(Port 5433)  │  │(Port 5434)  │    │
                    │  └─────────────┘  └─────────────┘  └─────────────┘    │
                    │                                                         │
                    │  ┌─────────────┐              ┌─────────────┐          │
                    │  │Redis Cache  │              │RabbitMQ     │          │
                    │  │Cart Storage │              │Messaging    │          │
                    │  │(Port 6379)  │              │(Port 5672)  │          │
                    │  └─────────────┘              └─────────────┘          │
                    └─────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────────┐
    │                           MESSAGE FLOWS                                 │
    │                                                                         │
    │  User Service ──────► RabbitMQ ──────► Product Service                 │
    │      │                   │                    │                        │
    │      │                   │                    ▼                        │
    │      │                   │            ┌─────────────┐                  │
    │      │                   │            │Stock Updates│                  │
    │      │                   │            │Order Events │                  │
    │      │                   │            │User Events  │                  │
    │      │                   │            └─────────────┘                  │
    │      │                   │                    │                        │
    │      ▼                   ▼                    ▼                        │
    │  Order Service ◄──── Cart Service ◄──── Product Service               │
    └─────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────────┐
    │                      VULNERABILITY DISTRIBUTION                         │
    │                                                                         │
    │  API1 (BOLA)          │ User, Order, Cart Services                     │
    │  API2 (Broken Auth)   │ User Service (MD5, weak JWT)                   │
    │  API3 (Property Auth) │ User Service (admin escalation)                │
    │  API4 (Resource Abuse)│ Cart, Product Services (no limits)             │
    │  API5 (Function Auth) │ All Services (open admin endpoints)            │
    │  API6 (Business Logic)│ Order, Cart Services (logic flaws)             │
    │  API7 (SSRF)          │ Upload Service (internal access)               │
    │  API8 (Misconfig)     │ All Services (debug, errors, CORS)             │
    │  API9 (Inventory)     │ Product Service (deleted data access)          │
    │  API10 (Unsafe API)   │ External API (predictable, no validation)      │
    └─────────────────────────────────────────────────────────────────────────┘

## Services

| Service | Port | Description | Database |
|---------|------|-------------|----------|
| API Gateway | 8000 | Routes requests to microservices | None |
| User Service | 5001 | User registration, authentication | PostgreSQL |
| Product Service | 5002 | Product catalog management | PostgreSQL |
| Cart Service | 5003 | Shopping cart functionality | Redis |
| Order Service | 5004 | Order processing | PostgreSQL |
| Upload Service | 5005 | File upload (SSRF demo) | None |
| External API | 5006 | Third-party API simulation | None |
| Admin Panel | 3000 | Administrative interface | Direct DB access |
| Customer Frontend | 3001 | User-facing web interface | None |

## Quick Start

### Prerequisites

- Docker Desktop
- Docker Compose
- 8GB+ RAM recommended

### Installation

1. Clone the repository:
\`\`\`bash
git clone <repository-url>
cd vulnerable-ecommerce-microservices
\`\`\`

2. Start all services:
\`\`\`bash
docker-compose up -d
\`\`\`

3. Wait for all services to initialize (approximately 2-3 minutes)

4. Access the applications:
   - **Customer Frontend**: http://localhost:3001
   - **Admin Panel**: http://localhost:3000
   - **API Gateway**: http://localhost:8000

### Default Credentials

- **Admin User**: `admin` / `admin123`
- **Regular Users**: Create new accounts via registration

## OWASP API Security Top 10 Vulnerabilities

This application demonstrates all OWASP API Security Top 10 vulnerabilities:

### API1: Broken Object Level Authorization (BOLA)
- **Location**: User Service, Order Service, Cart Service
- **Example**: Access any user's profile: `GET /api/users/{user_id}`
- **Example**: View any user's orders: `GET /api/orders/user/{user_id}`

### API2: Broken Authentication
- **Location**: User Service
- **Issues**: 
  - Weak password hashing (MD5)
  - No rate limiting on login attempts
  - Weak JWT secret key
  - Long token expiration (30 days)

### API3: Broken Object Property Level Authorization
- **Location**: User Service
- **Example**: Update user admin status: `PUT /api/users/{user_id}` with `{"is_admin": true}`

### API4: Unrestricted Resource Consumption
- **Location**: Cart Service, Product Service
- **Issues**:
  - No rate limiting on cart operations
  - No pagination on product listings
  - Unlimited cart item quantities

### API5: Broken Function Level Authorization
- **Location**: All services
- **Issues**:
  - Admin endpoints accessible without authentication
  - No role-based access control
  - Direct database access in admin panel

### API6: Unrestricted Access to Sensitive Business Flows
- **Location**: Order Service, Cart Service
- **Issues**:
  - Can cancel completed orders
  - No stock validation during checkout
  - Can manipulate cart totals

### API7: Server Side Request Forgery (SSRF)
- **Location**: Upload Service
- **Example**: `POST /upload/url` with internal URLs
- **Example**: `POST /upload/scan` for port scanning

### API8: Security Misconfiguration
- **Location**: All services
- **Issues**:
  - Debug mode enabled
  - Verbose error messages
  - Open CORS policies
  - Exposed debug endpoints

### API9: Improper Inventory Management
- **Location**: Product Service
- **Issues**:
  - Deleted products still accessible
  - Soft deletes exposed via parameters
  - No proper data lifecycle management

### API10: Unsafe Consumption of APIs
- **Location**: External API integration
- **Issues**:
  - Trusts external API responses blindly
  - No validation of third-party data
  - Exposes internal system information

## Testing the Vulnerabilities

### Example Exploits

1. **BOLA - Access other users' data**:
\`\`\`bash
curl http://localhost:8000/api/users/1
curl http://localhost:8000/api/orders/user/1
\`\`\`

2. **Privilege Escalation**:
\`\`\`bash
curl -X PUT http://localhost:8000/api/users/2 \
  -H "Content-Type: application/json" \
  -d '{"is_admin": true}'
\`\`\`

3. **SSRF - Internal network scanning**:
\`\`\`bash
curl -X POST http://localhost:5005/upload/scan \
  -H "Content-Type: application/json" \
  -d '{"target": "localhost", "port": 5432}'
\`\`\`

4. **Business Logic Bypass**:
\`\`\`bash
# Add negative quantities to cart
curl -X POST http://localhost:8000/api/cart/cart/1/add \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "quantity": -10}'
\`\`\`

## Security Testing Tools

Recommended tools for testing:
- **Burp Suite** - Web application security testing
- **OWASP ZAP** - Automated security scanning
- **Postman** - API testing and exploitation
- **curl** - Command-line API testing

## Educational Use

This application is designed for:
- Security training and workshops
- Penetration testing practice
- API security awareness
- Vulnerability assessment learning
- Secure coding education

## Cleanup

To stop and remove all containers:
\`\`\`bash
docker-compose down -v
\`\`\`

## Contributing

This is an educational project. If you find additional vulnerabilities or have suggestions for improvement, please submit an issue or pull request.

## Disclaimer

This application contains intentional security vulnerabilities and should never be deployed in a production environment. The authors are not responsible for any misuse of this software.

## License

This project is released under the MIT License for educational purposes only.
