import os
import zipfile
import shutil

# --- Configuration ---

# The folder where your .zip files are located
SOURCE_DIR = "datasets/dimacs-zip-files"

# The folder where you want the .mtx files to go
TARGET_DIR = "datasets/dimacs"

# ---------------------

def extract_mtx_files():
    """
    Finds all .zip files in SOURCE_DIR, opens them,
    and extracts only the .mtx file to TARGET_DIR.
    """
    
    print(f"--- Starting MTX File Extractor ---")
    
    # 1. Create the target directory if it doesn't exist
    if not os.path.exists(TARGET_DIR):
        print(f"Creating directory: {TARGET_DIR}")
        os.makedirs(TARGET_DIR)
    else:
        print(f"Target directory '{TARGET_DIR}' already exists.")

    # Check if the source directory exists
    if not os.path.exists(SOURCE_DIR):
        print(f"Error: Source directory '{SOURCE_DIR}' not found.")
        print("Please run the download script first.")
        return

    print(f"\nScanning '{SOURCE_DIR}' for .zip files...")
    
    extracted_count = 0
    skipped_count = 0
    
    # 2. Loop through every file in the source directory
    for file_name in os.listdir(SOURCE_DIR):
        if file_name.endswith(".zip"):
            zip_path = os.path.join(SOURCE_DIR, file_name)
            
            try:
                # 3. Open the zip file
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    # 4. Find the .mtx file(s) inside
                    mtx_files_in_zip = [name for name in zf.namelist() if name.endswith(".mtx")]
                    
                    if not mtx_files_in_zip:
                        print(f"- Warning: No .mtx file found in {file_name}")
                        continue

                    for mtx_name in mtx_files_in_zip:
                        # Get just the filename (e.g., "brock200-1.mtx")
                        target_filename = os.path.basename(mtx_name)
                        target_path = os.path.join(TARGET_DIR, target_filename)

                        # 5. Check if the .mtx file already exists
                        if os.path.exists(target_path):
                            print(f"- Skipping {target_filename} (already exists)")
                            skipped_count += 1
                            continue

                        # 6. Extract the file
                        # This method avoids creating extra subfolders
                        print(f"- Extracting {target_filename} from {file_name}...")
                        with zf.open(mtx_name) as source_file:
                            with open(target_path, 'wb') as target_file:
                                shutil.copyfileobj(source_file, target_file)
                        extracted_count += 1
                        
            except zipfile.BadZipFile:
                print(f"- Error: Could not open {file_name}. It may be corrupt.")
            except Exception as e:
                print(f"- An unexpected error occurred with {file_name}: {e}")

    print("\n--- Extraction Complete ---")
    print(f"Extracted: {extracted_count} new .mtx files")
    print(f"Skipped:   {skipped_count} existing files")
    print(f"All .mtx files are in: {TARGET_DIR}")

if __name__ == "__main__":
    extract_mtx_files()