# Geographic Data API

A RESTful API server for managing geographic data (countries, states, and cities) built with Flask and MongoDB.

## Features

- **CRUD Operations**: Full create, read, update, delete support for countries, states, and cities
- **Natural Keys**: Uses ISO country codes and state codes as primary keys instead of arbitrary IDs
- **Nested Routes**: States accessible via `/countries/{code}/states/{state_code}`
- **Swagger UI**: Auto-generated API documentation at `/`
- **MongoDB Backend**: Persistent storage with proper indexing

## Tech Stack

- **Framework**: Flask + Flask-RESTX
- **Database**: MongoDB
- **Testing**: pytest with coverage reporting
- **Linting**: flake8
- **CI/CD**: GitHub Actions

## Project Structure

```
├── server/           # API endpoints and models
├── cities/           # City queries and business logic
├── states/           # State queries and business logic
├── countries/        # Country queries and business logic
├── data/             # Database connection and utilities
├── security/         # Authentication and security
└── examples/         # Example code and forms
```

## Getting Started

### Prerequisites

- Python 3.13+
- MongoDB (local or Docker)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Software-Engineering
   ```

2. Set up the development environment:
   ```bash
   make dev_env
   ```

3. Set PYTHONPATH:
   ```bash
   export PYTHONPATH=$(pwd)
   ```

### Running the Server

**Development mode:**
```bash
./local.sh
```
The server will start at `http://127.0.0.1:8000`

**Access Swagger UI:**
Open `http://127.0.0.1:8000` in your browser for interactive API documentation.

## API Endpoints

### Countries
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/countries` | List all countries |
| POST | `/countries` | Create a new country |
| GET | `/countries/{code}` | Get country by ISO code |
| PUT | `/countries/{code}` | Update a country |
| DELETE | `/countries/{code}` | Delete a country |

### States
| Method | Endpoint | Description |curl http://localhost:8000/countries/SU
|--------|----------|-------------|
| GET | `/states` | List all states |
| POST | `/states` | Create a new state |
| GET | `/countries/{country_code}/states` | List states in a country |
| GET | `/countries/{country_code}/states/{state_code}` | Get a specific state |
| PUT | `/countries/{country_code}/states/{state_code}` | Update a state |
| DELETE | `/countries/{country_code}/states/{state_code}` | Delete a state |

### Cities
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/cities` | List all cities |
| POST | `/cities` | Create a new city |
| GET | `/cities/{id}` | Get city by MongoDB ObjectId |
| PUT | `/cities/{id}` | Update a city |
| DELETE | `/cities/{id}` | Delete a city |
| GET | `/cities/by-state/{state_code}` | List cities in a state |

### Utility
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/hello` | Health check |
| GET | `/statistics` | Database statistics |
| GET | `/endpoints` | List all endpoints |

## Development

### Running Tests

Run all tests with coverage:
```bash
make all_tests
```

Run tests for a specific module:
```bash
cd server && make tests
cd cities && make tests
cd states && make tests
cd countries && make tests
```

### Linting

```bash
cd <module> && make lint
```

### Building for Production

```bash
make prod
```

## Database Schema

### Countries
- `code` (string, primary key): ISO 2-3 letter code (e.g., "US", "CN")
- `name` (string): Country name

### States
- `state_code` (string): State/province code (e.g., "NY", "CA")
- `country_code` (string): Parent country's ISO code
- `name` (string): State name
- Primary key: composite of `(state_code, country_code)`

### Cities
- `_id` (ObjectId, primary key): MongoDB auto-generated ID
- `name` (string): City name
- `state_code` (string): Parent state code
- `population` (number, optional): City population

## License

See [LICENSE](LICENSE) for details.
