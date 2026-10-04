# NYC Taxi Data Re-identification Attack (2014 FOIL Vulnerability)

> **Academic Case Study** — Data Privacy, Semester 7

A Python/React-based simulation demonstrating how the 2014 NYC Taxi and Limousine Commission (TLC) FOIL data release was vulnerable to linkage/re-identification attacks due to:
1. **Unsalted MD5 hashing** of medallion numbers and hack licenses
2. **Unmasked GPS coordinates and timestamps** left in the clear

This project has been updated with a modern **React + FastAPI** architecture, featuring an interactive Cyberpunk HUD and live mapping.

## 🏗️ Architecture

```
ROOT/
├── api.py                 # FastAPI backend (REST API)
├── attack_logic.py        # Three-phase re-identification engine
├── mock_data.py           # Synthetic data generator (1,000 rows)
├── config.py              # Shared constants and target trips
├── taxi_data_2014.csv     # Generated synthetic dataset
├── frontend/              # Vite + React + Tailwind Frontend
│   ├── src/App.jsx        # Cyber HUD UI
│   └── src/index.css      # Custom Cyberpunk Tailwind V3 styling
├── requirements.txt       # Python backend dependencies
└── README.md              # This file
```

## ⚡ Quick Start

### 1. Backend Setup (FastAPI)
Open a terminal in the root directory:
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate synthetic dataset (if not already present)
python mock_data.py

# 3. Launch the FastAPI server
uvicorn api:app --reload
```

### 2. Frontend Setup (React/Vite)
Open a second terminal in the `frontend/` directory:
```bash
# 1. Install NPM dependencies
npm install

# 2. Launch the Vite Dev Server
npm run dev
```

Then navigate to `http://localhost:5173` in your browser to view the Cyber HUD.

## 🔬 The Attack (Three Phases)

### Phase 1 — Spatial-Temporal Filtering
Given "auxiliary knowledge" (e.g., a paparazzi photo showing a celebrity entering a taxi at The Standard Hotel at 2:03 AM), the attacker queries the dataset for trips with matching pickup coordinates and timestamps.

### Phase 2 — MD5 Hash Reversal
NYC taxi medallion numbers follow a predictable format (`<D><L><D><D>`, e.g., `5Z42`). The entire keyspace is only **18,954 entries** — a rainbow table can be constructed in **~20 milliseconds**. The attacker reverses the MD5 hash to recover the real medallion number.

### Phase 3 — Destination Extraction
With the trip uniquely identified, the attacker reads the unmasked drop-off GPS coordinates to discover exactly where the passenger went — potentially a home address, medical facility, or other sensitive location.

## 🛡️ Defense Simulations (How to Fix It)
The dashboard includes toggles to simulate proper anonymization techniques:
1. **Salted Hashes**: Adding a cryptographic salt before hashing explodes the keyspace, making rainbow tables computationally infeasible.
2. **Spatial Cloaking (K-Anonymity)**: Rounding GPS coordinates to 2 decimal places obscures the exact location to ~1.1km blocks, significantly increasing the number of candidate trips in Phase 1 and hiding the individual in a crowd.

## 📈 UI Features & Demonstrations
- **Interactive Cyber Map**: Features CartoDB Dark Matter tiles, glowing markers, and draws the de-anonymized trajectories on a live map using React-Leaflet.
- **Terminal Simulation**: Live-typing hacking console logs that provide step-by-step insight into the internal execution of the attack logic.
- **Dossier Export**: A one-click "DUMP CSV" button to download the successfully cracked taxi trips to prove the vulnerability is weaponizable.

## 📚 References

- Tockar, A. (2014). *Riding with the stars: Passenger privacy in the NYC taxicab dataset.* Neustar Research.
- Green, B., et al. (2017). *Open data privacy.* Berkman Klein Center for Internet & Society.

## ⚠️ Disclaimer

This project is for **academic and educational purposes only**. It demonstrates known, publicly-documented vulnerabilities in a historical dataset to illustrate data privacy concepts. No real personal data is used or exposed.
