#!/bin/bash
# Use to print each step: #!/bin/bash -x

PORTS=(5000 5001 5002 5003 5004 5005 5006 5701 5702 5703 8500)
ALL_PROCESSES=()
DOCKER_CONTAINERS=()

echo "========== Checking ports for local processes =========="
for PORT in "${PORTS[@]}"; do
    echo "Checking port $PORT..."

    while read -r line; do
        process_name=$(echo "$line" | awk '{print $1}')
        pid=$(echo "$line" | awk '{print $2}')
        user=$(echo "$line" | awk '{print $3}')
        name_field=$(echo "$line" | awk '{print $9}')

        # Skip header line
        if [[ "$process_name" == "COMMAND" ]]; then
            continue
        fi

        # Condition: localhost bindings OR Hazelcast java process
        if [[ "$name_field" == *"127.0.0.1"* || ( "$name_field" == "*"* && "$process_name" == "java" ) ]]; then
            if [[ ! " ${ALL_PROCESSES[*]} " =~ " $pid " ]]; then
                ALL_PROCESSES+=("$pid")
                echo "Marked for kill: $process_name (PID $pid) - $name_field"
            fi
        fi
    done < <(lsof -nP -i tcp:"$PORT" -sTCP:LISTEN 2>/dev/null)

    echo "----------------------------------------"
done

echo "========== Checking Docker containers =========="

# Optional: Filter containers based on exposed ports (or remove filter to stop all)
for PORT in "${PORTS[@]}"; do
    container_ids=$(docker ps --format '{{.ID}} {{.Ports}}' | grep "$PORT" | awk '{print $1}')
    for cid in $container_ids; do
        if [[ ! " ${DOCKER_CONTAINERS[*]} " =~ " $cid " ]]; then
            DOCKER_CONTAINERS+=("$cid")
            echo "Docker container marked for stop: $cid (Port $PORT)"
        fi
    done
done

# Summary
echo
echo "========== Summary =========="
[[ ${#ALL_PROCESSES[@]} -gt 0 ]] && echo "Processes to kill: ${ALL_PROCESSES[*]}"
[[ ${#DOCKER_CONTAINERS[@]} -gt 0 ]] && echo "Docker containers to stop: ${DOCKER_CONTAINERS[*]}"
[[ ${#ALL_PROCESSES[@]} -eq 0 && ${#DOCKER_CONTAINERS[@]} -eq 0 ]] && echo "Nothing to stop."

# Confirm
if [[ ${#ALL_PROCESSES[@]} -gt 0 || ${#DOCKER_CONTAINERS[@]} -gt 0 ]]; then
    echo "----------------------------------------"
    read -rp "Do you want to proceed with stopping these? (y/n): " confirm

    if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
        if [[ ${#ALL_PROCESSES[@]} -gt 0 ]]; then
            kill "${ALL_PROCESSES[@]}" & wait
            echo "Killed all selected local processes."
        fi
        if [[ ${#DOCKER_CONTAINERS[@]} -gt 0 ]]; then
            docker stop "${DOCKER_CONTAINERS[@]}"
            echo "Stopped all selected Docker containers."
        fi
    else
        echo "Aborted."
    fi
fi
