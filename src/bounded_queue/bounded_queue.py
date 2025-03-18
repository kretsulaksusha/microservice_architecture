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

consumer_count = 0

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
        for i in range(1, 101):
            queue.put(i)
            print(f"Producing:  {i:3d}.")
        # Poison pill to stop the consumers
        queue.put("END")
        queue.put("END")

    def consume(consumer_id):
        global consumer_count
        while True:
            size = queue.size().result()
            if size == 0:
                print(f"{Colors.WARNING}Consumer {consumer_id}: Queue is empty. Waiting...{Colors.ENDC}")
                time.sleep(0.5)
                continue

            head = queue.take().result()
            if head == "END":
                break

            print(f"Consumer {consumer_id}: {head:3d}.")
            consumer_count += 1

    producer_thread = threading.Thread(target=produce)
    consumer_thread_1 = threading.Thread(target=consume, args=(1,))
    consumer_thread_2 = threading.Thread(target=consume, args=(2,))

    producer_thread.start()
    consumer_thread_1.start()
    consumer_thread_2.start()

    producer_thread.join()
    consumer_thread_1.join()
    consumer_thread_2.join()

    print(f"\n{Colors.OKCYAN}Consumer count: {consumer_count}.{Colors.ENDC}\n")
    print(f"{Colors.OKGREEN}All threads are done. Shutting down the client...{Colors.ENDC}\n")

    client.shutdown()


if __name__ == "__main__":
    main()
