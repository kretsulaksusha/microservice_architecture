"""
----------------- Optimistic Lock -----------------

Running the script increment_key.py in 3 processes simultaneously.
"""
import sys
import os
import time
import subprocess
import hazelcast
sys.path.insert(0, os.getcwd())
from src.utils.colors import Colors

LOG_TAKEN_TIME = True
LOG_TAKEN_TIME_FILE = "src/optimistic_lock/result.txt"

def log_time(taken_time):
    """
    Function that logs the final value of the key 0 to a file.
    """
    with open(LOG_TAKEN_TIME_FILE, "a", encoding="utf-8") as file:
        file.write(f"{taken_time}\n")

def main():
    """
    Function that demonstrates the usage of the distributed map with optimistic locking.
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
    print(f"\n{Colors.HEADER}Starting value of 'key' 0: {starting_value}{Colors.ENDC}\n")

    start_time = time.time()

    # Run the increment_key.py script in 3 processes
    processes = [subprocess.Popen(["python3", "src/optimistic_lock/increment_key.py"]) for _ in range(3)]

    for p in processes:
        p.wait()

    end_time = time.time()
    taken_time = end_time - start_time

    # Check the final value
    final_value = distributed_map.get(0)
    print(f"\n{Colors.OKGREEN}Final value of 'key' 0: {final_value}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Time taken: {taken_time:.2f} seconds{Colors.ENDC}\n")

    client.shutdown()

    if LOG_TAKEN_TIME:
        log_time(taken_time)


if __name__ == "__main__":
    main()
