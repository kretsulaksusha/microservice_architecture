"""
----------------- BOUNDED QUEUE -----------------

This module demonstrates the usage of a distributed queue in Hazelcast.
The queue is bounded, and the producer will block if the queue is full.
"""
import time
import os
import sys
import threading
import hazelcast
sys.path.insert(0, os.getcwd())
from src.utils.colors import Colors

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
    queue = client.get_queue("queue")

    def produce():
        for i in range(1, 15):
            queue.put(i)
            print(f"Producing:  {i:3d}.")
        # Poison pill to stop the consumers
        queue.put("END")
        queue.put("END")

    producer_thread = threading.Thread(target=produce)
    producer_thread.start()
    producer_thread.join()

    time.sleep(3)
    size = queue.size().result()
    print(f"\n{Colors.BOLD}Queue size is {size}{Colors.ENDC}\n")

    print("Values:")
    for _ in range(size):
        print(queue.take().result())

    print(f"\n{Colors.OKGREEN}All threads are done. Shutting down the client...{Colors.ENDC}\n")

    client.shutdown()


if __name__ == "__main__":
    main()
