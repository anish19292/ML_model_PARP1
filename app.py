import streamlit as st
import os
import pickle
import pandas as pd
from PIL import Image
from rdkit import Chem
from rdkit.Chem import AllChem, Draw
from padelpy import padeldescriptor

# Page configuration
st.set_page_config(
  page_title='PARP-1 activity predictor',
  page_icon='💊',
  initial_sidebar_state='expanded')

# Load your banner image
banner_image_path ='Banner.png'
banner_image = Image.open(banner_image_path)

# Set the desired width for the banner image
banner_image_width = 800  # Adjust this value as needed

# Display the banner image with a fixed width
st.image(banner_image, width=banner_image_width)

# Session state
if 'smiles_input' not in st.session_state:
  st.session_state.smiles_input = ''

# Utilities
if os.path.isfile('molecule.smi'):
  os.remove('molecule.smi') 

# The App    
st.info('This GUI allow users to predict whether a query molecule is likely to be active/inactive towards the PARP-1 enzyme.')

tab1,tab2,tab3,tab4 = st.tabs(['GUI', 'Dataset and Model Performance', 'Contact', 'Acknowledgements'])


with tab1:
    with st.form('my_form'):
        st.subheader('Predict PARP1 inhibitory activity')

        smiles_txt = st.text_input('Enter SMILES notation', st.session_state.smiles_input)
        st.session_state.smiles_input = smiles_txt

        with st.expander('Example SMILES'):
            st.code('C1CC1C(=O)N2CCN(CC2)C(=O)C3=C(C=CC(=C3)CC4=NNC(=O)C5=CC=CC=C54)F')
            st.code('COc1ccc2c(c1)nc([nH]2)S(=O)Cc1ncc(c(c1C)OC)C')

        submit_button = st.form_submit_button('Submit')

    # Display input molecule info regardless of condition
    st.subheader('⚛️ Input molecule:')
    with st.expander('Show SMILES', expanded=True):
        st.text(st.session_state.smiles_input)

    with st.expander('Show chemical structures', expanded=True):
        smi = Chem.MolFromSmiles(st.session_state.smiles_input)
        Chem.Draw.MolToFile(smi, 'molecule.png', width=900)
        mol_image = Image.open('molecule.png')
        st.image(mol_image)

    # Input SMILES saved to file
    f = open('molecule.smi', 'w')
    f.write(f'{st.session_state.smiles_input}\tmol_001')
    f.close()
	  
	   # Compute PADEL descriptors
    if st.session_state.smiles_input != '':
            st.subheader('🔢 Descriptors')
            if os.path.isfile('molecule.smi'):
                padeldescriptor(mol_dir='molecule.smi', 
                                d_file='descriptors.csv',
                                descriptortypes='PubchemFingerprinter.xml', 
                                detectaromaticity=True,
                                standardizenitro=True,
                                standardizetautomers=True,
                                threads=2,
                                removesalt=True,
                                log=True,
                                fingerprints=True,
                                d_2d=True)

            descriptors = pd.read_csv('descriptors.csv')
            descriptors.drop('Name', axis=1, inplace=True)

            with st.expander('Show full set of descriptors as calculated for query molecule'):
                st.write(descriptors)
                st.write(descriptors.shape)

            # Load the model and feat_names
            model_data = pickle.load(open('classifier_1.pkl', 'rb'))
            loaded_classifier = model_data['classifier']
            loaded_feat_names = model_data['feat_names']

            query_desc_1 = descriptors.columns.difference(loaded_feat_names)
            query_desc_2 = descriptors.drop(query_desc_1, axis=1)

            # Scale the descriptors using Z-score normalization
            mean_std_data = {
                'SsssN': {'mean': 2.09, 'std': 1.87},
                'MAXDN': {'mean': 2.28, 'std': 0.96},
                'DELS': {'mean': 35.08, 'std': 15.83}
            }

            scaled_desc_1 = (query_desc_2['SsssN'] - mean_std_data['SsssN']['mean']) / mean_std_data['SsssN']['std']
            scaled_desc_2 = (query_desc_2['MAXDN'] - mean_std_data['MAXDN']['mean']) / mean_std_data['MAXDN']['std']
            scaled_desc_3 = (query_desc_2['DELS'] - mean_std_data['DELS']['mean']) / mean_std_data['DELS']['std']

            scaled_query_desc = pd.DataFrame({'SsssN': scaled_desc_1, 'MAXDN': scaled_desc_2, 'DELS': scaled_desc_3})

            with st.expander('Show scaled descriptors as used in trained model'):
                st.write(scaled_query_desc)
                st.write(scaled_query_desc.shape)

            # Read in saved classification model
            st.subheader('Predictions')
            pred_array = loaded_classifier.predict(scaled_query_desc)
            pred = int(pred_array[0])  # Extract the single element from the array

            if pred == 1:
                st.error('This compound is expected to be PARP-1 inactive.')
            if pred == 0:
                st.success('This compound is expected to be PARP-1 active.')

with tab2:
    st.header('Dataset')
    st.write('This model is built using 4298 compounds with PARP-1 activity data curated from the ChEMBL and PubChem databases. The dataset was binarized based on a cut-off of <1 μM for actives and ≥ 1 μM for inactives and balanced using SMOTE.')
    
    st.header('Model Performance')
    st.write('This model has accuracy 0.86, sensitivity 0.88, specificity 0.80 and compares favorably to reported models.')

with tab3:
    st.header('Contact')
    st.subheader('Developers:')
    st.write('1. Dr. Anish Gomatam (RA-III, Dept. of Medicinal Chemistry)')
    st.write('2. Ms. Bhakti Hirlekar (Ph.D. scholar, Dept. of Medicinal Chemistry)')

    st.subheader('Principal Investigator:')
    st.write('Dr. Vaibhav A. Dixit')
    st.write('Assistant Professor, Department of Medicinal Chemistry')
    
    st.subheader('Project coordinator:')
    st.write('Dr. USN Murty')
    st.write('Director, NIPER Guwahati')

    st.subheader('Contact Us')
    st.write("In case you have any queries, please feel free to reach out to us:")

    # Display email input field and message box
    user_email = st.text_input("Your Email:")
    user_query = st.text_area("Your Query:")

with tab4:
	st.header('Funding')
	st.write('This project has been sponsored by the Ministry of Electronics and Information Technology, Government of India (project reference number No(4)12/2021-ITEA).')
	st.write("A manuscript entitled 'Medicinal chemistry insights and improved models for PARP-1 activity prediction using data balancing, interpretable machine learning and matched molecular pair analysis' is under review.")
