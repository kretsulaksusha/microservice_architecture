#!/bin/bash
# Use to print each step: #!/bin/bash -x

PORTS=(5000 5001 5002 5003 5004 5005 5701 5702 5703)

ALL_PROCESSES=()

for PORT in "${PORTS[@]}"; do
    echo "Checking port $PORT..."

    processes=$(lsof -ti tcp:$PORT -sTCP:LISTEN)

    if [ -z "$processes" ]; then
        echo "No processes are listening on port $PORT."
    else
        echo "Processes listening on port $PORT:"
        lsof -i tcp:$PORT -sTCP:LISTEN -n -P

        echo "Adding processes to kill list: $processes"
        ALL_PROCESSES+=($processes)
    fi
    echo "----------------------------------------"
done

# Kill processes simultaneously
if [ ${#ALL_PROCESSES[@]} -gt 0 ]; then
    echo "All selected processes: ${ALL_PROCESSES[*]}"
    echo "----------------------------------------"

    # Confirmation
    read -p "Do you want to kill these processes? (y/n): " confirm

    if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
        kill ${ALL_PROCESSES[*]} & wait
        echo "All selected processes are killed."
    else
        echo "Rejected killing all processes."
    fi
else
    echo "No processes to kill."
fi
