# Coffee Shop Management System

A comprehensive Flask-based management system for coffee shop operations, providing real-time device monitoring, order management, inventory tracking, and analytics.

## Features

### 🎯 Core Functionality
- **Real-time Device Monitoring**: Track coffee machine status, temperature, and connectivity
- **Order Management**: Process transactions with payment tracking and exception handling  
- **Material Inventory**: Monitor ingredient levels with automated low-stock alerts
- **Recipe Management**: Create and deploy coffee recipes with JSON schemas
- **Remote Commands**: Send commands to devices with retry logic and status tracking
- **Alarm System**: Real-time alerts for device issues and low inventory
- **Analytics Dashboard**: KPI tracking with charts and trends
- **Audit Logging**: Comprehensive operation history

### 🏗️ Architecture
- **Flask** web framework with blueprint organization
- **SQLAlchemy** ORM with PostgreSQL database
- **Celery** async task processing with Redis
- **Bootstrap 5** responsive UI with Chart.js
- **RESTful API** with standardized JSON responses
- **Role-based Access Control** (Admin/Ops/Viewer)

## Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL 15+
- Redis 7+

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd coffeeNew
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
   python manage.py create-user --email admin@example.com --password Admin123! --name "Admin User"
   ```

5. **Start the application**
   ```bash
   # Option 1: Using honcho (recommended for development)
   honcho start
   
   # Option 2: Start services individually
   make run-web      # Flask web server
   make run-worker   # Celery worker 
   make run-beat     # Celery beat scheduler
   ```

6. **Access the application**
   - Web Interface: http://localhost:5000
   - Login: admin@example.com / Admin123!
   - API Health: http://localhost:5000/api/v1/health

## Data Models

### Core Entities

- **Merchant** - Coffee shop operators with contact info and status
- **Location** - Physical store locations with GPS coordinates
- **User** - System users with role-based permissions
- **Device** - Coffee machines with real-time status tracking
- **DeviceBin** - Material containers with capacity monitoring

### Inventory & Orders

- **MaterialDictionary** - Ingredient catalog with specifications
- **Order** & **OrderItem** - Transaction tracking with payment status
- **Recipe** - Coffee recipes with JSON schema definitions
- **RecipePackage** - Deployable recipe versions with versioning

### Operations

- **RemoteCommand** - Device command system with lifecycle tracking
- **CommandBatch** - Bulk operation management
- **Alarm** - Alert system for device issues and inventory
- **TaskJob** - Async task tracking with progress monitoring
- **OperationLog** - Comprehensive audit trail

## API Reference

### Base Configuration
- **Base URL**: `/api/v1`
- **Response Format**: `{"ok": true, "data": {...}}` or `{"ok": false, "error": {...}}`
- **Authentication**: Session-based for web UI, optional device tokens for device APIs
- **Rate Limiting**: Applied to critical endpoints

### Key Endpoints

#### Dashboard
```http
GET /api/v1/dashboard/summary?from=&to=&merchant_id=
```
Returns KPIs, trends, and summary statistics.

#### Device Management
```http
GET /api/v1/devices?query=&merchant_id=&model=&status=&page=
GET /api/v1/devices/{id}/summary
POST /api/v1/devices/{id}/commands
```

#### Order Processing
```http
GET /api/v1/orders?from=&to=&device_id=&payment_method=&page=
POST /api/v1/orders/{id}/manual_refund
```

#### Device Communication (Token Optional)
```http
POST /api/v1/devices/register
POST /api/v1/devices/{id}/status
POST /api/v1/devices/{id}/orders/create
```

## Web Interface

### Admin Dashboard
- **Real-time KPIs**: Device status, sales, alerts, material levels
- **Interactive Charts**: Sales trends and device online rates
- **Quick Actions**: Direct navigation to key management functions

### Device Management
- **Device List**: Filterable table with real-time status
- **Bulk Operations**: Send commands to multiple devices
- **Device Details**: Individual device monitoring and control

### Order Management  
- **Transaction History**: Searchable order list with payment status
- **Exception Handling**: Refund processing and error resolution
- **Export Functionality**: CSV downloads for reporting

### Material Management
- **Inventory Dictionary**: CRUD operations for material catalog
- **Device Bin Monitoring**: Real-time capacity and threshold tracking
- **Bulk Import**: CSV upload for material data

## Development

### Project Structure
```
├── app/
│   ├── __init__.py          # Application factory
│   ├── models/              # SQLAlchemy models
│   ├── api/                 # REST API endpoints
│   ├── admin/               # Web interface routes
│   ├── auth/                # Authentication blueprints
│   └── templates/           # Jinja2 templates
├── config.py                # Configuration settings
├── manage.py                # Management commands
├── requirements.txt         # Dependencies
└── Makefile                # Development commands
```

### Management Commands
```bash
python manage.py init-db          # Initialize database
python manage.py seed-demo        # Create sample data
python manage.py create-user      # Create admin user
```

### Development Commands
```bash
make install        # Install dependencies
make run-web        # Start Flask development server
make run-worker     # Start Celery worker
make test           # Run test suite
make lint           # Code quality checks
make format         # Format code with black/isort
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Environment (development/production) | development |
| `DATABASE_URL` | PostgreSQL connection string | postgresql://... |
| `REDIS_URL` | Redis connection string | redis://localhost:6379/0 |
| `SECRET_KEY` | Flask secret key | change-me-in-production |
| `ENABLE_SSE` | Server-sent events for real-time updates | false |
| `ENABLE_DEVICE_TOKEN` | Device token authentication | false |

## Security Features

- **CSRF Protection**: All forms protected with CSRF tokens
- **Role-based Access**: Admin/Ops/Viewer permission levels
- **Session Management**: Secure session handling with Flask-Login
- **Rate Limiting**: Protection against API abuse
- **Audit Logging**: Complete operation history tracking
- **Device Authentication**: Optional token-based device security

## Monitoring & Operations

### Metrics Endpoint
```http
GET /metrics
```
Exposes Prometheus-compatible metrics:
- API error rates and latency
- Device online rates
- Pending command counts
- Daily order volumes

### Logging
- **Structured Logging**: JSON format with contextual information
- **Operation Logs**: Database-stored audit trail
- **Error Tracking**: Comprehensive error handling and reporting

### Health Checks
- **API Health**: `/api/v1/health` - Service status
- **Database**: Connection and query performance
- **Redis**: Cache and task queue status

## Production Deployment

### Docker Support (Planned)
```bash
docker-compose up -d
```

### Manual Deployment
1. **Configure Production Environment**
   ```bash
   export FLASK_ENV=production
   export DATABASE_URL="postgresql://..."
   ```

2. **Start with Gunicorn**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 run:app
   ```

3. **Process Management**
   ```bash
   # Use supervisor or systemd for process management
   # Start web server, celery worker, and celery beat
   ```

### Performance Considerations
- **Database Connection Pooling**: Optimized SQLAlchemy settings
- **Redis Caching**: Session storage and task queuing
- **Static File Serving**: Use nginx or CDN for static assets
- **Load Balancing**: Multiple Gunicorn workers

## Contributing

1. **Code Style**: Use black for formatting, isort for imports
2. **Testing**: Add tests for new features
3. **Documentation**: Update README and API docs
4. **Commit Messages**: Use conventional commit format

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please create an issue in the repository or contact the development team.

---

**Built with ❤️ for coffee shop operators worldwide**