
# 🔐 Bitcoin Key Tools & Puzzle Explorers

A comprehensive Python-based toolkit for exploring the Bitcoin private key space, designed to aid in **puzzle solving**, **keyspace visualization**, and **vanity address generation**. Includes stateful scanners, key filtering logic, and binary tree path analysis based on real Bitcoin puzzle patterns.

---

## 📁 Project Structure

```
bitcoin-key-tools/
├── README.md
├── .gitignore
├── data/
│   ├── numbers.txt
│   ├── filtered_keys_*.csv
│   └── state_*.txt
└── src/
    ├── basic_scanner.py
    ├── optimized_scanner_ecdsa.py
    ├── optimized_scanner_secp256k1.py
    ├── tree_path_analyzer.py
    └── dfs_key_finder.py
```

---

## ⚙️ Installation & Environment Setup

```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/macOS
# venv\Scripts\activate  # On Windows

pip install ecdsa base58 requests tqdm pycryptodome secp256k1 networkx plotly pandas bitcoinlib
```

---

## 🧪 Script Explanations with Examples

### 1. `basic_scanner.py`
**Purpose**: Scans a range of private keys by sampling and checks if the resulting addresses start with a specific prefix.

**Run Example**:
```bash
python src/basic_scanner.py
```
Input:
```
start_hex: 100000000000000000
end_hex:   1000000000000000FF
prefix:    1P
step:      0.01
```

---

### 2. `optimized_scanner_ecdsa.py`
**Purpose**: Scans key range with public key derivation, custom hex filtering, and scan state saving.

**Run Example**:
```bash
python src/optimized_scanner_ecdsa.py
```

Edit inside the script:
```python
MIN_KEY = int("800000000000000000", 16)
MAX_KEY = int("8000000000000000FF", 16)
TARGET_ADDRESS = "1YourTargetPrefixHere"
```

---

### 3. `optimized_scanner_secp256k1.py`
**Purpose**: High-speed multithreaded scanner using C-based cryptography.

**Run Example**:
```bash
python src/optimized_scanner_secp256k1.py
```

Edit in script:
```python
start_hex = "400000000000000000"
end_hex   = "7fffffffffffffffff"
prefix    = "1PWo3"
step      = 0.00000001
```

---

### 4. `tree_path_analyzer.py`
**Purpose**: Converts decimal numbers into binary tree paths and analyzes frequent patterns.

**Run Example**:
```bash
python src/tree_path_analyzer.py
```

Input file:
```
data/numbers.txt  # List of decimal keys (e.g., 1, 3, 7, ...)
```

---

### 5. `dfs_key_finder.py`
**Purpose**: DFS-based private key search with prefix pruning based on known puzzle keys.

**Run Example**:
```bash
python src/dfs_key_finder.py
```

Edit in script:
```python
target_btc_address = "1FRoHA9xewq7DjrZ1psWJVeTer8gHRqEvR"
start_range = 0x80000000
end_range   = 0xFFFFFFFF
max_search_depth = 31
max_prefix_len   = 10
```

---

## 🔒 Hex Key Validation

Custom rules derived from analysis of puzzles 1–70:

- ❌ **No triples**: No 3 repeated characters (e.g. "fff", "aaa")
- ❌ **No repeated double pairs**: Only one `"aa"` allowed; `"112211"` → invalid
- ❌ **No double "6", "9", "a", or "d"**

Implemented in:
- `optimized_scanner_ecdsa.py`
- `optimized_scanner_secp256k1.py`

---

## 🧠 Summary Table

| Script                       | Use Case                     | Best For                     |
|-----------------------------|------------------------------|------------------------------|
| `basic_scanner.py`          | Sampling + prefix match      | Educational, vanity scanning |
| `optimized_scanner_ecdsa.py`| Stateful full scan + filters | Puzzle scanning w/ resume    |
| `optimized_scanner_secp256k1.py` | Fast, threaded prefix match | Large-scale key search       |
| `tree_path_analyzer.py`     | Tree/path analysis           | Pattern discovery            |
| `dfs_key_finder.py`         | Guided DFS via prefix paths  | Puzzle 66+ targeting         |

---

## 📄 .gitignore Template

```gitignore
__pycache__/
*.pyc
.venv/
venv/
.vscode/
.idea/
data/*.csv
data/*.txt
```

---

## ⚠️ Disclaimer

> For research/educational use only. Do not use with live wallets unless you understand the risks.

---

## 🔗 Resources

