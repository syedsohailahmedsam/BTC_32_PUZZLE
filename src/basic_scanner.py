# src/basic_scanner.py

# Ensure all necessary libraries are imported
import ecdsa
import hashlib
import base58
from tqdm import tqdm
# Import RIPEMD160 from pycryptodome
from Crypto.Hash import RIPEMD160
from decimal import Decimal, getcontext # Added for potential future use or completeness
import requests # Added for get_balance if it were used in this cell's logic
import csv # Added for potential future use or completeness

getcontext().prec = 80  # High precision for Decimal math, if needed

def private_key_to_address(key_int):
    """
    Converts a private key integer to its corresponding Bitcoin P2PKH address.
    """
    sk = ecdsa.SigningKey.from_secret_exponent(key_int, curve=ecdsa.SECP256k1)
    vk = sk.get_verifying_key()
    # uncompressed public key prefix 0x04
    pubkey_bytes = b'\x04' + vk.to_string()
    sha256 = hashlib.sha256(pubkey_bytes).digest()
    # Use the RIPEMD160 object from Crypto.Hash as intended
    h = RIPEMD160.new()
    h.update(sha256)
    ripemd160_hash = h.digest()
    # version byte for mainnet P2PKH
    prefixed = b'\x00' + ripemd160_hash
    checksum = hashlib.sha256(hashlib.sha256(prefixed).digest()).digest()[:4]
    address_bytes = prefixed + checksum
    return base58.b58encode(address_bytes).decode()

def hex_to_binary(hex_str):
    """
    Converts a hexadecimal string to its binary representation.
    """
    scale = 16  # base 16
    num_of_bits = len(hex_str) * 4
    return bin(int(hex_str, scale))[2:].zfill(num_of_bits)

def pad_to_64(hex_str):
    """
    Pads a hexadecimal string with leading zeros to ensure it is 64 characters long.
    """
    return hex_str.lower().lstrip('0x').rjust(64, '0')

def generate_and_filter(start_hex, end_hex, address_prefix, step_percent=0.01):
    """
    Generates Bitcoin private keys within a specified range, derives addresses,
    and filters them based on a given address prefix. This uses a sampling approach.
    """
    start_hex_64 = pad_to_64(start_hex)
    end_hex_64 = pad_to_64(end_hex)
    start = int(start_hex_64, 16)
    end = int(end_hex_64, 16)
    if end <= start:
        raise ValueError("End must be greater than start")

    total_steps = int(100 / step_percent) + 1
    matched = []

    print(f"Generating keys from {start_hex_64} to {end_hex_64} ({total_steps} steps)...")

    for i in tqdm(range(total_steps)):
        percent = i * step_percent
        key_int = start + int((end - start) * (percent / 100))
        priv_hex = hex(key_int)[2:].zfill(64)
        addr = private_key_to_address(key_int)
        if addr.startswith(address_prefix):
            binary_key = hex_to_binary(priv_hex)
            matched.append({
                'percentage': percent,
                'private_key_hex': priv_hex,
                'private_key_bin': binary_key,
                'address': addr
            })
    return matched

# === USER INPUTS ===
if __name__ == "__main__":
    print("--- Basic Bitcoin Key Scanner ---")
    start_hex = input("Enter start hex private key: ").strip()
    end_hex = input("Enter end hex private key: ").strip()
    address_prefix = input("Enter Bitcoin address prefix to filter (e.g. '1AB'): ").strip()
    step_percent_input = input("Enter step percentage (default 0.01): ").strip()
    step_percent = float(step_percent_input) if step_percent_input else 0.01

    results = generate_and_filter(start_hex, end_hex, address_prefix, step_percent)

    if results:
        print(f"\nFound {len(results)} matching keys:\n")
        for r in results:
            print(f"Percent: {r['percentage']:.2f}%")
            print(f"Address: {r['address']}")
            print(f"Private key (hex): {r['private_key_hex']}")
            print(f"Private key (bin): {r['private_key_bin']}\n")
    else:
        print("No matching addresses found.")
