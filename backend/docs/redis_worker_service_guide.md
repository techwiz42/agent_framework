# Redis Worker Service Guide

This document explains how the Redis worker service operates in the Cyberiad system and how to troubleshoot common issues.

## Overview

The Cyberiad backend uses Redis for message queuing and processing, particularly for agent-related tasks. This architecture allows the web server to remain responsive while offloading time-consuming operations to background workers.

### Key Components:

1. **Redis Server**: External service running on 209.38.173.235:6379
2. **Redis Service**: Interface for interacting with Redis queues (app/services/redis/redis_service.py)
3. **Redis Worker**: Background process that consumes and processes tasks from Redis queues (app/services/redis/worker.py)
4. **Agent Task Worker**: Handler specifically for agent-related tasks (app/services/redis/agent_task_worker.py)

## How It Works

1. When a user sends a message to an agent via websocket, the message is enqueued in the Redis `queue:agent_tasks` queue
2. The Redis worker process continuously monitors this queue
3. When a new task arrives, the worker dequeues it and passes it to the appropriate handler
4. For agent tasks, the handler processes the request, invokes the agent, and sends the response back through the websocket

## Installation

### Production Environment

1. Copy the service file to the systemd directory:
   ```bash
   sudo cp cyberiad-redis-worker-prod.service /etc/systemd/system/
   ```

2. Reload systemd configuration:
   ```bash
   sudo systemctl daemon-reload
   ```

3. Enable the service to start at boot:
   ```bash
   sudo systemctl enable cyberiad-redis-worker-prod.service
   ```

4. Start the service:
   ```bash
   sudo systemctl start cyberiad-redis-worker-prod.service
   ```

### Development Environment

1. Copy the service file to the systemd directory:
   ```bash
   sudo cp cyberiad-redis-worker-dev.service /etc/systemd/system/
   ```

2. Reload systemd configuration:
   ```bash
   sudo systemctl daemon-reload
   ```

3. Enable the service to start at boot:
   ```bash
   sudo systemctl enable cyberiad-redis-worker-dev.service
   ```

4. Start the service:
   ```bash
   sudo systemctl start cyberiad-redis-worker-dev.service
   ```

## Service Management

### Check Service Status

```bash
# For production
sudo systemctl status cyberiad-redis-worker-prod.service

# For development
sudo systemctl status cyberiad-redis-worker-dev.service
```

### View Service Logs

```bash
# For production
sudo journalctl -u cyberiad-redis-worker-prod.service

# For development
sudo journalctl -u cyberiad-redis-worker-dev.service

# Follow logs in real-time
sudo journalctl -u cyberiad-redis-worker-prod.service -f
```

### Restart the Service

```bash
# For production
sudo systemctl restart cyberiad-redis-worker-prod.service

# For development
sudo systemctl restart cyberiad-redis-worker-dev.service
```

## Troubleshooting

### No response from agents

If agents aren't responding to user queries, check the following:

1. **Verify Redis connection**:
   ```
   python redis_test.py
   ```
   This should show successful ping, enqueue, and dequeue operations.

2. **Check queue status**:
   ```
   python check_redis_queues.py
   ```
   This shows the current length of all queues.

3. **Verify worker is running**:
   ```
   ps aux | grep redis_worker
   ```
   You should see a running process for start_redis_worker.py.

4. **Check thread agents**:
   ```
   python check_thread_agents.py
   ```
   This confirms that agents are properly registered with conversations in the database.

5. **Common issues**:
   - The queue appears empty but tasks aren't processed: Redis worker is running but failing silently
   - Tasks stay in the queue: Worker not running or encountering errors
   - "No agent found for conversation": Thread agent not registered in the database for the conversation

If the service fails to start:

1. Check the logs for error messages:
   ```bash
   sudo journalctl -u cyberiad-redis-worker-prod.service -n 100
   ```

2. Verify that the Redis server is running:
   ```bash
   redis-cli -h 209.38.173.235 -p 6379 -a "3559ScootRedis" ping
   ```

3. Ensure the Python virtual environment exists and has all dependencies installed:
   ```bash
   /home/trurl/.virtualenvs/cyberia/bin/python -c "import redis.asyncio"
   ```

### Debugging and Maintenance

1. **Clear Redis queues**:
   ```
   python clear_redis_queues.py
   ```
   This is useful when there are stuck or invalid items in the queues.

2. **Manual worker testing**:
   ```
   python debug_worker.py
   ```
   This manually runs the worker process with verbose logging.

3. **Restart the worker**:
   ```
   kill -9 $(pgrep -f start_redis_worker.py)
   python start_redis_worker.py
   ```

## Architecture Considerations

### Why Use Redis?

- **Scalability**: Redis allows us to distribute workloads across multiple processes or servers
- **Reliability**: Tasks are persisted in Redis, so they won't be lost if a worker crashes
- **Performance**: The main web server remains responsive by offloading heavy processing

### Potential Improvements

- **Worker Monitoring**: Add monitoring for worker health and task processing metrics
- **Retry Mechanism**: Implement automatic retries for failed tasks
- **Dead Letter Queue**: Move failed tasks to a separate queue for inspection
- **Multiple Workers**: Scale by running multiple worker processes

## Implementation Notes

- The agent task worker is registered with the main worker in `register_with_worker()`
- The worker uses a blocking dequeue (`blpop`) with a timeout to efficiently wait for new tasks
- Error handling is implemented to ensure that the worker process continues running even if individual tasks fail
- Websocket connections are managed through the `connection_health` service