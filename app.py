import streamlit as st
import sqlite3
from datetime import datetime

# ---------------------------------------------------------
# PRODUCTION DATABASE ARCHITECTURE
# ---------------------------------------------------------
def init_db():
    conn = sqlite3.connect('livestock_farm_web.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Animals Directory Table supporting sub-classifications
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS animals (
            tag_id TEXT PRIMARY KEY,
            species TEXT CHECK(species IN ('Cattle', 'Sheep', 'Goat')),
            subtype TEXT,
            birth_date TEXT,
            status TEXT DEFAULT 'Active'
        )
    ''')
    # Biometric Weight Tracker
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weight_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag_id TEXT,
            weigh_date TEXT,
            weight_kg REAL,
            FOREIGN KEY(tag_id) REFERENCES animals(tag_id)
        )
    ''')
    # Regulated Veterinary Health Logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS health_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag_id TEXT,
            treatment_date TEXT,
            treatment_type TEXT,
            product_name TEXT,
            FOREIGN KEY(tag_id) REFERENCES animals(tag_id)
        )
    ''')
    # Nutritional Allocation Logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feed_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag_id TEXT,
            log_date TEXT,
            feed_type TEXT,
            quantity_kg REAL,
            FOREIGN KEY(tag_id) REFERENCES animals(tag_id)
        )
    ''')
    conn.commit()
    return conn

conn = init_db()

# ---------------------------------------------------------
# STRUCTURED SOUTH AFRICAN AGRICULTURAL DIRECTORIES
# ---------------------------------------------------------
DATA_DIRECTORY = {
    "Cattle": {
        "subtypes": ["Bull", "Cow", "Calf"],
        "vaccines": ["Brucellosis (S19/RB51 Mandatory)", "Anthrax & Black Quarter", "Lumpy Skin Disease (LSD)", "Rift Valley Fever (RVF)", "Foot-and-Mouth Disease (FMD)"],
        "feeds": ["Cattle Creep Feed", "Beef Production Lick", "High-Protein Concentrate", "Lucerne / Teff Hay Bales", "Winter Maintenance Block"]
    },
    "Sheep": {
        "subtypes": ["Ram", "Ewe", "Lamb"],
        "vaccines": ["Pulpy Kidney (Bloednier)", "Bluetongue (3-Bottle System)", "Pasteurella (Lungsiekte)", "Enzootic Abortion"],
        "feeds": ["Lamb Creep Pellets", "Ewe Production Lick", "Lucerne Forage", "Finishing Feed / Backgrounding"]
    },
    "Goat": {
        "subtypes": ["Buck", "Doe", "Kid"],
        "vaccines": ["Pulpy Kidney (Bloednier)", "Pasteurella (Pneumonia)", "Bluetongue (Midge Protection)", "Tetanus / Clostridial"],
        "feeds": ["Goat Booster Pellets", "Browse / Bush Forage Supplement", "Lucerne Hay", "General Ruminant Lick"]
    }
}

# ---------------------------------------------------------
# WEB INTERFACE SYSTEM CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(page_title="Enterprise Livestock Management", page_icon="🇿🇦", layout="wide")

st.title("🇿🇦 Enterprise Livestock Management & Record System")
st.markdown("---")

# Navigation Sidebar
menu = ["➕ Register Stock", "⚖️ Log Biometrics", "💉 Veterinary Logs", "🌾 Feed Allocation", "🔍 Search & Performance Analytics"]
choice = st.sidebar.selectbox("Application Navigation Menu", menu)

# Database Query Helper Operations
def get_animal_profile(tag_id):
    cursor = conn.cursor()
    cursor.execute("SELECT species, subtype, birth_date, status FROM animals WHERE tag_id = ?", (tag_id,))
    return cursor.fetchone()

def get_all_active_tags():
    cursor = conn.cursor()
    cursor.execute("SELECT tag_id FROM animals WHERE status = 'Active'")
    return [row[0] for row in cursor.fetchall()]

