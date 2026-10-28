# Umucyo Backend

## Overview
Umucyo is a tea-cooperative platform designed to improve transparency in tea delivery records, quality assessment, produce pricing and farmer payments in Rwanda. It helps cooperatives maintain reliable transaction records while giving farmers access to delivery information, payment updates, and a channel for reporting questions or concerns through basic mobile phones.
This repository contains the backend API for Umucyo, built with FastAPI. It provides the foundation for managing cooperative users, farmer registrations, collection points, weighing devices, produce delivery records, price history, payment transactions, farmer communications, operational tasks and audit logs.
The backend is designed to support integrations with IoT weighing devices, SMS and USSD communication services, and a mobile-money payment provider.

## Key Features
- **Cooperative and user management:** Organizes cooperative accounts, administrators and agents, with role-based access to cooperative operations.
- **Farmer registration:** Maintains farmer contact details and cooperative affiliations for delivery records, SMS notifications and USSD communication.
- **Collection point and agent management:** Records collection points, registers weighing devices and tracks agent assignments over time.
- **Delivery and weight records:** Stores produce deliveries, including gross weight, rejected weight, accepted weight, the responsible agent and the applicable produce price.
- **Produce price management:** Maintains cooperative prices and their effective periods so that delivery records can reference the applicable price.
- **Payment transaction management:** Records payment periods, quantities, amounts, approval information, payment-provider references and transaction outcomes.
- **SMS and USSD communication:** Provides a data model for recording incoming farmer reports and questions, outgoing notifications, message statuses and provider references.
- **Operational task management:** Allows reported non-financial issues to be associated with tasks assigned to cooperative agents.
- **Audit logging:** Records important changes to operational and financial data to support traceability and accountability.

## Data Model
The database design is documented in the project's Entity Relationship Diagram (ERD). At a high level, the schema consists of the following core entities:
| Entity | Purpose |
|---|---|
| `cooperative` | Stores cooperative details and account status. |
| `user` | Stores cooperative administrator and agent accounts, roles, and authentication data. |
| `farmer` | Stores farmer registration details, contact information, and cooperative affiliation. |
| `collection_point` | Stores locations where farmers deliver tea for weighing and assessment. |
| `agent_assignment` | Tracks agent assignments to collection points, including assignment periods. |
| `weighing_device` | Registers weighing devices and associates them with collection points. |
| `produce_record` | Stores delivery quantities, assessment details, applicable prices, and delivery information. |
| `produce_price` | Stores cooperative tea prices and the periods during which they apply. |
| `payment_transaction` | Stores payment periods, quantities, amounts, approval details, and provider transaction information. |
| `message_log` | Stores inbound and outbound SMS/USSD communications and their processing statuses. |
| `task` | Tracks operational tasks assigned to agents, including tasks originating from farmer reports. |
| `audit_log` | Records important changes to system data for auditing and accountability. |

## Tech Stack
- **Backend framework:** FastAPI
- **Programming language:** Python
- **Data validation:** Pydantic
- **Database:** Relational SQL database PostgreSQL 

## Prerequisites
Before running the backend, ensure you have:
- Python installed at a version supported by the project's dependencies.
- Access to a configured SQL database.
- `pip` or another compatible Python package installation tool.
- The project's required environment variables configured.
- API credentials for external services.
- Access to compatible weighing hardware and its communication setup if testing IoT functionality.

## Installation
Clone the repository and navigate to the backend directory:
```
git clone <BACKEND_REPOSITORY_URL>
cd <BACKEND_DIRECTORY>
```
Create a virtual environment:
```
python -m venv .venv
```
Activate a virtual environment:
```
source .venv/bin/activate
```

## Running the Application
Start the FastAPI application using Uvicorn:
```bash
uvicorn main:app --reload
```
The API will normally be available at:
- **Base URL:** `http://localhost:8000`
- **Swagger UI:** `http://localhost:8000/docs`

## Project Structure
The backend repository is organized into the following main components:
```text
sulwe-backend/
├── README.md
├── database.py
├── main.py
├── pyproject.toml
├── models/          
├── repositories/    
├── routers/        
├── schemas/         
├── services/        
└── tests/           
```

### Directory Responsibilities
- **main.py** Application entry point, FastAPI initialization, and router registration.
- **database.py** Database connection and session configuration.
- **models** Definitions of the entities represented in the database.
- **repositories/** Database queries and persistence operations.
- **routers/** HTTP endpoints for backend features.
- **schemas/** Data validation and serialization using the project's schema definitions.
- **services/** Business rules and integrations with external systems.
- **tests/** Automated tests for API endpoints, business logic, and database operations.

## Testing
Run the backend tests using:
```bash
pytest -v
```
Tests should cover:
- Cooperative, administrator, agent, and farmer registration.
- Authentication and role-based access controls.
- Collection point and agent assignment rules.
- Delivery record creation and weight validation.
- Produce price selection based on effective dates.
- Payment calculations, approvals, and payment status handling.
- SMS/USSD message processing and issue tracking.
- Task assignment and completion.
- Audit logging and data access restrictions.
