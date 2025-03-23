#!/bin/bash
# Use to print each step: #!/bin/bash -x

# Port 5005
python3 config-server/config-server.py &

# Port 5000
python3 facade-service/facade-service.py &

# Port 5001
python3 messages-service/messages-service.py &

# Launch 3 instances of logging-service
python3 logging-service/logging-service.py --port 5002 &
python3 logging-service/logging-service.py --port 5003 &
python3 logging-service/logging-service.py --port 5004 &

# Launch 3 Hazelcast cluster nodes
hz start -c "hazelcast-client.xml" &
hz start -c "hazelcast-client.xml" &
hz start -c "hazelcast-client.xml" &

wait
