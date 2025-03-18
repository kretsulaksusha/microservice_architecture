"""
----------------- PROCESSING RESULT -----------------

This script processes the final values of the distributed map without locks
and calculates the average final value.
"""
LOG_FINAL_VALUE_FILE = "src/no_locks/result.txt"

def main():
    """
    Function that demonstrates the usage of the distributed map without locks.
    """
    with open(LOG_FINAL_VALUE_FILE, "r", encoding="utf-8") as file:
        data = [int(val) for val in file.readlines()]

    print(f"Average final value: {round(sum(data)/len(data))}.")


if __name__ == "__main__":
    main()
