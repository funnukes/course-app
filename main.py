import streamlit as st
import pandas as pd
import os

# --- Load Data from CSV File ---
try:
    df = pd.read_csv('All_Courses.csv', sep=';', skiprows=6) 
    
    # --- Data Cleaning and Preparation ---
    if 'Course Name' in df.columns:
        df.rename(columns={'Course Name': 'Course'}, inplace=True)
    elif 'Course' not in df.columns:
        st.error("Error: Neither 'Course Name' nor 'Course' column found in the CSV. Please ensure your CSV has a 'Course Name' column.")
        st.stop()
    
    df.dropna(subset=['Course'], inplace=True)
    df['Code'] = pd.to_numeric(df['Code'], errors='coerce')
    df.dropna(subset=['Code'], inplace=True) 
    df['Code'] = df['Code'].astype(int).astype(str).str.strip() 

    df = df[df['Code'].str.lower() != 'nan']
    df = df[df['Code'] != ''] 
    
    df['Incompatibilities'] = df['Incompatibilities'].fillna('').astype(str)
    df['Incompatible_List'] = df['Incompatibilities'].apply(
        lambda x: [i.strip() for i in x.split(',') if i.strip() and i.strip() != '200F']
    )
    df['Decision'] = 'No' 

    print("DataFrame head after loading and cleaning:")
    print(df.head())
    print("\nDataFrame info after loading and cleaning:")
    print(df.info())

except FileNotFoundError:
    st.error("Error: 'All_Courses.csv' not found. Please ensure the file is named 'All_Courses.csv' and is in the same directory as this script.")
    st.stop()
except KeyError as e:
    st.error(f"Error loading CSV file: Column '{e}' not found after loading. Please check your CSV header and ensure it contains 'Code' and 'Course Name' (or 'Course').")
    st.stop()
except Exception as e:
    st.error(f"Error loading CSV file: {e}. This often means the file format or delimiter is incorrect. Please check your CSV file's content and maybe try opening it in a text editor to confirm structure and delimiter (semicolon).")
    st.stop()

# --- Streamlit App Layout and Logic ---

st.set_page_config(layout="wide")
st.title("🎓 Interactive Course Selection Tool")
st.markdown("Choose up to **5 courses**. Incompatible options will be grayed out but still visible below.")

if 'selections' not in st.session_state:
    st.session_state.selections = {}

selected_codes = [
    code for code, decision in st.session_state.selections.items() if decision == 'Yes'
]

incompatible_all = set()
for code in selected_codes:
    course_row = df[df['Code'] == code]
    if not course_row.empty:
        incompat_list_for_selected = course_row.iloc[0]['Incompatible_List']
        incompatible_all.update(incompat_list_for_selected)

if len(selected_codes) >= 5:
    st.warning("⚠️ You have selected 5 courses. Deselect one to add others.")

st.markdown("### 📋 Course List")
for idx, row in df.iterrows():
    code = str(row['Code']) 
    name = row['Course']
    is_selected = st.session_state.selections.get(code) == 'Yes'
    is_disabled = False
    reason = ""

    if code in incompatible_all and not is_selected:
        is_disabled = True
        reason = "❌ Incompatible with selected courses"

    if len(selected_codes) >= 5 and not is_selected:
        is_disabled = True
        reason = "⚠️ Limit reached"

    col1, col2 = st.columns([4, 1])
    with col1:
        # Added two empty writes to push the course name down further for better alignment
        col1.write("") 
        col1.write("") 
        col1.write(f"**{name}** (Code: `{code}`)")
    with col2:
        option = st.selectbox(
            label="", 
            options=["No", "Yes"],
            index=1 if is_selected else 0, 
            key=f"decision_{code}", 
            disabled=is_disabled, 
            help=reason 
        )
        st.session_state.selections[code] = option 

final_selected_codes = [c for c, v in st.session_state.selections.items() if v == 'Yes']
final_selected_names = [df[df['Code'] == c].iloc[0]['Course'] for c in final_selected_codes]

st.markdown("---")
st.subheader("✅ Selected Courses:")
if final_selected_names:
    for name in final_selected_names:
        st.write(f"• {name}")
else:
    st.write("No courses selected.")

st.markdown("### 🚫 Incompatible Courses:")
if final_selected_codes:
    incompatible_names = set()
    for code in final_selected_codes:
        row = df[df['Code'] == code].iloc[0] 
        incompatible_codes = row['Incompatible_List']
        for inc in incompatible_codes:
            if not df[df['Code'] == inc]['Course'].empty and inc not in final_selected_codes:
                incompatible_names.add(df[df['Code'] == inc]['Course'].iloc[0])

    if incompatible_names:
        st.error("The following courses are **not compatible** with your current selection:")
        for name in sorted(incompatible_names):
            st.markdown(f"• {name}")
    else:
        st.success("No conflicts! 🎉 All selected courses are compatible.")
else:
    st.info("Select courses to see incompatibility information.")

st.markdown("---")
st.markdown("### 📝 Instructions:")
st.markdown("""
1. **Select up to 5 courses** from the list above.
2. **Incompatible courses** will be automatically disabled when you make selections.
3. **View your final selection** in the summary above.
4. **Check compatibility** in the incompatible courses section.
""")

st.markdown("### 🚀 Deployment:")
st.markdown("To run this app locally: `pip install streamlit pandas` and then `streamlit run main.py`")
