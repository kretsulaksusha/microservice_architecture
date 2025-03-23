#!/bin/bash
# Use to print each step: #!/bin/bash -x

mkdir -p scripts/logs

log_file="scripts/logs/send_post_req_log.txt"

echo "Logging time: $(date '+%d-%m-%Y %H:%M:%S')" >> "$log_file" 2>&1

for i in {1..10}; do
    response=$(curl -s -X POST 'http://127.0.0.1:5000/facade' \
         -H "Content-Type: application/json" \
         -d "{\"msg\": \"msg$i\"}")

    echo "$response" >> "$log_file"
    
    status=$(echo "$response" | grep -o '"status": *"[^"]*"' | cut -d '"' -f4)

    if [ "$status" == "success" ]; then
        echo "Sent: msg$i - SUCCESS"
    else
        echo "Sent: msg$i - FAILED"
    fi

done
