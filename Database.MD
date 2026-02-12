# Geographic Data API - Database & Architecture Documentation

## Entity Hierarchy

```mermaid
graph TD
    subgraph hierarchy [Data Model Hierarchy]
        Countries[Countries]
        States[States]
        Cities[Cities]
        Parks[Parks]
    end
    
    Countries -->|"has many"| States
    States -->|"has many"| Cities
    Parks -.->|"located in"| States
```

---

## API Route Structure

```mermaid
flowchart LR
    subgraph flat [Flat Routes]
        C1["/cities"]
        C2["/cities/id"]
        S1["/states"]
        P1["/parks"]
        P2["/parks/id"]
        P3["/parks/state/code"]
        CO1["/countries"]
        CO2["/countries/code"]
    end
    
    subgraph nested [Nested Routes]
        N1["/countries/code/states"]
        N2["/countries/code/states/state_code"]
        N3["/countries/code/states/state_code/cities"]
    end
```

---

## Complete Endpoint Reference

| Endpoint | GET | POST | PUT | DELETE |
|----------|-----|------|-----|--------|
| **Countries** |||||
| `/countries` | List all | Create | - | - |
| `/countries/{code}` | Get one | - | Update | Delete |
| `/countries/{code}/states` | List states | Create state | - | - |
| `/countries/{code}/states/{state}` | Get state | - | Update | Delete |
| `/countries/{code}/states/{state}/cities` | List cities | Create city | - | - |
| **Cities (flat)** |||||
| `/cities` | List all | - | - | - |
| `/cities/{id}` | Get one | - | Update | Delete |
| **States (flat - search only)** |||||
| `/states?country_code=X&state_code=Y` | Filter/search | - | - | - |
| **Parks** |||||
| `/parks` | List all | Create | - | - |
| `/parks/{id}` | Get one | - | Update | Delete |
| `/parks/state/{code}` | By state | - | - | - |
| **Utility** |||||
| `/hello` | Health check | - | - | - |
| `/statistics` | DB stats | - | - | - |
| `/endpoints` | List routes | - | - | - |
| `/delete-all-data` | - | - | - | Wipe DB |

---

## Request Flow

```mermaid
sequenceDiagram
    participant Client
    participant Flask as Flask API
    participant Queries as queries.py
    participant MongoDB
    
    Client->>Flask: POST /countries/US/states
    Flask->>Flask: handle_errors decorator
    Flask->>Queries: sqry.create(data)
    Queries->>MongoDB: insert document
    MongoDB-->>Queries: inserted_id
    Queries-->>Flask: state_code, country_code
    Flask-->>Client: 201 Created
```

---

## Design Decisions

| Aspect | Implementation |
|--------|----------------|
| **Create cities** | Only via nested route `/countries/{c}/states/{s}/cities` |
| **Create states** | Only via nested route `/countries/{c}/states` |
| **Create countries** | Flat route `POST /countries` |
| **Create parks** | Flat route `POST /parks` |
| **Search states** | Query params on `/states?country_code=X` |
| **Primary keys** | Countries: `code`, States: `country_code+state_code`, Cities/Parks: `_id` |

---

## Database Collections

| Collection | Primary Key | Example Document |
|------------|-------------|------------------|
| `countries` | `code` | `{"code": "US", "name": "United States", "capital": "Washington D.C."}` |
| `states` | `country_code` + `state_code` | `{"country_code": "US", "state_code": "NY", "name": "New York"}` |
| `cities` | `_id` (ObjectId) | `{"name": "NYC", "state_code": "NY", "country_code": "US"}` |
| `parks` | `_id` (ObjectId) | `{"name": "Yellowstone", "state_code": "WY"}` |

---

## Data Flow Architecture

```mermaid
flowchart TB
    subgraph client [Client Layer]
        Web[Web Browser]
        API_Client[API Client]
    end
    
    subgraph server [Server Layer]
        Flask[Flask App]
        Endpoints[endpoints.py]
        Queries[queries.py modules]
    end
    
    subgraph data [Data Layer]
        DBConnect[db_connect.py]
        MongoDB[(MongoDB Atlas)]
    end
    
    Web --> Flask
    API_Client --> Flask
    Flask --> Endpoints
    Endpoints --> Queries
    Queries --> DBConnect
    DBConnect --> MongoDB
```
