# Image Optimizer Service

A service for optimizing images by converting them to WebP or AVIF formats.

## Docker Setup

### Prerequisites

- Docker
- Docker Compose

### Configuration

All configuration is done through environment variables. You can set these in the `.env` file.

#### Available Configuration Options:

**Database Configuration:**
- `POSTGRES_USER`: PostgreSQL username (default: postgres)
- `POSTGRES_PASSWORD`: PostgreSQL password (default: postgres)
- `POSTGRES_DB`: PostgreSQL database name (default: image_optimizer)
- `DB_PORT`: Port to expose PostgreSQL on the host (default: 5432)

**App Configuration:**
- `APP_PORT`: Port to expose the Flask app on the host (default: 5000)
- `APP_WORKERS`: Number of Gunicorn workers for the app (default: 2)

**Worker Configuration:**
- `WORKER_REPLICAS`: Number of worker containers to run (default: 2)
- `WORKER_THREADS`: Number of threads per worker container (default: 2)
- `POLL_INTERVAL`: Interval in seconds for workers to poll for new tasks (default: 1)

**Image Conversion Settings:**
- `STORAGE_PATH`: Path to store converted images (default: /app/images)
- `WEBP_QUALITY`: WebP compression quality (default: 80)
- `WEBP_METHOD`: WebP compression method (default: 4)
- `AVIF_QUALITY`: AVIF compression quality (default: 65)
- `AVIF_SPEED`: AVIF compression speed (default: 6)

### Building and Running

1. Clone the repository:
   ```
   git clone <repository-url>
   cd image_optimizer
   ```

2. Configure the environment variables in the `.env` file (optional):
   ```
   # Edit the .env file to customize settings
   nano .env
   ```

3. Build and start the containers:
   ```
   docker-compose up -d
   ```

4. Check the status of the containers:
   ```
   docker-compose ps
   ```

5. View logs:
   ```
   docker-compose logs -f
   ```

### Scaling Workers

To scale the number of worker containers:

```
# Update the WORKER_REPLICAS in .env file
# Then restart the services
docker-compose up -d
```

### Stopping the Service

```
docker-compose down
```

To remove all data (including the database volume):

```
docker-compose down -v
```

## API Usage

Convert an image to WebP format:
```
GET http://localhost:5000/https://example.com/image.jpg?format=webp
```

Convert an image to AVIF format:
```
GET http://localhost:5000/https://example.com/image.jpg?format=avif
``` 