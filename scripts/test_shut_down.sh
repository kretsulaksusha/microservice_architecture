#!/bin/bash
# Use to print each step: #!/bin/bash -x

if [ "$1" == "1" ]; then
    PORTS=(5003 5702)
elif [ "$1" == "2" ]; then
    PORTS=(5003 5004 5702 5703)
else
    echo "Usage: $0 [1|2]"
    exit 1
fi

# Collect all processes to kill simultaneously
ALL_PROCESSES=()

for PORT in "${PORTS[@]}"; do
    echo "Checking port $PORT..."

    processes=$(lsof -ti tcp:$PORT -sTCP:LISTEN)

    if [ -z "$processes" ]; then
        echo "No processes are listening on port $PORT."
    else
        echo "Processes listening on port $PORT:"
        lsof -i tcp:$PORT -sTCP:LISTEN -n -P

        # Add processes to the list
        ALL_PROCESSES+=($processes)
    fi
    echo "----------------------------------------"
done

# Kill processes simultaneously
if [ ${#ALL_PROCESSES[@]} -gt 0 ]; then
    echo "Killing all processes: ${ALL_PROCESSES[*]}"
    kill -9 ${ALL_PROCESSES[*]}
    echo "All processes killed."
else
    echo "No processes to kill."
fi

echo "Logging services and Hazelcast nodes have been successfully stopped."
