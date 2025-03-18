"""
----------------- DISTRIBUTED MAP -----------------

This script demonstrates how to use the distributed map data structure in Hazelcast.
"""
import hazelcast

def main():
    """
    Function that demonstrates the usage of the distributed map.
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

    for i in range(1000):
        distributed_map.put(i, i)

    print("Map size:", distributed_map.size())

    # The result of the get request is fetched here
    print("Key, Value")
    for i in range(1000):
        print(f"{i:3d}, {distributed_map.get(i):5d}")
        assert distributed_map.get(i) == i

    client.shutdown()


if __name__ == "__main__":
    main()
