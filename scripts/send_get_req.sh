#!/bin/bash
# Use to print each step: #!/bin/bash -x

mkdir -p scripts/logs

log_file="scripts/logs/send_get_req_log.txt"

echo "Logging time: $(date '+%d-%m-%Y %H:%M:%S')" >> "$log_file" 2>&1

curl -s -X GET http://127.0.0.1:5000/facade | tee -a "$log_file"
