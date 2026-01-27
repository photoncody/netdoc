# NetDoc

NetDoc is a lightweight, containerized Network Documentation solution built with Python and FastAPI. It provides a simple API and interface to manage network devices, track IP addresses, and document your infrastructure.

## Features

*   **Device Management**: Track devices with details like Name, Type, Location, IP Address, MAC Address, Serial Number, and more.
*   **Inventory**: Keep track of Manufacturer, Model, OS, and linking information (Uplink Device/Notes).
*   **IP Address Management**:
    *   Track static IPs, DHCP, and Public IPs.
    *   **Subnet Scanner**: Specific tool endpoint to visualize IP usage within a subnet (Free, Used, Reserved, Network, Broadcast).
*   **Import/Export**: Easily import and export your device inventory using CSV files.
*   **Authentication**: Optional simple authentication mechanism.
*   **Containerized**: Easy to deploy with Docker and Docker Compose.

## Getting Started

### Prerequisites

*   Docker
*   Docker Compose

### Quick Start

1.  Clone the repository.
2.  Run with Docker Compose:

    ```bash
    docker compose up -d
    ```

3.  Access the application at `http://localhost:8080`.

## Configuration

### Authentication

By default, NetDoc runs without authentication. To enable it, set the following environment variables in your `compose.yaml` (uncomment the lines) or pass them to the container:

*   `NETDOC_USER`: Your admin username.
*   `NETDOC_PASSWORD`: Your admin password.

Example `compose.yaml` snippet:

```yaml
    environment:
      - NETDOC_USER=admin
      - NETDOC_PASSWORD=securepassword123
```

### Persistence

Data is persisted using a Docker volume named `netdoc_data`. The SQLite database is stored at `/data/netdoc.db` inside the container.

## API Usage

The API is built with FastAPI and provides interactive documentation.

*   **Swagger UI**: `http://localhost:8080/docs`
*   **ReDoc**: `http://localhost:8080/redoc`

### Key Endpoints

*   `GET /api/devices`: List all devices.
*   `POST /api/devices`: Create a new device.
*   `GET /api/devices/export`: Export devices to CSV.
*   `POST /api/devices/import`: Import devices from CSV.
*   `GET /api/tools/subnet`: Scan a subnet (e.g., `?cidr=192.168.1.0/24`).

## Development

To run locally without Docker:

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
2.  Run the server:
    ```bash
    uvicorn app.main:app --reload
    ```
    *Note: You might need to ensure the `/data` directory exists and is writable, or adjust the database path in `app/database.py`.*
