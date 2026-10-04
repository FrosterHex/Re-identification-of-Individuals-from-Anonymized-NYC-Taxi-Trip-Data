"""
app.py — NYC Taxi Data Re-identification Attack Dashboard (Streamlit)

Interactive demonstration of the 2014 FOIL vulnerability where unsalted MD5
hashes on taxi medallions and hack licenses can be trivially reversed, and
precise GPS + timestamp data enables linkage attacks using auxiliary knowledge.

Usage:
    streamlit run app.py

References:
    Tockar, A. (2014). Riding with the stars: Passenger privacy in the NYC
        taxicab dataset. Neustar Research.
    Green, B., et al. (2017). Open data privacy. Berkman Klein Center for
        Internet & Society.
"""

import os

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from attack_logic import RainbowTableCracker, run_attack
from config import DEFAULT_SEARCH_RADIUS_M, DEFAULT_TIME_WINDOW_MIN, KNOWN_LOCATIONS, TARGET_TRIPS

# ──────────────────────────────────────────────────────────────────────────────
# Page Configuration
# ──────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="NYC Taxi Re-identification Attack",
    page_icon="🚕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# Custom Styling
# ──────────────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    /* ── Global ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    .stApp {
        font-family: 'Inter', sans-serif;
    }

    /* ── Hero header ── */
    .hero-container {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        border-radius: 16px;
        padding: 2.5rem 2rem;
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    .hero-title {
        font-size: 2rem;
        font-weight: 700;
        color: #ffffff;
        margin: 0 0 0.5rem 0;
        letter-spacing: -0.02em;
    }
    .hero-subtitle {
        font-size: 1rem;
        color: #a0a0b8;
        margin: 0;
        line-height: 1.6;
    }
    .hero-badge {
        display: inline-block;
        background: rgba(255, 82, 82, 0.15);
        color: #ff5252;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 1rem;
        border: 1px solid rgba(255, 82, 82, 0.25);
    }

    /* ── Phase cards ── */
    .phase-card {
        background: linear-gradient(145deg, #1a1a2e, #16213e);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    }
    .phase-card.phase-1 { border-left-color: #00bcd4; }
    .phase-card.phase-2 { border-left-color: #ff9800; }
    .phase-card.phase-3 { border-left-color: #f44336; }

    .phase-header {
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-bottom: 0.5rem;
    }
    .phase-1 .phase-header { color: #00bcd4; }
    .phase-2 .phase-header { color: #ff9800; }
    .phase-3 .phase-header { color: #f44336; }

    .phase-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #e0e0e0;
        margin-bottom: 0.75rem;
    }

    /* ── Metric boxes ── */
    .metric-row {
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
    }
    .metric-box {
        background: rgba(255, 255, 255, 0.04);
        border-radius: 8px;
        padding: 0.75rem 1rem;
        flex: 1;
        min-width: 140px;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }
    .metric-label {
        font-size: 0.65rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #888;
        margin-bottom: 0.25rem;
    }
    .metric-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1rem;
        font-weight: 500;
        color: #fff;
    }
    .metric-value.danger { color: #ff5252; }
    .metric-value.success { color: #69f0ae; }
    .metric-value.warn { color: #ffd740; }
    .metric-value.info { color: #40c4ff; }

    /* ── Hash reveal ── */
    .hash-reveal {
        background: rgba(0, 0, 0, 0.3);
        border-radius: 8px;
        padding: 1rem;
        margin-top: 0.5rem;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .hash-row {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 0.5rem;
    }
    .hash-label {
        font-size: 0.7rem;
        color: #888;
        min-width: 80px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .hash-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        color: #ccc;
        word-break: break-all;
    }
    .hash-arrow {
        color: #ff9800;
        font-size: 1.2rem;
    }
    .hash-cracked {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1rem;
        font-weight: 600;
        color: #ff5252;
        background: rgba(255, 82, 82, 0.1);
        padding: 0.15rem 0.5rem;
        border-radius: 4px;
    }

    /* ── Sidebar styling ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0c29 0%, #1a1a2e 100%);
    }
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #e0e0e0;
    }

    /* ── Warning banner ── */
    .warning-banner {
        background: linear-gradient(135deg, rgba(255, 82, 82, 0.08), rgba(255, 152, 0, 0.08));
        border: 1px solid rgba(255, 82, 82, 0.2);
        border-radius: 10px;
        padding: 1rem 1.25rem;
        margin: 1rem 0;
        font-size: 0.85rem;
        color: #e0e0e0;
        line-height: 1.5;
    }

    /* ── Section dividers ── */
    .section-divider {
        border: none;
        border-top: 1px solid rgba(255, 255, 255, 0.06);
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# Load Data
# ──────────────────────────────────────────────────────────────────────────────

DATA_PATH = os.path.join(os.path.dirname(__file__), "taxi_data_2014.csv")


@st.cache_data
def load_data() -> pd.DataFrame:
    """Load the synthetic taxi dataset."""
    return pd.read_csv(DATA_PATH)


df = load_data()


# ──────────────────────────────────────────────────────────────────────────────
# Hero Header
# ──────────────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="hero-container">
    <div class="hero-badge">🔓 Data Privacy Case Study</div>
    <h1 class="hero-title">NYC Taxi Re-identification Attack</h1>
    <p class="hero-subtitle">
        Demonstrating how unsalted MD5 hashing and unmasked GPS coordinates in the
        2014 NYC TLC FOIL release allowed trivial de-anonymization of taxi passengers
        using publicly available auxiliary knowledge.
    </p>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# Sidebar — Attacker's Auxiliary Knowledge
# ──────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🕵️ Attacker's Auxiliary Knowledge")
    st.markdown(
        '<p style="color:#999; font-size:0.8rem;">'
        "Simulate what an attacker would know — e.g., a paparazzi photo showing "
        "a celebrity entering a taxi at a specific time and place."
        "</p>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Preset scenarios
    st.markdown("### 📍 Known Location")
    preset = st.selectbox(
        "Select a known location",
        options=["Custom"] + list(KNOWN_LOCATIONS.keys()),
        index=0,
        help="Pick a known NYC landmark or enter custom coordinates.",
    )

    if preset != "Custom":
        loc = KNOWN_LOCATIONS[preset]
        default_lat = loc["lat"]
        default_lon = loc["lon"]
        st.info(f"ℹ️ {loc['description']}")
    else:
        default_lat = 40.7408
        default_lon = -74.0080

    target_lat = st.number_input(
        "Pickup Latitude", value=default_lat, format="%.6f",
        min_value=40.0, max_value=41.0, step=0.0001,
    )
    target_lon = st.number_input(
        "Pickup Longitude", value=default_lon, format="%.6f",
        min_value=-74.5, max_value=-73.0, step=0.0001,
    )

    st.markdown("---")
    st.markdown("### 🕐 Known Time")

    # Quick-fill from target trips
    target_preset = st.selectbox(
        "Quick-fill from planted targets",
        options=["Manual Entry"] + [t["label"] for t in TARGET_TRIPS],
    )

    if target_preset != "Manual Entry":
        trip_info = next(t for t in TARGET_TRIPS if t["label"] == target_preset)
        default_time = trip_info["pickup_datetime"]
        # Also set the correct location
        target_lat = trip_info["pickup_lat"]
        target_lon = trip_info["pickup_lon"]
    else:
        default_time = "2014-06-15 02:03:00"

    target_time = st.text_input(
        "Pickup Datetime (YYYY-MM-DD HH:MM:SS)",
        value=default_time,
    )

    st.markdown("---")
    st.markdown("### ⚙️ Search Parameters")

    radius_m = st.slider(
        "Spatial Radius (meters)", 10, 500, DEFAULT_SEARCH_RADIUS_M,
        help="How close must a trip's pickup be to the target GPS coordinates?",
    )
    window_min = st.slider(
        "Time Window (± minutes)", 1, 30, DEFAULT_TIME_WINDOW_MIN,
        help="How close must a trip's pickup time be to the target time?",
    )

    st.markdown("---")
    crack_hack = st.checkbox(
        "Also crack hack license hash",
        value=False,
        help="Builds a 900K-entry rainbow table. Takes a few seconds longer.",
    )

    st.markdown("---")
    st.markdown("### 🛡️ Defense Simulations")
    is_salted = st.checkbox(
        "Simulate Salted Hashes",
        value=False,
        help="If the TLC had used a cryptographic salt, rainbow tables would be infeasible.",
    )
    
    cloak_enabled = st.checkbox("Apply Spatial Cloaking (K-Anonymity)", value=False)
    cloak_precision = None
    if cloak_enabled:
        cloak_precision = st.slider(
            "GPS Precision (decimals)", 1, 4, 2,
            help="Rounding to 2 decimals obscures exact locations to ~1.1km blocks.",
        )

    st.markdown("---")
    run_button = st.button(
        "🚀 LAUNCH ATTACK",
        use_container_width=True,
        type="primary",
    )


# ──────────────────────────────────────────────────────────────────────────────
# Tab Layout
# ──────────────────────────────────────────────────────────────────────────────

tab_data, tab_attack, tab_map, tab_metrics = st.tabs([
    "📊 Raw Data",
    "⚡ Attack Results",
    "🗺️ Map Visualization",
    "📈 Performance Metrics",
])

# ── Tab 1: Raw Data ──────────────────────────────────────────────────────────

with tab_data:
    st.markdown("### The 'Anonymized' Dataset")
    st.markdown(
        '<div class="warning-banner">'
        "⚠️ <strong>This is how the data was released.</strong> Medallion and hack "
        "license numbers are hashed with unsalted MD5. GPS coordinates and timestamps "
        "are <em>completely unmasked</em> — the core vulnerability."
        "</div>",
        unsafe_allow_html=True,
    )

    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.metric("Total Records", f"{len(df):,}")
    with col_info2:
        st.metric("Columns", len(df.columns))
    with col_info3:
        st.metric("Hashed Fields", "2 (medallion, hack license)")

    st.dataframe(df, use_container_width=True, height=400)

    with st.expander("🔍 Column Descriptions"):
        st.markdown("""
| Column | Description | Privacy Risk |
|---|---|---|
| `medallion_hash` | MD5(vehicle medallion number) — unsalted | 🔴 Reversible |
| `hack_license_hash` | MD5(driver hack license) — unsalted | 🔴 Reversible |
| `pickup_datetime` | Exact pickup timestamp | 🔴 Unmasked |
| `dropoff_datetime` | Exact drop-off timestamp | 🔴 Unmasked |
| `pickup_longitude/latitude` | Precise pickup GPS | 🔴 Unmasked |
| `dropoff_longitude/latitude` | Precise drop-off GPS | 🔴 Unmasked |
| `fare_amount` | Trip fare in USD | 🟡 Quasi-identifier |
        """)


# ── Tab 2: Attack Results ───────────────────────────────────────────────────

with tab_attack:
    if not run_button:
        st.markdown(
            '<div style="text-align:center; padding:4rem 2rem; color:#666;">'
            '<p style="font-size:3rem;">🕵️</p>'
            '<p style="font-size:1.1rem; font-weight:500;">Configure attack parameters in the sidebar</p>'
            '<p style="font-size:0.85rem; margin-top:0.5rem;">Then press <strong>LAUNCH ATTACK</strong> to begin the re-identification simulation.</p>'
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        with st.spinner("Executing re-identification attack..."):
            result = run_attack(
                df,
                target_lat=target_lat,
                target_lon=target_lon,
                target_time=target_time,
                radius_m=radius_m,
                window_min=window_min,
                crack_hack_license=crack_hack,
                cloak_precision=cloak_precision,
                is_salted=is_salted,
            )

        if not result["success"]:
            st.error(
                f"❌ **No matching trips found.** "
                f"No pickups within {radius_m}m of ({target_lat}, {target_lon}) "
                f"within ±{window_min} min of {target_time}. "
                f"Try increasing the search radius or time window."
            )
        else:
            dest = result["destination"]
            stats = result["rainbow_table_stats"]

            # ── Phase 1 ──
            st.markdown(f"""
<div class="phase-card phase-1">
    <div class="phase-header">Phase 1 — Spatial-Temporal Filtering</div>
    <div class="phase-title">Isolating candidate trips using auxiliary knowledge</div>
    <div class="metric-row">
        <div class="metric-box">
            <div class="metric-label">Target Coordinates</div>
            <div class="metric-value info">{target_lat:.4f}, {target_lon:.4f}</div>
        </div>
        <div class="metric-box">
            <div class="metric-label">Target Time</div>
            <div class="metric-value info">{target_time}</div>
        </div>
        <div class="metric-box">
            <div class="metric-label">Candidates Found</div>
            <div class="metric-value {'success' if result['phase1_candidates'] == 1 else 'warn'}">{result['phase1_candidates']}</div>
        </div>
        <div class="metric-box">
            <div class="metric-label">Filter Time</div>
            <div class="metric-value">{result.get('phase1_time_s', 'N/A')}s</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

            # ── Phase 2 ──
            cracked_med = result["cracked_medallion"] or "N/A"
            cracked_hack = result.get("cracked_hack_license") or "—"

            st.markdown(f"""
<div class="phase-card phase-2">
    <div class="phase-header">Phase 2 — MD5 Hash Reversal (Rainbow Table)</div>
    <div class="phase-title">Cracking the "anonymized" identifiers</div>
    <div class="metric-row">
        <div class="metric-box">
            <div class="metric-label">Medallion Keyspace</div>
            <div class="metric-value warn">{stats['medallion_keyspace']:,} hashes</div>
        </div>
        <div class="metric-box">
            <div class="metric-label">Table Build Time</div>
            <div class="metric-value">{stats['medallion_build_time_s']}s</div>
        </div>
        <div class="metric-box">
            <div class="metric-label">Lookup Time</div>
            <div class="metric-value success">{result.get('phase2_time_s', 'N/A')}s</div>
        </div>
    </div>
    <div class="hash-reveal">
        <div class="hash-row">
            <span class="hash-label">MD5 Hash</span>
            <span class="hash-value">{dest['medallion_hash']}</span>
            <span class="hash-arrow">→</span>
            <span class="hash-cracked">{cracked_med}</span>
        </div>
        <div class="hash-row">
            <span class="hash-label">Hack Lic.</span>
            <span class="hash-value">{dest['hack_license_hash']}</span>
            <span class="hash-arrow">→</span>
            <span class="hash-cracked">{cracked_hack}</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

            # ── Phase 3 ──
            st.markdown(f"""
<div class="phase-card phase-3">
    <div class="phase-header">Phase 3 — Destination Exposed</div>
    <div class="phase-title">The passenger's private destination is now revealed</div>
    <div class="metric-row">
        <div class="metric-box">
            <div class="metric-label">Drop-off Latitude</div>
            <div class="metric-value danger">{dest['dropoff_latitude']}</div>
        </div>
        <div class="metric-box">
            <div class="metric-label">Drop-off Longitude</div>
            <div class="metric-value danger">{dest['dropoff_longitude']}</div>
        </div>
        <div class="metric-box">
            <div class="metric-label">Drop-off Time</div>
            <div class="metric-value danger">{dest['dropoff_datetime']}</div>
        </div>
        <div class="metric-box">
            <div class="metric-label">Fare Amount</div>
            <div class="metric-value danger">${dest['fare_amount']}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

            # Show the matched dataframe
            st.markdown("#### Matched Trip Records")
            st.dataframe(result["matched_trips"], use_container_width=True)

            st.markdown("---")
            report_md = f"""# NYC Taxi Re-identification Attack Report
            
## Phase 1: Spatial-Temporal Filtering
- Target: {target_lat}, {target_lon} at {target_time}
- Candidates Found: {result['phase1_candidates']}

## Phase 2: Hash Reversal (Rainbow Table)
- Cracked Medallion: {cracked_med}
- Cracked Hack License: {cracked_hack}

## Phase 3: Destination Exposed
- Drop-off Location: {dest['dropoff_latitude']}, {dest['dropoff_longitude']}
- Drop-off Time: {dest['dropoff_datetime']}
- Fare: ${dest['fare_amount']}
"""
            st.download_button(
                label="📄 Download Attack Summary (Markdown)",
                data=report_md,
                file_name="attack_summary.md",
                mime="text/markdown",
            )


# ── Tab 3: Map Visualization ────────────────────────────────────────────────

with tab_map:
    if not run_button:
        st.markdown(
            '<div style="text-align:center; padding:4rem 2rem; color:#666;">'
            '<p style="font-size:3rem;">🗺️</p>'
            '<p style="font-size:1.1rem; font-weight:500;">Run an attack to see the map</p>'
            '<p style="font-size:0.85rem; margin-top:0.5rem;">The map will show the pickup (red) and revealed drop-off (green) locations.</p>'
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        if not result["success"]:
            st.warning("No trips matched — nothing to plot.")
        else:
            dest = result["destination"]
            pickup_coords = [dest["pickup_latitude"], dest["pickup_longitude"]]
            dropoff_coords = [dest["dropoff_latitude"], dest["dropoff_longitude"]]

            # Center the map between pickup and dropoff
            center_lat = (pickup_coords[0] + dropoff_coords[0]) / 2
            center_lon = (pickup_coords[1] + dropoff_coords[1]) / 2

            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=12,
                tiles="CartoDB dark_matter",
            )

            # Pickup marker (red)
            folium.Marker(
                pickup_coords,
                popup=folium.Popup(
                    f"<b>PICKUP (Known)</b><br>"
                    f"Time: {dest['pickup_datetime']}<br>"
                    f"Lat: {pickup_coords[0]}<br>"
                    f"Lon: {pickup_coords[1]}",
                    max_width=300,
                ),
                tooltip="Pickup Location (Auxiliary Knowledge)",
                icon=folium.Icon(color="red", icon="info-sign"),
            ).add_to(m)

            # Pickup radius circle
            folium.Circle(
                pickup_coords,
                radius=radius_m,
                color="#ff5252",
                fill=True,
                fill_opacity=0.15,
                popup=f"Search radius: {radius_m}m",
            ).add_to(m)

            # Dropoff marker (green)
            folium.Marker(
                dropoff_coords,
                popup=folium.Popup(
                    f"<b>DROP-OFF (EXPOSED!)</b><br>"
                    f"Time: {dest['dropoff_datetime']}<br>"
                    f"Lat: {dropoff_coords[0]}<br>"
                    f"Lon: {dropoff_coords[1]}<br>"
                    f"Fare: ${dest['fare_amount']}",
                    max_width=300,
                ),
                tooltip="Drop-off Location (REVEALED)",
                icon=folium.Icon(color="green", icon="home"),
            ).add_to(m)

            # Connecting line (the exposed route)
            folium.PolyLine(
                [pickup_coords, dropoff_coords],
                color="#ffd740",
                weight=3,
                opacity=0.8,
                dash_array="10",
                tooltip="Exposed Trip Route",
            ).add_to(m)

            # Legend
            legend_html = """
            <div style="
                position: fixed;
                bottom: 50px; left: 50px;
                background: rgba(15, 12, 41, 0.92);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 10px;
                padding: 12px 16px;
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                color: #ccc;
                z-index: 9999;
                box-shadow: 0 4px 16px rgba(0,0,0,0.4);
            ">
                <div style="font-weight:600; margin-bottom:8px; color:#fff;">Legend</div>
                <div>🔴 Pickup — Known (Auxiliary Knowledge)</div>
                <div>🟢 Drop-off — <span style="color:#ff5252; font-weight:600;">EXPOSED</span></div>
                <div>🟡 Dashed — Inferred Trip Route</div>
            </div>
            """
            m.get_root().html.add_child(folium.Element(legend_html))

            st_folium(m, use_container_width=True, height=550)

            st.markdown(
                '<div class="warning-banner">'
                "🚨 <strong>Privacy Implication:</strong> An attacker who knew the "
                "passenger entered a taxi at the red marker now knows exactly where "
                "they went (green marker). This could reveal a home address, a "
                "medical facility, a political meeting — any destination the "
                "passenger believed was private."
                "</div>",
                unsafe_allow_html=True,
            )


# ── Tab 4: Performance Metrics ──────────────────────────────────────────────

with tab_metrics:
    if not run_button:
        st.markdown(
            '<div style="text-align:center; padding:4rem 2rem; color:#666;">'
            '<p style="font-size:3rem;">📈</p>'
            '<p style="font-size:1.1rem; font-weight:500;">Run an attack to see metrics</p>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown("### Attack Performance Metrics")
        st.markdown(
            "These metrics demonstrate how computationally trivial the attack is — "
            "the entire re-identification completes in under a second."
        )

        if result["success"]:
            stats = result["rainbow_table_stats"]

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(
                    "Phase 1: Filtering",
                    f"{result.get('phase1_time_s', 0) * 1000:.1f} ms",
                    help="Time to scan 1,000 rows with Haversine + timestamp filter.",
                )
            with col2:
                st.metric(
                    "Phase 2: Rainbow Build",
                    f"{stats['medallion_build_time_s'] * 1000:.1f} ms",
                    help="Time to precompute all 18,954 medallion hashes.",
                )
            with col3:
                st.metric(
                    "Phase 2: Hash Lookup",
                    f"{result.get('phase2_time_s', 0) * 1_000_000:.0f} µs",
                    help="Time to look up the cracked hash in the rainbow table.",
                )
            with col4:
                total_ms = (
                    result.get("phase1_time_s", 0)
                    + stats["medallion_build_time_s"]
                    + result.get("phase2_time_s", 0)
                ) * 1000
                st.metric(
                    "Total Attack Time",
                    f"{total_ms:.1f} ms",
                    help="End-to-end time for the full re-identification.",
                )

            st.markdown("---")

            # Keyspace comparison
            st.markdown("### Rainbow Table Keyspace Analysis")
            st.markdown(
                "The small, predictable format of NYC taxi identifiers makes "
                "rainbow table construction trivial."
            )

            keyspace_data = pd.DataFrame([
                {
                    "Identifier": "Medallion Number",
                    "Format": "<D><L><D><D>",
                    "Example": "5Z42",
                    "Total Keyspace": f"{stats['medallion_keyspace']:,}",
                    "Build Time": f"{stats['medallion_build_time_s']*1000:.1f} ms",
                    "Feasibility": "Trivial",
                },
                {
                    "Identifier": "Hack License",
                    "Format": "6-digit numeric",
                    "Example": "437289",
                    "Total Keyspace": f"{stats.get('hack_license_keyspace', 900_000):,}" if isinstance(stats.get('hack_license_keyspace'), int) else stats.get('hack_license_keyspace'),
                    "Build Time": f"{stats.get('hack_license_build_time_s', 0)*1000:.1f} ms"
                                  if isinstance(stats.get("hack_license_keyspace", 0), int) and stats.get("hack_license_keyspace", 0) > 0
                                  else str(stats.get('hack_license_build_time_s', "Not built")),
                    "Feasibility": "Trivial" if not is_salted else "Infeasible",
                },
                {
                    "Identifier": "Comparison: 8-char password",
                    "Format": "[a-zA-Z0-9]",
                    "Example": "pA55w0rD",
                    "Total Keyspace": "218,340,105,584,896",
                    "Build Time": "Days to years",
                    "Feasibility": "Hard",
                },
            ])
            st.dataframe(keyspace_data, use_container_width=True, hide_index=True)

            if not is_salted:
                st.info(f"💾 **Memory Footprint:** The rainbow tables consume approximately **{stats.get('memory_usage_mb', 0)} MB** of RAM. This demonstrates that the attack can be run on a standard, low-resource laptop without specialized hardware.")

            st.markdown("---")

            # Attack parameters summary
            st.markdown("### Attack Configuration Summary")
            params = result["attack_params"]
            config_data = pd.DataFrame([
                {"Parameter": "Target Latitude", "Value": str(params["target_lat"])},
                {"Parameter": "Target Longitude", "Value": str(params["target_lon"])},
                {"Parameter": "Target Time", "Value": params["target_time"]},
                {"Parameter": "Search Radius", "Value": f"{params['radius_m']} m"},
                {"Parameter": "Time Window", "Value": f"± {params['window_min']} min"},
                {"Parameter": "Dataset Size", "Value": f"{len(df):,} rows"},
                {"Parameter": "Candidates Found", "Value": str(result["phase1_candidates"])},
                {"Parameter": "Unique Match", "Value": "Yes" if result["phase1_candidates"] == 1 else "No"},
            ])
            st.dataframe(config_data, use_container_width=True, hide_index=True)

        else:
            st.info("Attack did not find matching trips. Adjust parameters and retry.")


# ──────────────────────────────────────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────────────────────────────────────

st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
st.markdown(
    '<div style="text-align:center; color:#555; font-size:0.75rem; padding:1rem 0;">'
    "<strong>Academic Use Only</strong> — Data Privacy Case Study | "
    "Tockar (2014), Green et al. (2017)"
    "</div>",
    unsafe_allow_html=True,
)
