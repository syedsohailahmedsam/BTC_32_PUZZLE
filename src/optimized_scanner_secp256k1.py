# src/optimized_scanner_secp256k1.py

# --- Imports ---
import hashlib
import base58
from Crypto.Hash import RIPEMD160 # Using RIPEMD160 from pycryptodome
from multiprocessing.dummy import Pool # Using dummy for simpler threading, can be replaced with Pool for true multiprocessing
from tqdm import tqdm
import secp256k1  # C-based, fast secp256k1 library

# --- Constants ---
# N is the order of the secp256k1 curve, which is the maximum valid value for a private key.
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

# Global variables to be set by run_scanner for multiprocessing pool
# These are used to pass parameters to `check_key` function when used with Pool
START, END, ADDRESS_PREFIX = 0, 0, ""

# --- Key Validation Logic ---
def is_valid_key(hex_key):
    """
    Applies a custom, non-standard validation to the hexadecimal private key.
    This logic is identical to the one in optimized_scanner_ecdsa.py.
    """
    restricted = {'6', '9', 'a', 'd'}
    double_run_counts = {} # Tracks occurrences of double runs for each character
    count = 1 # Counts consecutive identical characters

    for i in range(1, len(hex_key)):
        curr, prev = hex_key[i], hex_key[i-1]

        if curr == prev:
            count += 1
        else:
            # If a run ends and it was a double run, record it
            if count == 2:
                double_run_counts[prev] = double_run_counts.get(prev, 0) + 1
            count = 1 # Reset count for new character

        # Immediate invalidation rules
        if count > 2: # More than two consecutive identical characters (e.g., 'aaa')
            return False
        if curr in restricted and count > 1: # Restricted char appears consecutively (e.g., '66')
            return False

    # Check for the last run after the loop finishes
    if count == 2:
        double_run_counts[hex_key[-1]] = double_run_counts.get(hex_key[-1], 0) + 1

    # Final check: Ensure no character has more than one double run
    return all(runs <= 1 for runs in double_run_counts.values())

# --- Key to Address Conversion ---
def private_key_to_address(key_int):
    """
    Converts a private key integer to its corresponding Bitcoin P2PKH address.
    Uses the secp256k1 C library for efficient public key derivation.
    """
    # Convert integer private key to 32-byte format
    private_key_bytes = key_int.to_bytes(32, byteorder='big')

    # Create a private key object using the secp256k1 library
    sk = secp256k1.PrivateKey(private_key_bytes)

    # Derive the uncompressed public key (65 bytes: 0x04 + 32-byte X + 32-byte Y)
    pubkey_bytes = sk.pubkey.serialize(compressed=False)

    # SHA256 Hash of the public key
    sha256_1 = hashlib.sha256(pubkey_bytes).digest()

    # RIPEMD160 Hash of the SHA256 hash
    ripemd160 = RIPEMD160.new(sha256_1).digest()

    # Add version byte (0x00 for mainnet P2PKH addresses)
    prefixed = b'\x00' + ripemd160

    # Calculate checksum (first 4 bytes of double SHA256 hash of prefixed data)
    checksum = hashlib.sha256(hashlib.sha256(prefixed).digest()).digest()[:4]

    # Concatenate prefixed data and checksum, then Base58 encode
    return base58.b58encode(prefixed + checksum).decode()

def pad_to_64(hex_str):
    """
    Pads a hexadecimal string with leading zeros to ensure it is 64 characters long.
    This is standard for representing a 256-bit private key in hex.
    """
    return hex_str.lower().lstrip('0x').rjust(64, '0')

# --- Check Single Key (for multiprocessing) ---
def check_key(percent):
    """
    Function to be executed by each worker process/thread.
    Calculates a private key based on the given percentage, validates it,
    derives its address, and checks if it matches the target prefix.
    """
    # Calculate the private key integer based on its position in the overall range
    key_int = START + int((END - START) * (percent / 100))

    # Validate key_int is within the valid range for secp256k1 (1 to N-1)
    if not (1 <= key_int < N):
        return None

    # Convert to hex string for custom validation
    priv_hex = hex(key_int)[2:].zfill(64)

    # Apply custom private key validation
    if not is_valid_key(priv_hex.lstrip('0')): # lstrip('0') for validation as per original logic
        return None

    # Derive Bitcoin address
    addr = private_key_to_address(key_int)

    # Check if the derived address starts with the desired prefix
    if addr.startswith(ADDRESS_PREFIX):
        return {'percentage': percent, 'private_key_hex': priv_hex, 'address': addr}
    return None