- [Bitcoin Puzzle](https://privatekeys.pw/puzzles/bitcoin-puzzle-tx)

---

## 🧾 Sample Outputs

### `basic_scanner.py`

```
--- Basic Bitcoin Key Scanner ---
Enter start hex private key: 100000000000000000
Enter end hex private key:   1000000000000000FF
Enter Bitcoin address prefix to filter (e.g. '1AB'): 1P
Enter step percentage (default 0.01): 0.01
Generating keys from 100000000000000000 to 1000000000000000ff (10001 steps)...

Found 1 matching keys:

Percent: 0.78%
Address: 1Pabcxyz...
Private key (hex): 100000000000000012
Private key (bin): 000100000000...
```

---

### `optimized_scanner_ecdsa.py`

```
--- Optimized ECDSA Scanner with State Saving ---
Resuming from attempt 0
Checked: 10000 keys | Found: 2 | Time elapsed: 4.32s

Found:
PrivateKey: a1b2c3d4e5f6...
Address: 1Pxxxx...
Keys saved to: filtered_keys_ecdsa.csv
```

---

### `optimized_scanner_secp256k1.py`

```
--- Optimized secp256k1 Scanner with Multiprocessing ---

🚀 Running with HIGH-SPEED C library on 8 threads...
Scanning range: 400000000000000000 to 7fffffffffffffffff
Target address prefix: 1P
Scanning resolution (step_percent): 1e-08%

✅ Found matching key(s):

Percent: 12.00000001%
Address: 1Pabc123...
Private key (hex): 4abcd123456789...
--------------------
Scan complete. Found a total of 1 matching key(s).
```

---

### `tree_path_analyzer.py`

```
--- Binary Tree Path Analyzer ---
Reading numbers from: data/numbers.txt
Total numbers read: 70

All paths from root for each number:
Number: 7
Path: [1, 3, 7, 15]
Depth: 3

Most common nodes:
  Node 1 appears 70 times
  Node 3 appears 58 times

Most common edges:
  Edge (1, 3) appears 58 times
  Edge (3, 7) appears 45 times

Saved CSV files: most_common_edges.csv, most_common_nodes.csv, most_common_prefixes.csv
```

---

### `dfs_key_finder.py`

```
--- DFS Key Finder with Prefix Pruning ---
Created 'data/numbers.txt' with example allowed keys.

Starting guided DFS search for 1FRoHA9xewq7DjrZ1psWJVeTer8gHRqEvR in range 0x80000000 to 0xffffffff...

=== MATCH FOUND ===
Path: LRRLRRLLRLR...
Private Key (hex): abcd1234ef56789...
Address: 1FRoHA9xewq7DjrZ1psWJVeTer8gHRqEvR

Private key found: abcd1234ef56789...
Cleaned up 'data/numbers.txt'.
```

---

## 🧾 Script Run Commands + Input/Output Examples

---

### 🧪 `basic_scanner.py`

**Command**:
```bash
python src/basic_scanner.py
```

**Input**:
```
Enter start hex private key: 100000000000000000
Enter end hex private key:   1000000000000000FF
Enter Bitcoin address prefix to filter (e.g. '1AB'): 1P
Enter step percentage (default 0.01): 0.01
```

**Output**:
```
--- Basic Bitcoin Key Scanner ---
Generating keys from 100000000000000000 to 1000000000000000ff (10001 steps)...

Found 1 matching keys:

Percent: 0.78%
Address: 1Pabcxyz...
Private key (hex): 100000000000000012
Private key (bin): 000100000000...
```

---

### ⚡ `optimized_scanner_ecdsa.py`

**Command**:
```bash
python src/optimized_scanner_ecdsa.py
```

**Output**:
```
--- Optimized ECDSA Scanner with State Saving ---
Resuming from attempt 0
Checked: 10000 keys | Found: 2 | Time elapsed: 4.32s

Found:
PrivateKey: a1b2c3d4e5f6...
Address: 1Pxxxx...
Keys saved to: filtered_keys_ecdsa.csv
```

---

### 🚀 `optimized_scanner_secp256k1.py`

**Command**:
```bash
python src/optimized_scanner_secp256k1.py
```

**Output**:
```
--- Optimized secp256k1 Scanner with Multiprocessing ---

🚀 Running with HIGH-SPEED C library on 8 threads...
Scanning range: 400000000000000000 to 7fffffffffffffffff
Target address prefix: 1P
Scanning resolution (step_percent): 1e-08%

✅ Found matching key(s):

Percent: 12.00000001%
Address: 1Pabc123...
Private key (hex): 4abcd123456789...
--------------------
Scan complete. Found a total of 1 matching key(s).
```

---

### 🌲 `tree_path_analyzer.py`

**Command**:
```bash
python src/tree_path_analyzer.py
```

**Output**:
```
--- Binary Tree Path Analyzer ---
Reading numbers from: data/numbers.txt
Total numbers read: 70

All paths from root for each number:
Number: 7
Path: [1, 3, 7, 15]
Depth: 3

Most common nodes:
  Node 1 appears 70 times
  Node 3 appears 58 times

Most common edges:
  Edge (1, 3) appears 58 times
  Edge (3, 7) appears 45 times

Saved CSV files: most_common_edges.csv, most_common_nodes.csv, most_common_prefixes.csv
```

---

### 🧭 `dfs_key_finder.py`

**Command**:
```bash
python src/dfs_key_finder.py
```

**Output**:
```
--- DFS Key Finder with Prefix Pruning ---
Created 'data/numbers.txt' with example allowed keys.

Starting guided DFS search for 1FRoHA9xewq7DjrZ1psWJVeTer8gHRqEvR in range 0x80000000 to 0xffffffff...

=== MATCH FOUND ===
Path: LRRLRRLLRLR...
Private Key (hex): abcd1234ef56789...
Address: 1FRoHA9xewq7DjrZ1psWJVeTer8gHRqEvR

Private key found: abcd1234ef56789...
Cleaned up 'data/numbers.txt'.
```

---

## ☕ Support & Donations

If this Bitcoin key research toolkit helps you, consider supporting it:

[![Buy Me a Coffee](https://img.shields.io/badge/☕-Buy%20Me%20a%20Coffee-orange)](https://buymeacoffee.com/syedsohailahmed)

**BITCOIN**:  
`bc1qk33euetuagkvl0vzyucyp4pp3e7zxq8pjg3u6h`  
**ETHEREUM**:  
`0x20De3188D4a085c434e55C656A668C052b8A4c20`  
**TRON**:  
`TCuvSLbTqh6Zg96jwb9V8UdnHwebftsfTZ`  
**SOLANA**:  
`CkKSjBU6sDWf19a86vPEiKCFx9ojvLJAAsm16kP2YWeu`  