# ---------------------------------------------------------
# INTERFACE PATTERN 1: REGISTER STOCK
# ---------------------------------------------------------
if choice == "➕ Register Stock":
    st.header("Animal Demographics Registry Entry")
    
    with st.form("register_form", clear_on_submit=True):
        tag_id = st.text_input("Unique Ear-Tag ID:").strip()
        species = st.selectbox("Livestock Species Group:", ["Cattle", "Sheep", "Goat"])
        subtype = st.selectbox("Animal Subtype / Class:", DATA_DIRECTORY[species]["subtypes"])
        submitted = st.form_submit_button("Commit Entry to Registry")
        
        if submitted:
            if not tag_id:
                st.error("Validation Omission: Unique Identification Ear-Tag ID parameter required.")
            else:
                cursor = conn.cursor()
                try:
                    bdate = datetime.now().strftime("%Y-%m-%d")
                    cursor.execute("INSERT INTO animals (tag_id, species, subtype, birth_date) VALUES (?, ?, ?, ?)", 
                                   (tag_id, species, subtype, bdate))
                    conn.commit()
                    st.success(f"Asset Profile [{species} - {subtype}] logged successfully under Tag {tag_id}!")
                except sqlite3.IntegrityError:
                    st.error("Conflict Warning: Primary Key Error: Unique Identification Ear-Tag ID already exists in index.")

# ---------------------------------------------------------
# INTERFACE PATTERN 2: LOG BIOMETRICS
# ---------------------------------------------------------
elif choice == "⚖️ Log Biometrics":
    st.header("Live Weight Monitoring Scale Logs")
    active_tags = get_all_active_tags()
    
    if not active_tags:
        st.info("No active animals discovered in the system register. Please add stock records first.")
    else:
        with st.form("weight_form", clear_on_submit=True):
            tag_id = st.selectbox("Select Target Animal Ear-Tag ID:", active_tags)
            weight = st.number_input("Scale Weight Reading (kg):", min_value=0.1, step=0.1)
            submitted = st.form_submit_button("Log Verified Weight Statement")
            
            if submitted:
                cursor = conn.cursor()
                wdate = datetime.now().strftime("%Y-%m-%d")
                cursor.execute("INSERT INTO weight_logs (tag_id, weigh_date, weight_kg) VALUES (?, ?, ?)", (tag_id, wdate, weight))
                conn.commit()
                st.success(f"Biometric Weight Entry securely tracked for asset entry {tag_id}.")

# ---------------------------------------------------------
# INTERFACE PATTERN 3: VETERINARY LOGS
# ---------------------------------------------------------
elif choice == "💉 Veterinary Logs":
    st.header("Veterinary Medicine & Immunisation Logs")
    active_tags = get_all_active_tags()
    
    if not active_tags:
        st.info("No active livestock database entries found to assign clinical events to.")
    else:
        tag_id = st.selectbox("Select Target Animal Ear-Tag ID:", active_tags)
        profile = get_animal_profile(tag_id)
        species = profile[0]
        
        with st.form("health_form", clear_on_submit=True):
            st.caption(f"Selected Asset Profile Background Taxonomy: **{species} ({profile[1]})**")
            treatment_type = st.selectbox("Medical Treatment Classification:", ["Vaccination", "Deworming", "Emergency Medical Treatment"])
            
            # Dynamic conditional options filtering matching the selected asset species
            allowed_remedies = DATA_DIRECTORY[species]["vaccines"] + ["Standard Deworming Treatment", "Oxytetracycline LA Antibiotic"]
            product_name = st.selectbox("Pre-Approved Local Protocol Remedy:", allowed_remedies)
            
            submitted = st.form_submit_button("Commit Medical Record Line Item")
            
            if submitted:
                cursor = conn.cursor()
                hdate = datetime.now().strftime("%Y-%m-%d")
                cursor.execute("INSERT INTO health_logs (tag_id, treatment_date, treatment_type, product_name) VALUES (?, ?, ?, ?)", 
                               (tag_id, hdate, treatment_type, product_name))
                conn.commit()
                st.success("Veterinary Health Log written to Ledger successfully.")

# ---------------------------------------------------------
# INTERFACE PATTERN 4: FEED ALLOCATION
# ---------------------------------------------------------
elif choice == "🌾 Feed Allocation":
    st.header("Feed & Nutritional Allocation Tracker")
    active_tags = get_all_active_tags()
    
    if not active_tags:
        st.info("No active livestock database entries found to allocate nutritional feeding items to.")
    else:
        tag_id = st.selectbox("Select Target Animal Ear-Tag ID:", active_tags)
        profile = get_animal_profile(tag_id)
        species = profile[0]
        
        with st.form("feed_form", clear_on_submit=True):
            st.caption(f"Selected Asset Profile Background Taxonomy: **{species} ({profile[1]})**")
            feed_type = st.selectbox("Nutritional Rations Selection Reference:", DATA_DIRECTORY[species]["feeds"])
            quantity = st.number_input("Allocated Weight Quantity Mass (kg):", min_value=0.01, step=0.1)
            submitted = st.form_submit_button("Commit Feed Allocation Record")
            
            if submitted:
                cursor = conn.cursor()
                ldate = datetime.now().strftime("%Y-%m-%d")
                cursor.execute("INSERT INTO feed_logs (tag_id, log_date, feed_type, quantity_kg) VALUES (?, ?, ?, ?)", 
                               (tag_id, ldate, feed_type, quantity))
                conn.commit()
                st.success("Nutritional Allocation statement written to Ledger successfully.")

