import streamlit as st
import pandas as pd
import os

# --- Load Data from CSV File ---
# IMPORTANT: Uses semicolon (';') as delimiter and skips 6 rows before the header.
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
    
    # 1. Drop rows where 'Course' is entirely missing (NaN)
    df.dropna(subset=['Course'], inplace=True)

    # 2. Clean and standardize 'Code' column:
    #    a. Convert to numeric, coercing errors to NaN (e.g., "abc" -> NaN)
    #    b. Drop rows where 'Code' couldn't be converted to a number (NaNs)
    #    c. Convert to integer (removes the .0, e.g., 34.0 -> 34)
    #    d. Convert to string (e.g., 34 -> "34") and strip any whitespace
    df['Code'] = pd.to_numeric(df['Code'], errors='coerce')
    df.dropna(subset=['Code'], inplace=True) # Drop rows where Code is NaN after numeric conversion
    df['Code'] = df['Code'].astype(int).astype(str).str.strip() 

    # Filter out rows where 'Code' explicitly became the string 'nan' (already covered by dropna)
    df = df[df['Code'].str.lower() != 'nan']
    df = df[df['Code'] != ''] # Also filter out genuinely empty strings if any exist
    
    # The 'Incompatibilities' column often contains comma-separated values.
    # We ensure it's treated as string and then split it into a list of individual codes.
    df['Incompatibilities'] = df['Incompatibilities'].fillna('').astype(str)
    df['Incompatible_List'] = df['Incompatibilities'].apply(
        lambda x: [i.strip() for i in x.split(',') if i.strip() and i.strip() != '200F']
    )
    df['Decision'] = 'No' # Default decision for each course

    # Optional: Print info to console for debugging if needed (won't show in Streamlit app directly)
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

# --- Streamlit App Layout and Logic ---

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

# --- Debugging Info (for you to copy) ---
# You can remove this section once the app is working as expected.
st.subheader("--- DEBUGGING INFO ---")
st.write("1. Selected Courses (Codes):", selected_codes)

# Find all incompatible course codes based on current selections
incompatible_all = set()
for code in selected_codes:
    course_row = df[df['Code'] == code]
    if not course_row.empty:
        incompat_list_for_selected = course_row.iloc[0]['Incompatible_List']
        st.write(f"2. Incompatibilities for selected course '{code}':", incompat_list_for_selected)
        incompatible_all.update(incompat_list_for_selected)

st.write("3. All Incompatible Codes (incompatible_all set):", incompatible_all)
st.subheader("--------------------")
# --- End Debugging Info ---


# Display a warning if the course selection limit is reached
if len(selected_codes) >= 5:
    st.warning("⚠️ You have selected 5 courses. Deselect one to add others.")

# Show the course table
st.markdown("### 📋 Course List")
for idx, row in df.iterrows():
    code = str(row['Code']) # This `str()` conversion here is redundant if Code is already string, but harmless.
    name = row['Course']
    is_selected = st.session_state.selections.get(code) == 'Yes'
    is_disabled = False
    reason = ""

    # Logic to disable (grey out) incompatible or limit-reached courses
    if code in incompatible_all and not is_selected:
        is_disabled = True
        reason = "❌ Incompatible with selected courses"

    if len(selected_codes) >= 5 and not is_selected:
        is_disabled = True
        reason = "⚠️ Limit reached"

    # Create two columns for each course entry: one for course details, one for the selectbox
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"**{name}** (Code: `{code}`)")
    with col2:
        option = st.selectbox(
            label="", # Label is empty as the name is in col1
            options=["No", "Yes"],
            index=1 if is_selected else 0, # Set default based on session state
            key=f"decision_{code}", # Unique key for each selectbox (important for Streamlit)
            disabled=is_disabled, # Disable based on logic
            help=reason # Tooltip for disabled options
        )
        st.session_state.selections[code] = option # Update session state with user's selection

# Final course selection summary
final_selected_codes = [c for c, v in st.session_state.selections.items() if v == 'Yes']
final_selected_names = [df[df['Code'] == c].iloc[0]['Course'] for c in final_selected_codes]

st.markdown("---")
st.subheader("✅ Selected Courses:")
if final_selected_names:
    for name in final_selected_names:
        st.write(f"• {name}")
else:
    st.write("No courses selected.")

# Show incompatible courses in a message box (not the greying out)
st.markdown("### 🚫 Incompatible Courses:")
if final_selected_codes:
    incompatible_names = set()
    for code in final_selected_codes:
        row = df[df['Code'] == code].iloc[0] # Get the row for the selected course
        incompatible_codes = row['Incompatible_List']
        for inc in incompatible_codes:
            # Only list incompatibilities that are NOT among the currently selected courses
            # And ensure the incompatible code exists in the DataFrame's 'Code' column
            course_name_series = df[df['Code'] == inc]['Course']
            if not course_name_series.empty and inc not in final_selected_codes:
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
