#!/bin/bash
# Complete script to check shared PostgreSQL usage between bots
# Usage: ssh mrbzzz@74.208.125.51 'bash -s' < check_shared_postgres.sh

set -e

echo "🔍 COMPREHENSIVE SHARED POSTGRESQL CHECK"
echo "========================================"
echo "Server: $(hostname -I | awk '{print $1}') ($(hostname))"
echo "Time: $(date)"
echo ""

# 1. Check Docker installation
echo "🐳 DOCKER STATUS:"
if command -v docker &> /dev/null; then
    echo "✅ Docker installed: $(docker --version)"
    docker_running=$(docker info >/dev/null 2>&1 && echo "yes" || echo "no")
    if [ "$docker_running" = "yes" ]; then
        echo "✅ Docker daemon running"
    else
        echo "❌ Docker daemon not running"
        exit 1
    fi
else
    echo "❌ Docker not installed"
    exit 1
fi

echo ""
echo "📦 ALL CONTAINERS:"
docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "🗄️ POSTGRESQL CONTAINERS:"
postgres_containers=$(docker ps --format "{{.Names}}" | grep -i postgres || echo "none")
if [ "$postgres_containers" != "none" ]; then
    echo "Found PostgreSQL containers:"
    docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" | grep -i postgres
else
    echo "❌ No PostgreSQL containers found"
fi

echo ""
echo "🔍 SHARED POSTGRESQL CHECK:"
if docker ps --format "{{.Names}}" | grep -q "vps_postgres_shared"; then
    echo "✅ Shared PostgreSQL container found: vps_postgres_shared"
    
    # Check container details
    echo ""
    echo "📊 Container details:"
    docker inspect vps_postgres_shared --format "
Image: {{.Config.Image}}
Status: {{.State.Status}}
Memory: {{.HostConfig.Memory}}
Ports: {{range .NetworkSettings.Ports}}{{.}}{{end}}"
    
    # Check databases
    echo ""
    echo "🗃️ Databases in shared PostgreSQL:"
    if docker exec vps_postgres_shared psql -U postgres -c "\l" 2>/dev/null; then
        echo "✅ Database connection successful"
    else
        echo "❌ Cannot connect to PostgreSQL"
    fi
    
    # Check active connections
    echo ""
    echo "🔗 Active database connections:"
    docker exec vps_postgres_shared psql -U postgres -c "
    SELECT 
        datname as database,
        usename as user,
        application_name,
        client_addr,
        state
    FROM pg_stat_activity 
    WHERE datname NOT IN ('template0', 'template1', 'postgres')
    ORDER BY datname;" 2>/dev/null || echo "❌ Cannot retrieve connection info"
    
    # Check database sizes
    echo ""
    echo "💾 Database sizes:"
    docker exec vps_postgres_shared psql -U postgres -c "
    SELECT 
        datname as database_name,
        pg_size_pretty(pg_database_size(datname)) as size,
        (SELECT count(*) FROM pg_stat_activity WHERE datname = d.datname) as connections
    FROM pg_database d 
    WHERE datname NOT IN ('template0', 'template1', 'postgres')
    ORDER BY pg_database_size(datname) DESC;" 2>/dev/null || echo "❌ Cannot retrieve database sizes"
    
else
    echo "❌ Shared PostgreSQL container 'vps_postgres_shared' not found"
fi

echo ""
echo "🤖 BOT CONTAINERS CHECK:"

# Find all bot containers
bot_containers=$(docker ps --format "{{.Names}}" | grep -E "(hello|bot)" || echo "none")
if [ "$bot_containers" != "none" ]; then
    echo "Found bot containers:"
    echo "$bot_containers" | while read -r container; do
        echo ""
        echo "Bot: $container"
        echo "  Status: $(docker ps --format "{{.Status}}" --filter "name=$container")"
        
        # Check DATABASE_URL
        db_url=$(docker exec "$container" env 2>/dev/null | grep DATABASE_URL || echo "Not found")
        echo "  DATABASE_URL: $db_url"
        
        # Check if using shared postgres
        if echo "$db_url" | grep -q "postgres-shared"; then
            echo "  ✅ Using shared PostgreSQL"
        elif echo "$db_url" | grep -q "postgres"; then
            echo "  ⚠️  Using PostgreSQL but not shared"
        else
            echo "  ❌ No PostgreSQL connection found"
        fi
        
        # Check port configuration
        server_port=$(docker exec "$container" env 2>/dev/null | grep SERVER_PORT || echo "SERVER_PORT=8000")
        echo "  Port: $server_port"
    done
else
    echo "❌ No bot containers found"
fi

echo ""
echo "🌐 DOCKER NETWORKS:"
networks=$(docker network ls --format "{{.Name}}" | grep -i shared || echo "none")
if [ "$networks" != "none" ]; then
    echo "Shared networks found:"
    docker network ls --format "table {{.Name}}\t{{.Driver}}\t{{.Scope}}" | grep -i shared
    
    # Check network details
    echo ""
    echo "🔗 Network connections:"
    docker network ls --format "{{.Name}}" | grep -i shared | while read -r network; do
        echo "Network: $network"
        docker network inspect "$network" --format "{{range .Containers}}  {{.Name}}: {{.IPv4Address}}{{end}}" 2>/dev/null || echo "  Cannot inspect network"
    done
else
    echo "❌ No shared networks found"
fi

echo ""
echo "🔧 RESOURCE USAGE:"
echo "Memory usage by containers:"
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.CPUPerc}}" | head -20

echo ""
echo "💽 System resources:"
echo "Total memory: $(free -h | awk '/^Mem:/ {print $2}')"
echo "Available memory: $(free -h | awk '/^Mem:/ {print $7}')"
echo "Disk usage: $(df -h / | awk 'NR==2 {print $5 " used of " $2}')"

echo ""
echo "🏗️ DEPLOYMENT DIRECTORIES:"
echo "Home directory contents:"
ls -la "$HOME/" | grep -E "(hello|bot)" || echo "No bot directories found"

echo ""
echo "📋 CONFIGURATION FILES:"
for dir in "$HOME"/hello-* "$HOME"/*bot*; do
    if [ -d "$dir" ]; then
        echo "Directory: $dir"
        if [ -f "$dir/.env" ]; then
            echo "  .env file exists"
            # Show non-sensitive env vars
            grep -E "^(PROJECT_NAME|ENVIRONMENT|SERVER_PORT|DEBUG)" "$dir/.env" 2>/dev/null || echo "  No standard env vars found"
        fi
        if [ -f "$dir/docker-compose.yml" ]; then
            echo "  docker-compose.yml exists"
        fi
    fi
done

echo ""
echo "🔍 PORT USAGE:"
echo "Active ports:"
netstat -tlnp 2>/dev/null | grep -E ":(8000|8001|8002|5432|5433)" || echo "Standard bot ports not found"

echo ""
echo "========================================"
if docker ps --format "{{.Names}}" | grep -q "vps_postgres_shared"; then
    if docker ps --format "{{.Names}}" | grep -E "(hello|bot)" >/dev/null; then
        echo "✅ RESULT: Shared PostgreSQL setup appears to be working"
        echo "✅ Found shared PostgreSQL and bot containers"
    else
        echo "⚠️  RESULT: Shared PostgreSQL exists but no bot containers found"
    fi
else
    echo "❌ RESULT: Shared PostgreSQL setup not detected"
    echo "❌ Consider running shared PostgreSQL setup"
fi
echo "🏁 Check completed at $(date)"