# ---------------------------------------------------------
# INTERFACE PATTERN 5: SEARCH & PERFORMANCE ANALYTICS
# ---------------------------------------------------------
elif choice == "🔍 Search & Performance Analytics":
    st.header("Asset Registry Search Query & Executive Audit")
    
    search_id = st.text_input("Search System Ear-Tag ID:").strip()
    
    if search_id:
        profile = get_animal_profile(search_id)
        
        if not profile:
            st.error(f"Query Execution Terminated: Reference target index '{search_id}' does not exist inside active data tables.")
        else:
            species, subtype, bdate, status = profile
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📋 Core Profile Summary")
                st.text(f"Asset Ear-Tag ID:   {search_id}\nSpecies Group:      {species}\nSubtype Class:      {subtype}\nRegistration Date:  {bdate}\nOperational Status: {status}")
            
            with col2:
                st.subheader("📚 South African Guide Checklist Tracker")
                st.write(f"**Required Routine Protocol For {species.upper()}:**")
                for v in DATA_DIRECTORY[species]["vaccines"]:
                    st.markdown(f"- {v}")
            
            st.markdown("---")
            
            # Mathematical Performance Evaluator Engine (ADG calculations over timestamps)
            st.subheader("📈 Metrology & Biometric Performance (Average Daily Gain)")
            cursor = conn.cursor()
            cursor.execute("SELECT weigh_date, weight_kg FROM weight_logs WHERE tag_id = ? ORDER BY weigh_date ASC", (search_id,))
            weights = cursor.fetchall()
            
            if not weights:
                st.warning("No verified scale biometrics archived for this unique identity target.")
            else:
                for i in range(len(weights)):
                    curr_date, curr_w = weights[i]
                    if i == 0:
                        st.info(f"📍 [{curr_date}] Baseline Weight Logged: **{curr_w} kg**")
                    else:
                        prev_date, prev_w = weights[i-1]
                        d1 = datetime.strptime(prev_date, "%Y-%m-%d")
                        d2 = datetime.strptime(curr_date, "%Y-%m-%d")
                        days = (d2 - d1).days
                        
                        if days > 0:
                            adg = (curr_w - prev_w) / days
                            adg_str = f"{adg*1000:+5.0f} g/day" if abs(adg) < 1.0 else f"{adg:+5.2f} kg/day"
                            st.write(f"⚖️ [{curr_date}] **{curr_w} kg** | Production Evaluation Rate: **{adg_str}** (Delta: {days} Days)")
                        else:
                            st.write(f"⚖️ [{curr_date}] **{curr_w} kg** [N/A Historical Duplicate Audit Entry]")

            st.markdown("---")
            
            # Historic Ledger Timeline Subsections
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("🌾 Nutritional Consumption History")
                cursor.execute("SELECT log_date, feed_type, quantity_kg FROM feed_logs WHERE tag_id = ? ORDER BY log_date DESC", (search_id,))
                feeds = cursor.fetchall()
                if feeds:
                    for f in feeds:
                        st.write(f"📅 *[{f[0]}]* Ration: **{f[1]}** | Quantity: **{f[2]} kg**")
                else:
                    st.caption("No formal custom nutritional disbursements indexed for this asset entry.")
            
            with c2:
                st.subheader("💉 Clinical Veterinary Intervention History")
                cursor.execute("SELECT treatment_date, treatment_type, product_name FROM health_logs WHERE tag_id = ? ORDER BY treatment_date DESC", (search_id,))
                health = cursor.fetchall()
                if health:
                    for h in health:
                        st.write(f"📅 *[{h[0]}]* Classification: **{h[1]}** | Remedy: **{h[2]}**")
                else:
                    st.caption("Clean Record: No veterinary treatment interventions logged against index.")
