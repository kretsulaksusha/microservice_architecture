"""
----------------- DISTRIBUTED MAP WITHOUT LOCKS -----------------

Incrementing the value of a key 0 in a distributed map without using locks.
"""
import hazelcast

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

    # Get or create the "distributed-map" on the cluster
    # blocking() - sync map, all operations are blocking
    distributed_map = client.get_map("distributed-map").blocking()

    iterations = 10000
    key = 0

    for _ in range(iterations):
        current_value = distributed_map.get(key) or 0
        distributed_map.put(0, current_value + 1)

    client.shutdown()


if __name__ == "__main__":
    main()
