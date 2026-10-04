# NYC Taxi Data Re-identification Attack (2014 FOIL Vulnerability)

> **Academic Case Study** — Data Privacy, Semester 7

A Python-based simulation demonstrating how the 2014 NYC Taxi and Limousine Commission (TLC) FOIL data release was vulnerable to linkage/re-identification attacks due to:
1. **Unsalted MD5 hashing** of medallion numbers and hack licenses
2. **Unmasked GPS coordinates and timestamps** left in the clear

## 🏗️ Architecture

```
ROOT/
├── config.py              # Shared constants, landmark coordinates, target trips
├── mock_data.py           # Synthetic data generator (1,000 rows)
├── attack_logic.py        # Three-phase re-identification engine
├── app.py                 # Streamlit interactive dashboard
├── taxi_data_2014.csv     # Generated synthetic dataset
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## ⚡ Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate synthetic dataset (if not already present)
python mock_data.py

# 3. Launch the dashboard
streamlit run app.py
```

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

## 📈 New Features
- **Realistic Data Generation**: Fares are calculated dynamically based on Haversine distance, and random pickups are constrained to land bounds (Manhattan/Brooklyn/Queens) instead of water.
- **Memory Profiling**: Shows how lightweight the rainbow tables are (only a few megabytes of RAM required).
- **Report Export**: Easily export the attack summary (Phase 1, 2, 3 metrics) directly to Markdown for academic reporting.

## 📚 References

- Tockar, A. (2014). *Riding with the stars: Passenger privacy in the NYC taxicab dataset.* Neustar Research.
- Green, B., et al. (2017). *Open data privacy.* Berkman Klein Center for Internet & Society.

## ⚠️ Disclaimer

This project is for **academic and educational purposes only**. It demonstrates known, publicly-documented vulnerabilities in a historical dataset to illustrate data privacy concepts. No real personal data is used or exposed.
