import inspect
import os
import pandas as pd
import streamlit as st
from mitosheet.streamlit.v1 import spreadsheet

st.set_page_config(layout='wide')
st.title("Recon Demo App")

# This is an app that lets users:
# 1. Upload a file
# 2. Create a recon script using the mitosheet
# 3. Run the recon script on new data

create_tab, consume_tab = st.tabs(["Create Recon Script", "Run Recon Script"])

def get_code_to_write(description, code):
    return f"""\"\"\"
{description}
\"\"\"

{code}
"""

with create_tab:
    st.write("Create Recon Script")

    # Get a name and description for the recon
    name = st.text_input("Name")
    description = st.text_area("Description")

    file = st.file_uploader("Upload a file", type=["csv"])

    if file:
        
        # Write the file to disk
        df = pd.read_csv(file)
        _, code = spreadsheet(df, df_names=["df"])

        st.code(code)

        # Add button to save script
        save = st.button("Save Script")
        if save:

            recon_folder = "./recon"
            recon_path = f'./recon/{name}.py'

            if not os.path.exists(recon_folder):
                os.mkdir(recon_folder)

            # Write the file
            with open(recon_path, "w") as f:
                f.write(get_code_to_write(description, code))

            st.success(f"Saved recon script to {recon_path}")

with consume_tab:
    st.write("Run Recon Script")

    # Let users select a recon script, from the recon folder
    recon_folder = "./recon"
    recon_scripts = os.listdir(recon_folder)
    recon_script = st.selectbox("Select a recon script", recon_scripts)

    # Load the script
    with open(f"{recon_folder}/{recon_script}", "r") as f:
        code = f.read()

    
    # Read in the new file to run the recon on
    file = st.file_uploader("Upload a new file", type=["csv"])
    if file:
        # Write the file to disk
        with open("new_file.csv", "wb") as f:
            f.write(file.read())

        
    # Append the code to read in the current file
    code = f"""import pandas as pd
df = pd.read_csv('new_file.csv')
{code}
"""

    st.code(code)

    # Exec the code and get any defined functions from it
    exec(code)
    functions = [f for f in locals().values() if callable(f)]
    new_functions = []
    for f in functions:
        # Filter them out if they are from mitosheet
        if "mitosheet" not in str(inspect.getmodule(f)):
            new_functions.append(f)
    
    st.write(new_functions)

    


    df = pd.read_csv(file)




