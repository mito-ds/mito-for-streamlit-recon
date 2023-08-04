import inspect
import os
import pandas as pd
import streamlit as st
from mitosheet.streamlit.v1 import spreadsheet

st.set_page_config(layout='wide')
st.title("Data Automation Demo App")

st.markdown("""
This application shows how Mito Enterprise can help non-technical users automate a process using Mito, 
without needing to know any Python code. See instructions below.
            
#### App Limitaitons
1.  This application only supports a single dataframe as input / output. Ensure you never
    have more than one tab in your spreadsheet.
2.  The data format of original data, as well as the data the automation is being rerun
    on must be the same.
""")

FOLDER = './automation'

# This is an app that lets users:
# 1. Upload a file
# 2. Create a automation script using the mitosheet
# 3. Run the automation script on new data

create_tab, consume_tab = st.tabs(["Create Automation Script", "Run Automation Script"])

def get_code_to_write(description, code):
    return f"""\"\"\"
{description}
\"\"\"

{code}
"""    

with create_tab:
    st.markdown("""
## Creating a Data Automation
            
1. Give a Name and Description for the process you are automating. 
2. Upload a file that is the start of your data automation.
3. Use Mito to add new columns, filter, and transform your data into a final state.
4. Open **Code > Configure Code** and turn Generate Function to True.
4. Click the save button at the bottom, and then switch to the Run Automation Script tab.
""")

    # Get a name and description for the automation
    name = st.text_input("Name")
    description = st.text_area("Description")

    file = st.file_uploader("Upload a file", type=["csv"])

    if file:
        
        df = pd.read_csv(file)
        new_dfs, code = spreadsheet(df, df_names=["df"])

        if len(new_dfs) > 1:
            st.error("Please ensure there is only one tab in your sheet. This demo application only supports single-tab automations.")

        st.code(code)

        # Add button to save script
        save = st.button("Save Script")
        if save:

            automation_path = f'{FOLDER}/{name}'
            check_path = f'{automation_path}/check.py'
            data_path = f'{automation_path}/data.csv'

            if not os.path.exists(FOLDER):
                os.mkdir(FOLDER)
            if not os.path.exists(automation_path):
                os.mkdir(automation_path)

            # Write the file
            with open(check_path, "w") as f:
                f.write(get_code_to_write(description, code))
            # Write the data
            df.to_csv(data_path, index=False)

            st.success(f"Saved automation script to {automation_path}")

with consume_tab:
    st.markdown("""
## Consuming a Data Automation
1. Switch to the Run Automation Script tab.
2. Select an automation you want to run. 
3. Upload a dataset that contains new data in the _same format_ as the original data.
4. Watch the automation run on your new dataset!
""")

    # Let users select a automation script, from the automation folder
    automation_scripts = [None] + (os.listdir(FOLDER) if os.path.exists(FOLDER) else [])
    automation_script = st.selectbox("Select a automation script", automation_scripts)

    if automation_script is None:
        st.error('Select a saved automation script to run the automation.')
        st.stop()

    # Load the script
    with open(f"{FOLDER}/{automation_script}/check.py", "r") as f:
        code = f.read()

    # Chop off the final line
    code = "\n".join(code.split("\n")[:-2])

    # Show the description of the automation, which is the doc-string at the top of code
    description = code[3:code[3:].index('"""') + 3]
    st.text(description)
    
    # Exec the code and get any defined functions from it
    functions_before = [f for f in locals().values() if callable(f)]
    exec(code)
    functions = [f for f in locals().values() if callable(f) and f not in functions_before]
    new_functions = []
    for f in functions:
        # Filter them out if they are from mitosheet
        if "mitosheet" not in str(inspect.getmodule(f)) :
            new_functions.append(f)

    if len(new_functions) != 1:
        st.error('Please make sure the defined Python script has just one functiond defined in it.')       
        st.stop()

    automation_function = new_functions[0]
    # Read in the new file to run the automation on
    file = st.file_uploader("Upload a new file to run the automation on.", type=["csv"])

    # Run the automation function on the new file
    if file:
        df = pd.read_csv(file)
        automation_df = automation_function(df)

        # Allow users to download this new dataframe

        st.success("Finished automation.")

        @st.cache_data
        def convert_df(df):
            # IMPORTANT: Cache the conversion to prevent computation on every rerun
            return df.to_csv().encode('utf-8')

        csv = convert_df(automation_df)
        st.download_button(
            label="Download final automation as CSV",
            data=csv,
            file_name='automation.csv',
            mime='text/csv',
        )







