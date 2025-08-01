# src/dfs_key_finder.py

# Install required packages (these are already in the main installation list)
# !pip install bitcoinlib tqdm

from bitcoinlib.keys import Key # For Bitcoin key operations
from tqdm import tqdm # For progress bar
import hashlib
import base58
import os
from collections import Counter # Used in build_prefix_set (implicitly via Counter)
from multiprocessing import Pool, cpu_count # For parallel processing in building prefixes

# --- Key Conversion and Address Derivation ---
def dec_key_to_LR_path(key_int, total_bits=32):
    """
    Converts a decimal key integer to a binary path string of 'L' (0) / 'R' (1).
    The path length is fixed by total_bits.
    """
    # Format to a fixed-length binary string, padded with leading zeros
    bin_str = format(key_int, f'0{total_bits}b')
    path = ''.join(['L' if bit == '0' else 'R' for bit in bin_str])
    return path

def node_path_to_privkey_in_range(path, start_range_int, end_range_int):
    """
    Determines the private key integer corresponding to a given binary path
    within a specified numerical range. This is a binary search-like logic.
    """
    current_start = start_range_int
    current_end = end_range_int

    for direction in path:
        mid = (current_start + current_end) // 2
        if direction == 'L':
            current_end = mid
        else:  # 'R'
            current_start = mid + 1
    # The key is the midpoint of the final narrowed range
    return (current_start + current_end) // 2

def private_key_to_address(privkey_hex):
    """
    Converts a hexadecimal private key to its Bitcoin address using bitcoinlib.
    """
    try:
        key = Key(import_key=privkey_hex)
        return key.address()
    except Exception as e:
        # print(f"Error converting key {privkey_hex} to address: {e}") # Uncomment for debug
        return None

# --- Prefix Filtering Logic ---
def read_private_keys_dec(file_path):
    """Reads decimal private keys from a file, one per line."""
    with open(file_path, 'r') as f:
        lines = f.readlines()
    keys_dec = [int(line.strip()) for line in lines if line.strip().isdigit()]
    print(f"Loaded {len(keys_dec)} private keys from {file_path}")
    return keys_dec

def build_prefix_set(keys_dec, max_prefix_len=10, total_bits=32):
    """
    Builds a set of "allowed prefixes" (binary paths 'L'/'R') from a list of decimal keys.
    This set is used to prune the DFS search tree.
    """
    prefixes = set()
    for key in keys_dec:
        path = dec_key_to_LR_path(key, total_bits=total_bits)
        # Add all prefixes up to max_prefix_len
        for length in range(1, min(max_prefix_len + 1, len(path) + 1)):
            prefixes.add(path[:length])
    print(f"Built prefix set with {len(prefixes)} prefixes up to length {max_prefix_len}")
    return prefixes

def prefix_filter(path, allowed_prefixes):
    """
    Checks if the current path (as a tuple of 'L'/'R') is a valid prefix
    based on the `allowed_prefixes` set. This is a pruning mechanism.
    """
    path_str = ''.join(path)
    if not path_str: # Root path is always allowed to start the search
        return True

    # Check if the current path_str is a prefix of any allowed prefix
    # OR if any allowed prefix is a prefix of the current path_str
    # This ensures we only explore branches that are "close" to known paths.
    for allowed_p in allowed_prefixes:
        if allowed_p.startswith(path_str) or path_str.startswith(allowed_p):
            return True
    return False

# --- Depth-First Search Algorithm ---
def dfs_search(path, depth, max_depth, target_address, current_start, current_end, allowed_prefixes):
    """
    Performs a Depth-First Search to find a private key.
    It prunes branches that don't match allowed prefixes.
    """
    if depth > max_depth:
        return None # Stop if max depth is exceeded

    # Apply prefix pruning: if current path is not "allowed", stop exploring this branch
    if not prefix_filter(path, allowed_prefixes):
        return None

    # Calculate the private key for the current node/path
    privkey_int = node_path_to_privkey_in_range(path, current_start, current_end)
    privkey_hex = format(privkey_int, '064x') # Format to 64-char hex string

    # Derive Bitcoin address
    addr = private_key_to_address(privkey_hex)

    # Print progress (uncomment for verbose output)
    # print(f"Depth {depth} | Path {''.join(path) or 'Root'} | Key {privkey_hex[-8:]} | Addr {addr}")

    # Check if target address is found
    if addr == target_address:
        print("\n=== MATCH FOUND ===")
        print(f"Path: {''.join(path) or 'Root'}")
        print(f"Private Key (hex): {privkey_hex}")
        print(f"Address: {addr}")
        return privkey_hex

    # Recursively search left child ('L')
    left_result = dfs_search(path + ['L'], depth + 1, max_depth, target_address, current_start, (current_start + current_end)//2, allowed_prefixes)
    if left_result:
        return left_result

    # Recursively search right child ('R')
    right_result = dfs_search(path + ['R'], depth + 1, max_depth, target_address, (current_start + current_end)//2 + 1, current_end, allowed_prefixes)
    if right_result:
        return right_result

    return None # No match found in this branch

if __name__ == '__main__':
    print("--- DFS Key Finder with Prefix Pruning ---")
    # Example usage:
    # Create a dummy numbers.txt for allowed_prefixes (these are just arbitrary numbers)
    example_allowed_keys = [
        1, 3, 7, 8, 21, 49, 76, 224, 467, 514, 1155
    ]
    with open("data/numbers.txt", "w") as f:
        for num in example_allowed_keys:
            f.write(str(num) + "\n")
    print("Created 'data/numbers.txt' with example allowed keys.")

    # Define the target Bitcoin address (replace with a real target if desired)
    # This is a sample address, not necessarily related to the example_allowed_keys
    target_btc_address = '1FRoHA9xewq7DjrZ1psWJVeTer8gHRqEvR' # Example target

    # Define the full range of the private key space to search within
    # For a 32-bit puzzle, this might be 0 to 2^32 - 1
    # For a full 256-bit key, it's 1 to N-1
    # The example uses a much smaller range for demonstration purposes.
    start_range = 0x80000000 # Example start of a 32-bit range
    end_range = 0xFFFFFFFF   # Example end of a 32-bit range
    max_search_depth = 31    # Max depth for a 32-bit number (0-indexed)
    max_prefix_len = 10      # How deep to prune with prefixes (e.g., only check paths up to 10 bits long if they match)

    # Build the set of allowed prefixes from the example keys
    allowed_prefixes = build_prefix_set(example_allowed_keys, max_prefix_len=max_prefix_len, total_bits=max_search_depth + 1)

    print(f"Starting guided DFS search for {target_btc_address} in range {hex(start_range)} to {hex(end_range)}...\n")

    # Start the DFS search from the root (empty path)
    found_key = dfs_search(
        [], # Start with an empty path
        0, # Start at depth 0
        max_search_depth,
        target_btc_address,
        start_range,
        end_range,
        allowed_prefixes
    )

    if found_key:
        print(f"\nPrivate key found: {found_key}")
    else:
        print("\nNo matching private key found within depth and prefix constraints.")

    # Clean up the dummy file
    os.remove("data/numbers.txt")
    print("Cleaned up 'data/numbers.txt'.")