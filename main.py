import streamlit as st
import pandas as pd
import os

# --- Load Data from CSV File ---
# Assuming 'All_Courses.csv' is in the same directory as this script (main.py).
try:
    df = pd.read_csv('All_Courses.csv') # Changed filename here
    # Ensure 'Code' column is treated as strings for consistency with comparisons later
    df['Code'] = df['Code'].astype(str)
except FileNotFoundError:
    st.error("Error: 'All_Courses.csv' not found. Please make sure the CSV file is in the same directory as the script.")
    st.stop() # Stop the app if the file isn't found
except Exception as e:
    st.error(f"Error loading CSV file: {e}")
    st.stop() # Stop the app if there's another error during loading

# --- End of Data Loading ---

# Prepare data (same as your original code, adapted for new column names if needed)
# Ensure your CSV has 'Code', 'Course Name', 'Professor', 'Sessions', 'Incompatibilities'
# We'll map 'Course Name' to 'Course' for compatibility with the rest of the code.
df.rename(columns={'Course Name': 'Course'}, inplace=True)


df['Incompatibilities'] = df['Incompatibilities'].fillna('').astype(str)
df['Incompatible_List'] = df['Incompatibilities'].apply(
    lambda x: [i.strip() for i in x.split(',') if i.strip() and i.strip() != '200F']
)
df['Decision'] = 'No'  # Default

st.set_page_config(layout="wide")
st.title("🎓 Interactive Course Selection Tool")
st.markdown("Choose up to **5 courses**. Incompatible options will be grayed out but still visible below.")

# Track session state
if 'selections' not in st.session_state:
    st.session_state.selections = {}

selected_codes = [
    code for code, decision in st.session_state.selections.items() if decision == 'Yes'
]

# Find all incompatible course codes
incompatible_all = set()
for code in selected_codes:
    course_row = df[df['Code'] == code] # Compare string codes
    if not course_row.empty:
        incompatible_all.update(course_row.iloc[0]['Incompatible_List'])

# Count limit warning
if len(selected_codes) >= 5:
    st.warning("⚠️ You have selected 5 courses. Deselect one to add others.")

# Show the course table
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
        st.markdown(f"**{name}** (Code: `{code}`)")
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

# Final course selection
final_selected_codes = [c for c, v in st.session_state.selections.items() if v == 'Yes']
final_selected_names = [df[df['Code'] == c].iloc[0]['Course'] for c in final_selected_codes] # Compare string codes

st.markdown("---")
st.subheader("✅ Selected Courses:")
if final_selected_names:
    for name in final_selected_names:
        st.write(f"• {name}")
else:
    st.write("No courses selected.")

# Show incompatible courses in a message box
st.markdown("### 🚫 Incompatible Courses:")
if final_selected_codes:
    incompatible_names = set()
    for code in final_selected_codes:
        row = df[df['Code'] == code].iloc[0] # Compare string codes
        incompatible_codes = row['Incompatible_List']
        for inc in incompatible_codes:
            if inc not in final_selected_codes:
                course_name = df[df['Code'] == inc]['Course'].values # Compare string codes
                if len(course_name) > 0:
                    incompatible_names.add(course_name[0])

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
