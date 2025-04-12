#!/bin/bash
# Use to print each step: #!/bin/bash -x

# Launch 2 instances of messages-service
python3 messages-service/messages-service.py --port 5001 &
python3 messages-service/messages-service.py --port 5002 &

wait
