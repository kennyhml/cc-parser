import time

from src.parser import CCParser


def main():
    start = time.perf_counter()
    print("Parsing...")
    try:
        parser = CCParser()
        parser()
    except Exception as e:
        print(f"Ran into an error trying to parse: {e}")
    else:
        time_taken = round(time.perf_counter() - start, 2)
        print(f"Parsing successful! Completed in {time_taken} seconds.")

    input("Press any key to close...")


if __name__ == "__main__":
    main()