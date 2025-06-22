# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Setup and Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Start the application (with dependency and data file checks)
python start.py

# Direct Flask app start (faster for development)
python app.py
```

### Testing
```bash
# Run all system tests
python tests/test_system.py

# Run specific test modules
python tests/test_admin_system.py      # Admin system tests
python tests/test_enhanced_features.py # Enhanced features tests
python tests/test_api.py              # API endpoint tests

# Run individual test functions
python tests/test_system.py data      # Data loading test
python tests/test_system.py product   # Product search test
python tests/test_system.py ai        # AI response test
```

### Database and Data Management
```bash
# Generate secret key for production
python src/utils/generate_secret_key.py

# Clean start (useful for testing)
python start_clean.py
```

## Architecture Overview

### Core Application Structure
- **app.py**: Main Flask application with 29 RESTful API endpoints
- **src/models/**: Business logic modules organized by domain
- **templates/**: Jinja2 HTML templates for web interface
- **static/**: CSS, JS, and generated barcode images
- **data/**: JSON and CSV data files for persistence

### Key Business Components

**Knowledge Retriever System** (`src/models/knowledge_retriever.py`):
- Orchestrates AI responses using intent analysis and data retrieval
- Integrates with LLM client for natural language processing
- Handles product search, policy queries, and contextual conversations

**Inventory Management** (`src/models/inventory_manager.py`):
- Complete CRUD operations for products with barcode generation
- Integration with storage area and pickup location management
- Code128 barcode generation with PIL image processing
- Stock history tracking and low stock warnings

**Admin Authentication** (`src/models/admin_auth.py`):
- Session-based authentication with secure password hashing
- Token management for API access control

**Data Persistence Layer**:
- JSON files for structured data (inventory, feedback, logs)
- CSV for product catalog
- No database dependency - file-based storage system

### API Architecture
The application exposes 29 RESTful endpoints grouped by functionality:
- Customer chat API (`/api/chat`)
- Admin authentication (`/api/admin/login`, `/api/admin/logout`)
- Inventory management (15 endpoints under `/api/admin/inventory`)
- Count management (8 endpoints for inventory counting)
- Comparison analysis (6 endpoints for data analysis)
- Feedback and export APIs

### Frontend Architecture
- **Customer Interface**: Single-page chat application with real-time messaging
- **Admin Dashboard**: Multi-section SPA with dynamic content loading
- **Responsive Design**: Mobile-first CSS with desktop adaptations
- **Internationalization**: Built-in support for Chinese/English with Flask-Babel

### Data Flow
1. Customer queries → Knowledge Retriever → Intent Analysis → Data Search → LLM Processing → Response
2. Admin operations → Authentication Check → Business Logic → Data Persistence → Audit Logging
3. Inventory updates → Barcode Generation → File Storage → History Tracking

### Key Dependencies
- **Flask**: Web framework with session management and templating
- **pandas**: CSV data processing and manipulation
- **jieba**: Chinese text segmentation for search functionality
- **python-barcode + PIL**: Barcode generation and image processing
- **requests**: LLM API communication (DeepSeek integration)

### Configuration
Environment variables for deployment:
- `LLM_API_KEY`: DeepSeek API authentication
- `SECRET_KEY`: Flask session security
- `FLASK_ENV`: development/production mode
- `PORT`: Server port (default 5000)

### Testing Strategy
- **System Tests**: End-to-end functionality verification
- **API Tests**: All endpoint validation with mock data
- **Feature Tests**: Specific business logic validation
- **Performance Tests**: Response time and load testing

### Security Features
- Password hashing with SHA-256
- Session-based authentication
- CORS configuration for API access
- Operation audit logging
- Input validation and sanitization

## Important Notes

### File Encoding
All data files use UTF-8 encoding. The system includes encoding utilities in `src/utils/encoding_utils.py` for handling Chinese characters in product names and barcode generation.

### Barcode System
Barcode images are generated using Code128 format and stored in `static/barcodes/`. The system automatically generates unique 12-digit codes with the prefix "88" for product identification.

### Data Initialization
The system automatically creates required data files on first run. Key files:
- `data/inventory.json`: Product inventory data
- `data/admin.json`: Admin user accounts (default: admin/admin123)
- `data/operation_logs.json`: Audit trail
- `data/feedback.json`: Customer feedback records

### API Authentication
Admin API endpoints require session-based authentication. The `require_admin_auth()` function validates session tokens before allowing access to protected resources.

### Deployment Configuration
The application is configured for both local development and cloud deployment (Render). The `render.yaml` file contains production deployment settings.