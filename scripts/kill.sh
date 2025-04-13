#!/bin/bash
# Use to print each step: #!/bin/bash -x

PORTS=(5000 5001 5002 5003 5004 5005 5006 5701 5702 5703)

ALL_PROCESSES=()

for PORT in "${PORTS[@]}"; do
    echo "Checking port $PORT..."

    # Use process substitution to avoid subshell
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

# Kill processes simultaneously
if [ ${#ALL_PROCESSES[@]} -gt 0 ]; then
    echo "All selected processes: ${ALL_PROCESSES[*]}"
    echo "----------------------------------------"

    # Confirmation
    read -rp "Do you want to kill these processes? (y/n): " confirm

    if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
        kill ${ALL_PROCESSES[*]} & wait
        echo "All selected processes are killed."
    else
        echo "Rejected killing all processes."
    fi
else
    echo "No processes to kill."
fi
