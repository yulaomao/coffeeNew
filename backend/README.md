# Coffee Admin - Intelligent Coffee Machine Management Backend

A comprehensive Flask-based management backend for intelligent self-service coffee machines with device management, order processing, recipe management, and administrative features.

## Features

### Core Functionality
- **Device Management**: Register, monitor, and control coffee machines
- **Order Processing**: Handle orders, payments, and refunds
- **Material Management**: Track inventory levels and supply chain
- **Recipe Management**: Create, edit, and deploy coffee recipes
- **Command Dispatch**: Remote control and configuration of devices
- **Real-time Monitoring**: Live status updates and alerts
- **Background Tasks**: Async processing with Celery
- **Audit Trail**: Complete operation logging

### Technology Stack
- **Backend**: Flask 3.x, SQLAlchemy 2.x, PostgreSQL 15+
- **Queue System**: Celery 5.x with Redis
- **Authentication**: Flask-Login with session management
- **API**: RESTful API with Pydantic validation
- **Real-time**: Server-Sent Events (SSE)
- **Monitoring**: Prometheus metrics
- **Frontend**: Jinja2 templates with Bootstrap 5

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd coffeeNew/backend
   ```

2. **Set up Python environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your database and Redis settings
   ```

4. **Initialize database**
   ```bash
   python manage.py init-db
   python manage.py seed-demo
   ```

5. **Create admin user**
   ```bash
   python manage.py create-user --email admin@example.com --password Admin123! --name "System Admin" --role admin
   ```

6. **Start the services**

   **Option A: Using Makefile**
   ```bash
   # Terminal 1: Web server
   make run-web
   
   # Terminal 2: Celery worker
   make run-worker
   
   # Terminal 3: Celery beat scheduler
   make run-beat
   ```

   **Option B: Using manage.py**
   ```bash
   # Terminal 1: Web server
   python manage.py run-web
   
   # Terminal 2: Celery worker
   python manage.py run-worker
   
   # Terminal 3: Celery beat scheduler
   python manage.py run-beat
   ```

7. **Access the application**
   - Web Interface: http://localhost:5000
   - Login: admin@example.com / Admin123!
   - API Base URL: http://localhost:5000/api/v1
   - Metrics: http://localhost:5000/metrics

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Coffee        │    │   Management    │    │   Background    │
│   Machines      │◄───┤   Backend       │◄───┤   Workers       │
│   (Devices)     │    │   (Flask)       │    │   (Celery)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         └──────────────┤   PostgreSQL    │◄─────────────┘
                        │   Database      │
                        └─────────────────┘
                               │
                        ┌─────────────────┐
                        │     Redis       │
                        │  (Cache/Queue)  │
                        └─────────────────┘
```

## API Documentation

### Authentication
The API uses session-based authentication for management interfaces and optional device tokens for device communications.

### Base Response Format
```json
{
  "ok": true,
  "data": { ... }
}
```

Error responses:
```json
{
  "ok": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": { ... }
  }
}
```

### Key Endpoints

#### Dashboard
- `GET /api/v1/dashboard/summary` - System overview with KPIs

#### Device Management
- `GET /api/v1/devices` - List devices with filtering
- `GET /api/v1/devices/{id}` - Get device details
- `POST /api/v1/devices/{id}/commands` - Send command to device
- `POST /api/v1/devices/register` - Device registration (device API)
- `POST /api/v1/devices/{id}/status` - Status update (device API)

#### Order Management
- `GET /api/v1/orders` - List orders with filtering
- `POST /api/v1/orders/{id}/manual_refund` - Process refund
- `POST /api/v1/devices/{id}/orders/create` - Create order (device API)

#### Material Management
- `GET /api/v1/materials` - List materials
- `POST /api/v1/materials/import` - Import materials from CSV
- `PUT /api/v1/devices/{id}/bins/{bin_index}/bind` - Configure device bin

#### Command Dispatch
- `POST /api/v1/commands/dispatch` - Batch command dispatch
- `GET /api/v1/commands/batches` - List command batches
- `POST /api/v1/commands/batches/{id}/retry` - Retry failed commands

## Configuration

### Environment Variables
```bash
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=change-me-in-production

