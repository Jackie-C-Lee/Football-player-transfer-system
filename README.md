# ⚽ Football Player Transfer System

[![Solidity](https://img.shields.io/badge/Solidity-%5E0.8.0-363636?logo=solidity&logoColor=white)](https://soliditylang.org/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Ethereum](https://img.shields.io/badge/Ethereum-Ganache-3C3C3D?logo=ethereum&logoColor=white)](https://trufflesuite.com/ganache/)
[![Web3.py](https://img.shields.io/badge/Web3.py-6.8.0-orange)](https://web3py.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Note**: This project originated from a university-level *Blockchain Technology* course assignment and represents an **early-stage experimental prototype**. It demonstrates the feasibility of integrating blockchain with anti-money laundering protocols in a simulated football transfer environment, but is not production-ready.

---

A blockchain-powered football player transfer management system that combines **Ethereum smart contracts** with **Locality-Sensitive Hashing (LSH)** to deliver transparent, auditable, and fraud-resistant player transactions.

---

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [System Architecture](#-system-architecture)
- [How It Works](#-how-it-works)
  - [Smart Contract Lifecycle](#smart-contract-lifecycle)
  - [Anti-Money Laundering Protocol](#anti-money-laundering-protocol)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Usage Guide](#-usage-guide)
- [API Endpoints](#-api-endpoints)
- [Experimental Results](#-experimental-results)
- [Configuration](#-configuration)
- [Screenshots](#-screenshots)
- [Roadmap](#-roadmap)
- [License & Acknowledgements](#-license--acknowledgements)

---

## 🔍 Project Overview

Traditional football transfer markets face critical challenges: opacity in financial flows, money laundering risks through inflated transfer fees, and lack of trust between clubs and regulators. This project addresses these issues by leveraging blockchain's immutability and transparency, combined with a privacy-preserving LSH-based validation mechanism.

**Core idea**: Before a transfer is finalized, both the selling and buying clubs independently generate cryptographic LSH indexes from their financial records. A regulator then compares these indexes — similar indexes indicate the reported amounts are consistent, while anomalous similarity scores flag potential fraud or money laundering.

---

## ✨ Key Features

- **🔗 Ethereum Smart Contract** — On-chain management of club registration, transfer proposals, multi-party confirmations, and immutable audit trails.

- **🛡️ LSH-Based AML Detection** — Locality-Sensitive Hashing algorithm detects suspicious patterns by comparing income/expense financial vectors without exposing raw sensitive data.

- **✅ Three-Step Confirmation Protocol** — Seller proposes → Buyer accepts → Regulator validates. No transfer completes without all three signatures on-chain.

- **🌐 Interactive Web Interface** — A browser-based dashboard for viewing clubs, players, transfer offers, blockchain status, and real-time notifications.

- **🧪 Local Blockchain Testing** — Deployed and tested on Ganache (Ethereum local testnet), enabling zero-cost experimentation and reproducible results.

- **📦 Modular Python Backend** — Clean separation between blockchain interaction, LSH computation, database operations, and HTTP services.

---

## 🛠 Tech Stack

| Category | Technology | Role |
|----------|------------|------|
| **Smart Contract** | Solidity `^0.8.0` | On-chain transfer logic, club registry, event emission |
| **Blockchain Node** | Ganache (Ethereum Simulator) | Local test network with pre-funded accounts |
| **Blockchain SDK** | Web3.py `6.8.0` | Python ↔ Ethereum interaction, transaction building & signing |
| **AML Algorithm** | LSH + MinHash + NumPy | Financial vector projection and similarity comparison |
| **Database** | SQLite3 | Off-chain storage for clubs, players, offers, and history |
| **Web Backend** | Python `http.server` + socketserver | RESTful API serving the frontend |
| **Web Frontend** | Vanilla HTML/CSS/JavaScript | Responsive dashboard with dynamic data loading |
| **Dev Tools** | PyCharm, VS Code, solcx | Development, compilation, and deployment |

---

## 🏗 System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   WEB BROWSER (UI)                       │
│          Clubs │ Players │ Offers │ Blockchain           │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTP (localhost:8000)
┌─────────────────────▼───────────────────────────────────┐
│               PYTHON HTTP SERVER                         │
│  enhanced_app.py  —  Request routing & JSON API          │
└─────────────────────┬───────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌───────────────┐ ┌──────────┐ ┌──────────────┐
│ TRANSFER MGR  │ │   LSH    │ │  BLOCKCHAIN  │
│ (Orchestrator)│ │ SERVICE  │ │   SERVICE    │
│               │ │          │ │              │
│ • 流程编排    │ │• MinHash │ │ • Web3.py    │
│ • 报价管理    │ │• TIVA    │ │ • Contract   │
│ • 数据库操作  │ │• TEVA    │ │ • Tx signing │
│               │ │• 相似度  │ │ • Gas mgmt   │
└───────┬───────┘ └────┬─────┘ └──────┬───────┘
        │              │              │
        ▼              ▼              ▼
┌───────────────┐ ┌──────────┐ ┌──────────────┐
│    SQLite     │ │  NumPy   │ │   GANACHE    │
│   Database    │ │  Arrays  │ │  (ETH RPC)   │
└───────────────┘ └──────────┘ └──────────────┘
```

**Data Flow**:
1. User interacts with the web dashboard
2. HTTP server routes requests to the appropriate backend module
3. Transfer Manager coordinates between database queries, LSH computation, and blockchain interactions
4. All on-chain actions (register club, propose/accept/validate transfer) are recorded immutably on Ganache
5. LSH indexes are generated offline from financial data and compared to detect anomalies

---

## ⚙ How It Works

### Smart Contract Lifecycle

The transfer process follows a strict **state machine** with five stages, enforced by Solidity modifiers and require statements:

```
  ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
  │ PROPOSED │────▶│ ACCEPTED │────▶│VALIDATED │────▶│COMPLETED │
  └──────────┘     └──────────┘     └──────────┘     └──────────┘
       │                                  │
       └──────────── REJECTED ◀───────────┘
```

| Step | Actor | Action | On-Chain Effect |
|------|-------|--------|-----------------|
| **1. Propose** | Selling Club | Submits transfer details + LSH income hash | Transfer created with `Proposed` status |
| **2. Accept** | Buying Club | Confirms terms + provides LSH expense hash | Status → `Accepted` |
| **3. Validate** | Regulator (contract owner) | Compares LSH hashes, determines legitimacy | Status → `Completed` (if legitimate) or `Rejected` (if fraudulent) |
| **Cancel** | Selling Club | Withdraws before buyer acceptance | Status → `Rejected` |

**On-chain events emitted**: `ClubRegistered`, `TransferProposed`, `TransferAccepted`, `TransferValidated`, `TransferCompleted`, `TransferRejected`. These events provide a fully traceable audit log.

### Anti-Money Laundering Protocol

The system uses **Locality-Sensitive Hashing (LSH)** to compare financial records without exposing raw numbers:

1. **TIVA Generation** (Transfer Income Vector Abstraction)
   - The selling club generates a financial vector from its income records (transfer fees, player market values, fee-to-value ratios)
   - Random projections convert this vector into a binary LSH index

2. **TEVA Generation** (Transfer Expense Vector Abstraction)
   - The buying club independently generates a vector from its expense records (transfer fees, additional costs, total outlay)
   - The same random projection seeds produce an LSH index

3. **Similarity Comparison**
   - Hamming distance between the two binary indexes yields a similarity score (0.0–1.0)
   - **Normal range** (0.3–0.8): Transfer is considered legitimate
   - **Too low** (<0.3): Possible data manipulation — amounts may have been falsified
   - **Too high** (>0.9): Possible money laundering — amounts match too perfectly, suggesting collusion

> This approach preserves **privacy** (raw financial data never leaves each club) while enabling **regulatory oversight** (the regulator only compares cryptographic hashes).

---

## 📁 Project Structure

```
Football-player-transfer-system/
├── config/
│   ├── .env                    # Environment variables (Ganache URL, keys, DB path)
│   ├── database.py             # SQLite connection manager with context manager
│   └── __init__.py
├── contracts/
│   ├── TransferContract.sol    # Solidity smart contract (state machine + events)
│   └── TransferContract-sol.txt# Human-readable backup
├── gitPyCodes/
│   ├── deploy_contract.py      # Compile & deploy smart contract to Ganache
│   ├── init_database_enhanced.py# Initialize SQLite schema & seed data
│   ├── enhanced_app.py         # HTTP server + Web dashboard
│   ├── enhanced_transfer_manager.py# Core orchestrator (DB ↔ LSH ↔ Blockchain)
│   └── get_ganache_accounts.py # List Ganache accounts and balances
├── services/
│   ├── blockchain_service.py   # Web3.py wrapper (tx building, signing, querying)
│   ├── lsh_service.py          # LSH index generation & similarity comparison
│   ├── enhanced_transfer_service.py# Transfer business logic
│   └── __init__.py
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- **Python** 3.8 or higher
- **Node.js** (for Ganache CLI) or **Ganache Desktop** (GUI)
- **Git**

### Step-by-Step Setup

```bash
# 1. Clone the repository
git clone https://github.com/Jackie-C-Lee/Football-player-transfer-system.git
cd Football-player-transfer-system

# 2. Install Python dependencies
pip install -r requirements.txt
# If requirements.txt is unavailable, manually install:
# pip install web3 solcx python-dotenv numpy datasketch

# 3. Start Ganache (local blockchain)
# Option A: Ganache Desktop → Quickstart Ethereum
# Option B: ganache-cli --port 7545 --networkId 1337

# 4. Configure environment
# Edit config/.env with your Ganache account address and private key
# (Copy from Ganache UI → Accounts → first account)

# 5. Deploy the smart contract
python gitPyCodes/deploy_contract.py

# 6. Initialize the database
python gitPyCodes/init_database_enhanced.py

# 7. Launch the web interface
python gitPyCodes/enhanced_app.py
```

Then open **http://localhost:8000** in your browser.

---

## 📖 Usage Guide

### Typical Transfer Workflow

1. **View Dashboard** — Browse registered clubs, available players, and existing offers from the home page.

2. **Set Player Status** — Mark a player as "Available for Transfer" so other clubs can see them.

3. **Make an Offer** — A buying club submits a transfer offer with proposed fee.

4. **Handle Offer** — The selling club accepts, rejects, or counters the offer.

5. **Process Transfer** — Once both clubs agree:
   - The selling club's financial data generates the income LSH hash
   - The buying club's financial data generates the expense LSH hash
   - The system runs AML validation on-chain
   - The regulator (contract owner) validates the transfer

6. **View Results** — Check the transfer history and blockchain details to see the immutable record.

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Main dashboard (HTML) |
| `GET` | `/api/clubs` | List all registered clubs |
| `GET` | `/api/players` | List all players with status |
| `GET` | `/api/offers` | List all transfer offers |
| `GET` | `/api/history` | List completed/rejected transfers |
| `GET` | `/api/blockchain` | Get blockchain status & contract info |
| `GET` | `/api/notifications` | Get recent system notifications |
| `POST` | `/api/set_status` | Update a player's transfer status |
| `POST` | `/api/make_offer` | Create a new transfer offer |
| `POST` | `/api/handle_offer` | Accept or reject an offer |
| `POST` | `/api/process_transfer` | Execute full transfer with LSH + on-chain validation |

---

## 📊 Experimental Results

All experiments were conducted on a **Ganache local testnet** (Chain ID: 1337) with 10 pre-funded accounts simulating football clubs and a regulator.

| Metric | Result |
|--------|--------|
| **LSH Detection Accuracy** | 100% (all legitimate transfers correctly identified; all manipulated transfers flagged) |
| **Average Transaction Latency** | < 5 seconds per transfer (including gas estimation and on-chain confirmation) |
| **Concurrent Transfer Success Rate** | ≥ 80% under 10-thread parallel load |
| **On-Chain Audit Trail** | Every transfer state change recorded as an immutable Solidity event |
| **Smart Contract Gas Usage** | ~100K–200K gas per transfer (depending on stage) |

---

## ⚙ Configuration

Key environment variables in `config/.env`:

| Variable | Description | Example |
|----------|-------------|---------|
| `GANACHE_URL` | Ethereum RPC endpoint | `http://127.0.0.1:7545` |
| `CHAIN_ID` | Network chain ID | `1337` |
| `ACCOUNT_ADDRESS` | Regulator/deployer address | `0xF40fBD24...` |
| `PRIVATE_KEY` | Corresponding private key | `0xeea30488...` |
| `DB_PATH` | SQLite database file | `football_transfer_enhanced.db` |
| `LSH_HASH_DIMENSIONS` | Number of projection dimensions | `10` |
| `LSH_SIMILARITY_THRESHOLD_MIN` | Lower bound for legitimacy | `0.3` |
| `LSH_SIMILARITY_THRESHOLD_MAX` | Upper bound for legitimacy | `0.8` |

---

## 📸 Screenshots

> *Screenshots of the running web dashboard will be added here.*

*Dashboard showing clubs, players, and transfer offers*

*Transfer processing with LSH validation results*

*Blockchain transaction details view*

---

## 🗺 Roadmap

- [ ] Migrate to a public Ethereum testnet (Sepolia / Goerli) for broader demo access
- [ ] Add multi-token support (ERC-20) for transfer fee settlement
- [ ] Implement Role-Based Access Control (RBAC) in the smart contract
- [ ] Enhance the LSH model with real-world transfer market data
- [ ] Containerize with Docker for one-command setup
- [ ] Add comprehensive unit tests for smart contract (Hardhat / Truffle)
- [ ] Upgrade web frontend to a modern framework (React / Vue)

---

## 📄 License & Acknowledgements

This project is licensed under the **MIT License**.

**Course**: *Blockchain Technology* — University Course Assignment (2025)

**Acknowledgements**:
- [Ganache](https://trufflesuite.com/ganache/) — Personal Ethereum blockchain for testing
- [Web3.py](https://web3py.readthedocs.io/) — Ethereum interaction library for Python
- [datasketch](https://ekzhu.com/datasketch/) — MinHash LSH implementation
- [Solcx](https://github.com/ApeWorX/solcx) — Solidity compiler for Python

---

<p align="center">
  <sub>Built with ❤️ as a blockchain course project | Experimental prototype — not for production use</sub>
</p>