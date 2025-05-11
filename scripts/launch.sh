#!/bin/bash
# Use to print each step: #!/bin/bash -x

python3 consul_service/consul_service.py

# Launch 3 Hazelcast cluster nodes
hz start -c "hazelcast-client.xml" &
hz start -c "hazelcast-client.xml" &
hz start -c "hazelcast-client.xml" &

# Port 5000
python3 facade-service/facade-service.py &

# Launch 2 instances of messages-service
python3 messages-service/messages-service.py --port 5001 &
python3 messages-service/messages-service.py --port 5002 &

# Launch 3 instances of logging-service
python3 logging-service/logging-service.py --port 5003 &
python3 logging-service/logging-service.py --port 5004 &
python3 logging-service/logging-service.py --port 5005 &

wait
