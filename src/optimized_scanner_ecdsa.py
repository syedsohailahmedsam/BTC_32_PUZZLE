# src/optimized_scanner_ecdsa.py

import secrets
import hashlib
import base58
import time
from ecdsa import SECP256k1, SigningKey
import os
from Crypto.Hash import RIPEMD # Using RIPEMD from pycryptodome
import concurrent.futures # For ThreadPoolExecutor

# Configuration (These are example values, adjust as needed)
MIN_KEY = int("800101010101010101", 16) # Example start of a key range
MAX_KEY = int("FFFFFFFFFFFFFFFFFF", 16) # Example end of a key range
TARGET_ADDRESS = "1JTK7s9YVYywfm5XUH7RNhHJH1LshCaRFR" # Example target address (can be None)

OUTPUT_FILE = "filtered_keys_ecdsa.csv" # Output CSV file
STATE_FILE = "state_ecdsa.txt" # File to save/load scan state

def is_valid_key(hex_key):
    """
    Applies a custom, non-standard validation to the hexadecimal private key.
    This logic is identical to the one in optimized_scanner_secp256k1.py.
    """
    restricted = {'6', '9', 'a', 'd'}
    double_run_counts = {}
    count = 1

    for i in range(1, len(hex_key)):
        curr = hex_key[i]
        prev = hex_key[i - 1]

        if curr == prev:
            count += 1
        else:
            if count == 2:
                double_run_counts[prev] = double_run_counts.get(prev, 0) + 1
            count = 1

        if count > 2:
            return False
        if curr in restricted and count > 1:
            return False

    if count == 2:
        double_run_counts[hex_key[-1]] = double_run_counts.get(hex_key[-1], 0) + 1

    for digit, runs in double_run_counts.items():
        if runs > 1:
            return False

    return True

def private_key_to_public_address(private_key_hex):
    """
    Converts a private key in hexadecimal format to its Bitcoin P2PKH address.
    Uses the ecdsa library.
    """
    try:
        private_key_bytes = bytes.fromhex(private_key_hex)
        sk = SigningKey.from_string(private_key_bytes, curve=SECP256k1)
        vk = sk.verifying_key
        public_key_bytes = b'\x04' + vk.to_string() # Uncompressed public key

        sha256 = hashlib.sha256(public_key_bytes).digest()
        ripemd160 = RIPEMD.new() # Use RIPEMD from Crypto.Hash
        ripemd160.update(sha256)
        hashed = ripemd160.digest()

        versioned_payload = b'\x00' + hashed # 0x00 for mainnet P2PKH
        checksum = hashlib.sha256(hashlib.sha256(versioned_payload).digest()).digest()[:4]
        address = base58.b58encode(versioned_payload + checksum).decode()
        return address
    except Exception as e:
        # print(f"Error generating address for key {private_key_hex}: {e}") # Uncomment for detailed errors
        return None

def load_state():
    """Loads the last saved attempt count from the state file."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            state = f.read().strip()
            return int(state) if state else 0
    return 0

def save_state(attempts):
    """Saves the current attempt count to the state file."""
    try:
        with open(STATE_FILE, "w") as f:
            f.write(str(attempts))
    except Exception as e:
        print(f"Error saving state: {e}")

def process_key_range_ecdsa(start_key_value, end_key_value, target_address):
    """Worker function for processing a range of keys in parallel."""
    local_results = []
    for key_val in range(start_key_value, end_key_value):
        hex_key = hex(key_val)[2:].rjust(64, '0') # Pad to 64 chars here for consistent processing
        if is_valid_key(hex_key):
            addr = private_key_to_public_address(hex_key)
            if addr:
                local_results.append((hex_key, addr))
                if target_address and addr == target_address:
                    break # Stop if target found in this worker's range
    return local_results

def generate_filtered_keys_with_addresses(n=None, target=None):
    """
    Generates and filters Bitcoin private keys within a defined range,
    applying custom validation and saving state for resumption.
    Uses ThreadPoolExecutor for parallel processing.
    """
    results = []
    rejected = 0
    attempts = load_state() # Load starting attempt count
    print(f"Resuming from attempt {attempts}")

    # Open output file in append mode. If it's a new run, write header.
    with open(OUTPUT_FILE, "a") as f_out:
        if attempts == 0 and os.path.getsize(OUTPUT_FILE) == 0: # Check if file is truly empty
            f_out.write("PrivateKey,Address\n")

        start_time = time.time()
        total_keys_to_check = MAX_KEY - MIN_KEY + 1

        # Use 4 threads for parallel processing
        num_workers = 4 
        batch_size = 10000 # Number of keys to process per batch for progress updates

        while attempts < total_keys_to_check:
            current_batch_start_abs = MIN_KEY + attempts
            current_batch_end_abs = min(MIN_KEY + attempts + batch_size, MAX_KEY + 1)

            if current_batch_start_abs >= current_batch_end_abs:
                break # No more keys in range

            # Divide the current batch into chunks for workers
            chunk_size_per_worker = (current_batch_end_abs - current_batch_start_abs) // num_workers
            ranges_for_workers = []
            for i in range(num_workers):
                worker_start = current_batch_start_abs + i * chunk_size_per_worker
                worker_end = worker_start + chunk_size_per_worker
                ranges_for_workers.append((worker_start, worker_end))
            # Ensure the last chunk covers any remainder
            ranges_for_workers[-1] = (ranges_for_workers[-1][0], current_batch_end_abs)

            batch_found_results = []
            target_found_in_batch = False

            with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = [executor.submit(process_key_range_ecdsa, s, e, target) for s, e in ranges_for_workers]
                for future in concurrent.futures.as_completed(futures):
                    res = future.result()
                    batch_found_results.extend(res)
                    if target and any(addr == target for _, addr in res):
                        target_found_in_batch = True
                        break # Stop other workers if target found

            # Write results from the batch
            for priv_key, addr in batch_found_results:
                f_out.write(f"{priv_key},{addr}\n")
                results.append((priv_key, addr)) # Add to overall results list

            attempts += (current_batch_end_abs - current_batch_start_abs) # Update attempts by keys processed in batch
            save_state(attempts) # Save state after each batch

            elapsed = time.time() - start_time
            print(f"\rChecked: {attempts} keys | Found: {len(results)} | Time elapsed: {elapsed:.2f}s", end='')

            if target_found_in_batch:
                print(f"\nTarget address {target} found!")
                break
            
            if n is not None and len(results) >= n:
                break

            # Note: Rejected count is not accurately tracked with parallel processing this way
            # as it's not returned by `process_key_range_ecdsa`.
            # To track rejected, `process_key_range_ecdsa` would need to return it.

        elapsed = time.time() - start_time
    return results, attempts, rejected, elapsed

if __name__ == "__main__":
    print("--- Optimized ECDSA Scanner with State Saving ---")
    try:
        # You can change MIN_KEY, MAX_KEY, TARGET_ADDRESS, OUTPUT_FILE, STATE_FILE
        # directly in the script's constants section above.
        results, attempts, rejected, duration = generate_filtered_keys_with_addresses(target=TARGET_ADDRESS)
        print(f"\nDone! Found: {len(results)}, Attempts: {attempts}, Rejected: {rejected}, Time: {duration:.2f} sec")
        print(f"Keys saved to: {OUTPUT_FILE}")
    except KeyboardInterrupt:
        print("\nGenerator stopped manually.")
        print(f"State saved: total keys checked = {load_state()}")