# --- Optimized Scanner ---
def run_scanner(start_hex, end_hex, address_prefix, step_percent=0.01):
    """
    Orchestrates the private key scanning process using multiprocessing.
    It defines the search range, sets up the parallel pool, and manages progress.
    """
    # Use global variables to pass parameters to check_key for multiprocessing Pool
    global START, END, ADDRESS_PREFIX
    START = int(pad_to_64(start_hex), 16)
    END = int(pad_to_64(end_hex), 16)
    ADDRESS_PREFIX = address_prefix

    # Basic input validation
    if not END > START:
        raise ValueError("End private key must be greater than start private key.")
    if END >= N:
        raise ValueError(f"End private key must be less than N (curve order).")

    print(f"\n🚀 Running with HIGH-SPEED C library on 8 threads...")
    print(f"Scanning range: {start_hex} to {end_hex}")
    print(f"Target address prefix: {address_prefix}")
    print(f"Scanning resolution (step_percent): {step_percent}%")


    num_threads = 8 # Number of worker threads/processes for parallel execution
    total_percent = 100.0 # Total percentage of the range to cover
    percent = 0.0 # Current percentage scanned
    found_count = 0 # Counter for matching keys found
    chunk_size = 1000000 # Number of steps to process in each multiprocessing chunk. Adjust based on RAM.

    # Use multiprocessing.dummy.Pool for threading (lighter than full processes)
    # For CPU-bound tasks, multiprocessing.Pool (true processes) is often better,
    # but dummy.Pool might be sufficient for I/O-bound or mixed tasks.
    with Pool(num_threads) as pool:
        pbar = tqdm(total=int(total_percent / step_percent), desc="Scanning keys", dynamic_ncols=True)
        
        # Continuously generate steps and map them to the pool
        while percent < total_percent:
            # Generate a chunk of percentage steps
            steps_chunk = [percent + i * step_percent for i in range(chunk_size)]
            # Filter out steps that exceed the total_percent
            steps_chunk = [p for p in steps_chunk if p <= total_percent]

            if not steps_chunk:
                break # No more steps to process

            # Map the check_key function to the steps in the current chunk
            # chunksize for imap helps distribute tasks efficiently
            for result in pool.imap(check_key, steps_chunk, chunksize=1000):
                if result:
                    if found_count == 0:
                        print(f"\n✅ Found matching key(s):\n") # Print header only once
                    print(f"Percent: {result['percentage']:.8f}%")
                    print(f"Address: {result['address']}")
                    print(f"Private key (hex): {result['private_key_hex']}")
                    print("-" * 20)
                    found_count += 1
                pbar.update(1) # Update progress bar for each key checked

            # Update the starting percentage for the next chunk
            if steps_chunk:
                percent = steps_chunk[-1] + step_percent
            else:
                break # Should not happen if steps_chunk is not empty, but good for safety

        pbar.close() # Close the progress bar

    if found_count == 0:
        print("\n❌ No matching addresses found.")
    else:
        print(f"\nScan complete. Found a total of {found_count} matching key(s).")

# --- Run the Scanner ---
if __name__ == "__main__":
    print("--- Optimized secp256k1 Scanner with Multiprocessing ---")
    # Example usage:
    # These values define a range of private keys to scan.
    # For a real BTC puzzle, these ranges would be derived from the puzzle's known bits.
    # The 'step' defines the granularity of the search (how many keys are checked).
    # A smaller 'step' means more keys are checked, increasing accuracy but also time.

    # Example: A very small range for quick testing
    # start_hex = "1000000000000000000000000000000000000000000000000000000000000000"
    # end_hex   = "10000000000000000000000000000000000000000000000000000000000000FF" # Last two hex digits vary
    # prefix    = "1" # Very common prefix

    # Example from the original code: A larger range
    start_hex = "400000000000000000"
    end_hex   = "7fffffffffffffffff"
    prefix    = "1PWo3"         # Target prefix (this is a real address prefix)
    step      = 0.000000001       # Scanning resolution. Increase if memory usage is still high.
    
    run_scanner(start_hex, end_hex, prefix, step)