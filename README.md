# NYC Taxi Data Re-identification Attack (2014 FOIL Vulnerability)

> **Academic Case Study**

A Python/React-based simulation demonstrating how the 2014 NYC Taxi and Limousine Commission (TLC) FOIL data release was vulnerable to linkage/re-identification attacks due to:
1. **Unsalted MD5 hashing** of medallion numbers and hack licenses
2. **Unmasked GPS coordinates and timestamps** left in the clear

This project has been updated with a modern **React + FastAPI** architecture, featuring a highly-polished interactive Cyberpunk HUD and live mapping designed specifically for academic presentations.

## 🏗️ Architecture

```
ROOT/
├── api.py                 # FastAPI backend (REST API)
├── attack_logic.py        # Three-phase re-identification engine
├── mock_data.py           # Synthetic data generator & K-Anonymity cluster simulation
├── config.py              # Shared constants and pre-programmed target trips
├── taxi_data.csv          # Generated synthetic dataset (1,000+ rows)
├── frontend/              # Vite + React + Tailwind Frontend
│   ├── src/App.jsx        # Cyber HUD UI (State, Map, Tooltips)
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

# 2. Generate synthetic dataset (includes decoy K-Anonymity clusters)
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

## 🌍 Global Deployment (Free Hosting)

This project can be deployed globally for free using **Render** (Backend) and **Vercel** (Frontend).

### 1. Deploy the Backend (Render.com)
1. Create a free account on [Render](https://render.com/) and link your GitHub.
2. Click **New +** and select **Web Service**.
3. Connect your GitHub repository.
4. Set the following settings:
   - **Language**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn api:app --host 0.0.0.0 --port $PORT`
5. Click **Deploy**. Once it finishes, copy the URL provided (e.g., `https://your-api.onrender.com`).

### 2. Deploy the Frontend (Vercel)
1. Create a free account on [Vercel](https://vercel.com/) and link your GitHub.
2. Click **Add New Project** and import your repository.
3. In the project configuration, edit the **Root Directory** and select the `frontend/` folder.
4. Expand the **Environment Variables** section and add:
   - **Name**: `VITE_API_URL`
   - **Value**: `[Paste your Render URL here]` (e.g., `https://your-api.onrender.com`)
5. Click **Deploy**. Vercel will build the React app and give you a permanent global URL.

## 🔬 The Attack (Three Phases)

### Phase 1 — Spatial-Temporal Filtering
Given "auxiliary knowledge" (e.g., a paparazzi photo showing a celebrity entering a taxi at The Standard Hotel at 2:03 AM), the attacker queries the dataset for trips with matching pickup coordinates and timestamps.

### Phase 2 — MD5 Hash Reversal
NYC taxi medallion numbers follow a predictable format (`<D><L><D><D>`, e.g., `5Z42`). The entire keyspace is only **18,954 entries**. Hack Licenses are 6-digit numbers (**900,000 entries**). A rainbow table is constructed dynamically, allowing the attacker to reverse the MD5 hashes to recover the real medallion and driver license.

### Phase 3 — Destination Extraction
With the trip uniquely identified, the attacker reads the unmasked drop-off GPS coordinates to discover exactly where the passenger went — potentially a home address, medical facility, or other sensitive location.

## 🛡️ Defense Simulations (How to Fix It)
The dashboard includes toggles to simulate proper anonymization techniques:
1. **Salted Hashes**: Adding a cryptographic salt before hashing explodes the keyspace, making rainbow tables computationally infeasible.
2. **Spatial Cloaking (K-Anonymity)**: Rounding GPS coordinates to 2 decimal places obscures the exact location to ~1.1km blocks, significantly increasing the number of candidate trips in Phase 1 and hiding the individual in a crowd.

## 📈 UI Features & Demonstrations
- **Quick-Select Dossiers**: A dropdown to instantly load pre-programmed target auxiliary knowledge (e.g., Lenox Hill Patient, JFK Airport VIP).
- **Interactive Cyber Map**: Live plotting with `react-leaflet`. Features dynamic auto-zooming (FitBounds) and hover tooltips for fare/timestamp data.
- **K-Anonymity Grid Visualizer**: When Spatial Cloaking is enabled, the map draws a mathematical bounding box representing the exact grid cell that the target's GPS was rounded to, beautifully demonstrating geometric privacy.
- **Cinematic Dashboard**: Features a scanning radar overlay during loading states, slot-machine style rolling metric counters, and a live-typing hacking terminal.
- **Dossier Export**: A one-click "DUMP CSV" button to download the successfully cracked taxi trips to prove the vulnerability is weaponizable.

## 📚 References

- Tockar, A. (2014). *Riding with the stars: Passenger privacy in the NYC taxicab dataset.* Neustar Research.
- Green, B., et al. (2017). *Open data privacy.* Berkman Klein Center for Internet & Society.

## ⚠️ Disclaimer

This project is for **academic and educational purposes only**. It demonstrates known, publicly-documented vulnerabilities in a historical dataset to illustrate data privacy concepts. No real personal data is used or exposed.
