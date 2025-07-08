import streamlit as st
import pandas as pd
import os

# --- Load Data from CSV File ---
# IMPORTANT: Use sep=';' and skiprows=6 to correctly load the header
try:
    # Adding skiprows=6 based on file metadata that indicates 6 rows above the header
    df = pd.read_csv('All_Courses.csv', sep=';', skiprows=6) 
    
    # --- Data Cleaning and Preparation ---
    # Rename 'Course Name' to 'Course' for consistency with the rest of the app logic
    if 'Course Name' in df.columns:
        df.rename(columns={'Course Name': 'Course'}, inplace=True)
    elif 'Course' not in df.columns:
        st.error("Error: Neither 'Course Name' nor 'Course' column found in the CSV. Please ensure your CSV has a 'Course Name' column.")
        st.stop()
    
    # 1. Drop rows where 'Code' or 'Course' is entirely missing (NaN)
    # This prevents 'nan (code:nan)' issues and helps with duplicate keys.
    df.dropna(subset=['Code', 'Course'], inplace=True)

    # 2. Convert 'Code' to string and strip any whitespace
    df['Code'] = df['Code'].astype(str).str.strip()

    # 3. Filter out rows where 'Code' explicitly became the string 'nan' after conversion
    # or if it's empty after stripping.
    df = df[df['Code'].str.lower() != 'nan']
    df = df[df['Code'] != ''] # Also filter out genuinely empty strings if any exist

    # Optional: If 'Code' must be purely numeric (e.g., '1', '2', but not '200F' in Code column itself)
    # df = df[df['Code'].apply(lambda x: x.isdigit())]

    # Ensure 'Incompatibilities' is string and handle the list parsing
    df['Incompatibilities'] = df['Incompatibilities'].fillna('').astype(str)
    df['Incompatible_List'] = df['Incompatibilities'].apply(
        lambda x: [i.strip() for i in x.split(',') if i.strip() and i.strip() != '200F']
    )
    df['Decision'] = 'No' # Default decision for each course

    # Optional: Print info to console for debugging if needed (won't show in Streamlit app)
    print("DataFrame head after loading and cleaning:")
    print(df.head())
    print("\nDataFrame info after loading and cleaning:")
    print(df.info())

except FileNotFoundError:
    st.error("Error: 'All_Courses.csv' not found. Please ensure the file is named 'All_Courses.csv' and is in the same directory as this script.")
    st.stop()
except KeyError as e:
    # Specifically catch KeyError for missing columns
    st.error(f"Error loading CSV file: Column '{e}' not found after loading. Please check your CSV header and ensure it contains 'Code' and 'Course Name' (or 'Course').")
    st.stop()
except Exception as e:
    st.error(f"Error loading CSV file: {e}. This often means the file format or delimiter is incorrect. Please check your CSV file's content and maybe try opening it in a text editor to confirm structure and delimiter (semicolon).")
    st.stop()

# --- Rest of your Streamlit app code (no changes needed below this point) ---

st.set_page_config(layout="wide")
st.title("🎓 Interactive Course Selection Tool")
st.markdown("Choose up to **5 courses**. Incompatible options will be grayed out but still visible below.")

# Track session state to persist selections across reruns
if 'selections' not in st.session_state:
    st.session_state.selections = {}

# Get currently selected course codes
selected_codes = [
    code for code, decision in st.session_state.selections.items() if decision == 'Yes'
]

# Determine all courses that are incompatible with any of the selected courses
incompatible_all = set()
for code in selected_codes:
    course_row = df[df['Code'] == code] # Compare string codes
    if not course_row.empty:
        incompatible_all.update(course_row.iloc[0]['Incompatible_List'])

# Display a warning if the course selection limit is reached
if len(selected_codes) >= 5:
    st.warning("⚠️ You have selected 5 courses. Deselect one to add others.")

# Display the course list with selection options
st.markdown("### 📋 Course List")
for idx, row in df.iterrows():
    code = str(row['Code'])
    name = row['Course']
    is_selected = st.session_state.selections.get(code) == 'Yes'
    is_disabled = False
    reason = ""

    # Disable if incompatible with existing selections and not already selected
    if code in incompatible_all and not is_selected:
        is_disabled = True
        reason = "❌ Incompatible with selected courses"

    # Disable if limit reached and not already selected
    if len(selected_codes) >= 5 and not is_selected:
        is_disabled = True
        reason = "⚠️ Limit reached"

    # Create columns for layout: Course Name and Selectbox
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"**{name}** (Code: `{code}`)")
    with col2:
        option = st.selectbox(
            label="", # Label is empty as the name is in col1
            options=["No", "Yes"],
            index=1 if is_selected else 0, # Set default based on session state
            key=f"decision_{code}", # Unique key for each selectbox
            disabled=is_disabled, # Disable based on logic
            help=reason # Tooltip for disabled options
        )
        st.session_state.selections[code] = option # Update session state

# Display final selected courses
final_selected_codes = [c for c, v in st.session_state.selections.items() if v == 'Yes']
final_selected_names = [df[df['Code'] == c].iloc[0]['Course'] for c in final_selected_codes]

st.markdown("---")
st.subheader("✅ Selected Courses:")
if final_selected_names:
    for name in final_selected_names:
        st.write(f"• {name}")
else:
    st.write("No courses selected.")

# Display incompatible courses
st.markdown("### 🚫 Incompatible Courses:")
if final_selected_codes:
    incompatible_names = set()
    for code in final_selected_codes:
        row = df[df['Code'] == code].iloc[0] # Get the row for the selected course
        incompatible_codes = row['Incompatible_List']
        for inc in incompatible_codes:
            # Only list incompatibilities that are NOT among the currently selected courses
            if inc not in final_selected_codes:
                course_name_series = df[df['Code'] == inc]['Course']
                if not course_name_series.empty:
                    incompatible_names.add(course_name_series.iloc[0])

    if incompatible_names:
        st.error("The following courses are **not compatible** with your current selection:")
        for name in sorted(incompatible_names):
            st.markdown(f"• {name}")
    else:
        st.success("No conflicts! 🎉 All selected courses are compatible.")
else:
    st.info("Select courses to see incompatibility information.")

# Instructions for users
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