# Database
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/coffee_admin

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Features
ENABLE_SSE=true
ENABLE_DEVICE_TOKEN=false
```

### Database Schema
The system uses the following main entities:
- **Merchants & Locations**: Multi-tenant organization
- **Users**: Admin, operators, and viewers
- **Devices**: Coffee machines with status and configuration
- **Materials**: Inventory items and device bins
- **Orders**: Transaction records with items
- **Recipes**: Coffee making instructions
- **Commands**: Remote device operations
- **Alarms**: System alerts and notifications

## Development

### Running Tests
```bash
make test
# or
pytest --cov=app --maxfail=1 -q
```

### Database Migrations
```bash
# Create new migration
python manage.py migrate

# Apply migrations
python manage.py init-db
```

### Code Structure
```
backend/
├── app/                    # Main application package
│   ├── api/               # REST API endpoints
│   ├── models/            # SQLAlchemy data models
│   ├── services/          # Business logic layer
│   ├── views/             # Web UI controllers
│   ├── workers/           # Celery background tasks
│   ├── schemas/           # Pydantic validation schemas
│   └── utils/             # Utility modules
├── migrations/            # Database migrations
├── tests/                 # Test suite
├── manage.py             # CLI management commands
└── requirements.txt      # Python dependencies
```

## Device Integration

### Device Registration
Devices register themselves using:
```bash
curl -X POST http://localhost:5000/api/v1/devices/register \
  -H "Content-Type: application/json" \
  -H "X-Device-Token: your-device-token" \
  -d '{
    "device_id": "D001",
    "model": "CoffeePro-A",
    "firmware_version": "2.1.0",
    "serial": "SN123456",
    "address": "Store Location"
  }'
```

### Status Updates
Regular heartbeat:
```bash
curl -X POST http://localhost:5000/api/v1/devices/D001/status \
  -H "Content-Type: application/json" \
  -H "X-Device-Token: your-device-token" \
  -d '{
    "status": "online",
    "timestamp": "2024-01-01T12:00:00Z",
    "ip": "192.168.1.100",
    "temperature": 22.5
  }'
```

## Monitoring

### Prometheus Metrics
Available at `/metrics`:
- `api_requests_total` - API request counts
- `device_online_rate` - Device availability
- `daily_orders_total` - Order volume
- `pending_commands_count` - Queue depth
- `material_low_count` - Inventory alerts

### Health Checks
- Database connectivity
- Redis availability
- Celery worker status
- Background task queues

## Production Deployment

### Security Considerations
- Use HTTPS in production
- Configure strong SECRET_KEY
- Enable CSRF protection
- Set up proper database user permissions
- Configure Redis authentication
- Use environment-specific configuration

### Scaling
- Use PostgreSQL connection pooling
- Deploy multiple Flask workers (gunicorn)
- Scale Celery workers horizontally
- Use Redis clustering for high availability
- Implement database read replicas

### Monitoring
- Set up log aggregation
- Configure error tracking
- Monitor database performance
- Track business metrics
- Set up alerting rules

## Troubleshooting

### Common Issues

**Database Connection Error**
```bash
# Check PostgreSQL service
sudo systemctl status postgresql
# Verify connection string in .env
```

**Redis Connection Error**
```bash
# Check Redis service
sudo systemctl status redis
# Test Redis connectivity
redis-cli ping
```

**Celery Worker Not Starting**
```bash
# Check broker connectivity
celery -A app.workers.celery_app inspect ping
# View worker logs
python manage.py run-worker --loglevel=debug
```

**Migration Errors**
```bash
# Reset migrations (development only)
rm migrations/versions/*.py
python manage.py init-db
```

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

For support and questions:
- Check the troubleshooting section
- Review API documentation
- Examine system logs
- Test with demo data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request