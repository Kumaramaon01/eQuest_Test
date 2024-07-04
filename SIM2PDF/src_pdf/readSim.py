import os
import shutil
from fpdf import FPDF
from SIM2PDF.src_pdf import readSim
import PyPDF2
import streamlit as st
import glob as gb
from pathlib import Path
import fnmatch

# Reading SIM files line by line
def read_sim_file(sim_file_path):
    if os.path.isfile(sim_file_path):  # If the SIM file exists, then open it in read mode
        with open(sim_file_path, 'r', encoding='utf-8') as f:  # Function is used to specify the character encoding of the file being opened
            return f.read()
    else:
        print("SIM file does not exist.")
        return None

# Remove some redundant lines in the SIM file
def clean_sim(name):
    with open(name, 'r', encoding='utf-8') as file:
        lines = file.readlines()

        cleaned_lines = []
        i = 0
        while i < len(lines) - 1:  # Iterate until the second to last element
            # Check if "REPORT" is present in the current line and "RUN" in the next line
            if "REPORT" in lines[i] and "RUN" in lines[i + 1]:
                i += 2  # Skip both lines if both conditions are met
            elif "RUN" in lines[i]:
                i += 1
            else:
                cleaned_lines.append(lines[i])  # Otherwise, keep the current line
                i += 1  # Move to the next line

    # Join the cleaned lines into a single string
    return ''.join(cleaned_lines)

# Function to modify generated PDF and override in the same folder
def get_report_as_pdf(report_content, folder_name, path):
    # Create a PDF object
    pdf = FPDF()
    
    # Set font for the PDF
    pdf.set_font("Courier", size=6.5)

    # Add a page with increased horizontal width
    pdf.add_page(orientation='L')  # 'L' stands for landscape orientation
    pdf.set_auto_page_break(auto=True, margin=10)  # Setting automatic page break with a margin of 10

    # Split the report content by lines
    report_lines = report_content.strip().split('\n')

    # Add content from the SIM report, starting a new page for each section starting with "REPORT"
    for line in report_lines:
        if "RUN" in line:
            pdf.add_page()  # Start a new page
        pdf.multi_cell(0, 4, line)  # Adjust spacing to 4

    # Save the PDF to the specified file path
    temp_file = os.path.join(path, f'{folder_name}_temp.pdf')
    file_path = os.path.join(path, f'{folder_name}.pdf')
    pdf.output(temp_file)
    st.success("PDF report generated!")

    # Remove the first page using PyPDF2
    with open(temp_file, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        writer = PyPDF2.PdfWriter()
        for page_num in range(1, len(reader.pages)):
            writer.add_page(reader.pages[page_num])
        
        # Write to the final PDF file
        with open(file_path, 'wb') as output_file:
            writer.write(output_file)

    # Remove the temporary file
    os.remove(temp_file)

# Function to get PDF in the same directory where the generated SIM file is located
def generate_pdf(output_directory):
    simfiles = gb.glob(os.path.join(output_directory, '*.sim'))
    if simfiles:  # Check if simfiles list is not empty
        for sim_file in simfiles:
            folder_name = os.path.splitext(os.path.basename(sim_file))[0]
            parent_directory = os.path.dirname(sim_file)
            report_content = read_sim_file(sim_file)

            if report_content:
                print("\nGenerating PDF report...")
                get_report_as_pdf(report_content, folder_name, output_directory)
                print("PDF report generation complete.\n")
    else:
        print("No SIM files found in the specified directory.")

# Function to extract relevant data from the SIM file based on input reports
def extractReport(input_sim_files, reports):
    if not os.path.exists(input_sim_files):
        st.error(f"The directory {input_sim_files} does not exist.")
    else:
        # List all files in the directory and subdirectories
        simfiles = []
        for root, dirs, files in os.walk(input_sim_files):
            for filename in files:
                if fnmatch.fnmatch(filename, '*.sim'):
                    simfiles.append(os.path.join(root, filename))

        # Create "Report Outputs" folder inside the folder containing SIM files
        output_directory = os.path.join(input_sim_files, "Report Outputs")
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        else:
            shutil.rmtree(output_directory)
            os.makedirs(output_directory)

        # Process each SIM file
        for name in simfiles:
            with open(name) as f:
                f_list = f.readlines()
                for num, line in enumerate(f_list):
                    for r in reports:
                        if r in line:
                            rptstart = num - 2
                            lines = 0
                            for line in f_list[rptstart + 3:]:
                                if "REPORT" in line:
                                    rptlen = lines
                                    break
                                lines += 1
                            section = f_list[rptstart:rptstart + rptlen + 4]
                            file_name = "Reports_" + os.path.basename(name)
                            with open(os.path.join(output_directory, file_name), "a") as output:
                                for l in section:
                                    output.write(l)
                            break

        # Clean generated SIM files in "Report Outputs" folder
        for filename in os.listdir(output_directory):
            file_path = os.path.join(output_directory, filename)
            cleaned_content = clean_sim(file_path)  # Call your clean_sim function here
            
            # Convert cleaned_content to string if it's a list
            if isinstance(cleaned_content, list):
                cleaned_content = "\n".join(cleaned_content)
            
            # Write the cleaned content back to the file
            with open(file_path, "w") as cleaned_file:
                cleaned_file.write(cleaned_content)

        # Generate PDF reports from the cleaned SIM files in "Report Outputs" folder
        generate_pdf(output_directory)
        return "Extraction and PDF generation completed successfully."
