"""
----------------- PROCESSING RESULT -----------------

This script processes taken times of the distributed map with pessimistic lock
and calculates the average taken time.
"""
LOG_TAKEN_TIME_FILE = "src/pessimistic_lock/result.txt"

def main():
    """
    Function that demonstrates the usage of the distributed map with pessimistic lock.
    """
    with open(LOG_TAKEN_TIME_FILE, "r", encoding="utf-8") as file:
        data = [float(val) for val in file.readlines()]

    print(f"Average taken time: {round(sum(data)/len(data), 2)} seconds.")


if __name__ == "__main__":
    main()
