"""
----------------- DISTRIBUTED MAP WITHOUT LOCKS -----------------

Running the script increment_key.py in 3 processes simultaneously.
"""
import sys
import os
import subprocess
import hazelcast
sys.path.insert(0, os.getcwd())
from src.utils.colors import Colors

LOG_FINAL_VALUE = True
LOG_FINAL_VALUE_FILE = "src/no_locks/result.txt"

def log_final_value(final_value):
    """
    Function that logs the final value of the key 0 to a file.
    """
    with open(LOG_FINAL_VALUE_FILE, "a", encoding="utf-8") as file:
        file.write(f"{final_value}\n")

def main():
    """
    Function that demonstrates the usage of the distributed map without locks.
    """
    client = hazelcast.HazelcastClient(
        cluster_name="dev",
        cluster_members=[
            "127.0.0.1:5701",
            "127.0.0.1:5702",
            "127.0.0.1:5703",
        ],
        lifecycle_listeners=[
            lambda state: print("Lifecycle event >>>", state),
        ]
    )

    distributed_map = client.get_map("distributed-map").blocking()
    distributed_map.put(0, 0)

    starting_value = distributed_map.get(0)
    print(f"\n\n{Colors.HEADER}Starting value of 'key' 0: {starting_value}{Colors.ENDC}\n\n")

    # Run the increment_key.py script in 3 processes
    processes = [subprocess.Popen(["python3", "src/no_locks/increment_key.py"]) for _ in range(3)]

    for p in processes:
        p.wait()

    # Check the final value
    final_value = distributed_map.get(0)
    print(f"\n\n{Colors.OKGREEN}Final value of 'key' 0: {final_value}{Colors.ENDC}\n\n")

    client.shutdown()

    if LOG_FINAL_VALUE:
        log_final_value(final_value)


if __name__ == "__main__":
    main()
