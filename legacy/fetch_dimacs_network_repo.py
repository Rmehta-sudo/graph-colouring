import os
import requests

# --- Configuration ---

# The CORRECTED list of all .zip files to download
URL_LIST = [
    "https://nrvis.com/download/data/dimacs/C1000-9.zip",
    "https://nrvis.com/download/data/dimacs/C125-9.zip",
    "https://nrvis.com/download/data/dimacs/C2000-5.zip",
    "https://nrvis.com/download/data/dimacs/C2000-9.zip",
    "https://nrvis.com/download/data/dimacs/C250-9.zip",
    "https://nrvis.com/download/data/dimacs/C4000-5.zip",
    "https://nrvis.com/download/data/dimacs/C500-9.zip",
    "https://nrvis.com/download/data/dimacs/DSJC1000-5.zip",
    "https://nrvis.com/download/data/dimacs/DSJC500-5.zip",
    "https://nrvis.com/download/data/dimacs/MANN-a27.zip",
    "https://nrvis.com/download/data/dimacs/MANN-a45.zip",
    "https://nrvis.com/download/data/dimacs/MANN-a81.zip",
    "https://nrvis.com/download/data/dimacs/MANN-a9.zip",
    "https://nrvis.com/download/data/dimacs/brock200-1.zip",
    "https://nrvis.com/download/data/dimacs/brock200-2.zip",
    "https://nrvis.com/download/data/dimacs/brock200-3.zip",
    "https://nrvis.com/download/data/dimacs/brock200-4.zip",
    "https://nrvis.com/download/data/dimacs/brock400-1.zip",
    "https://nrvis.com/download/data/dimacs/brock400-2.zip",
    "https://nrvis.com/download/data/dimacs/brock400-3.zip",
    "https://nrvis.com/download/data/dimacs/brock400-4.zip",
    "https://nrvis.com/download/data/dimacs/brock800-1.zip",
    "https://nrvis.com/download/data/dimacs/brock800-2.zip",
    "https://nrvis.com/download/data/dimacs/brock800-3.zip",
    "https://nrvis.com/download/data/dimacs/brock800-4.zip",
    "https://nrvis.com/download/data/dimacs/c-fat200-1.zip",
    "https://nrvis.com/download/data/dimacs/c-fat200-2.zip",
    "https://nrvis.com/download/data/dimacs/c-fat200-5.zip",
    "https://nrvis.com/download/data/dimacs/c-fat500-1.zip",
    "https://nrvis.com/download/data/dimacs/c-fat500-10.zip",
    "https://nrvis.com/download/data/dimacs/c-fat500-2.zip",
    "https://nrvis.com/download/data/dimacs/c-fat500-5.zip",
    "httpsNext_Responseis.com/download/data/dimacs/gen200-p0-9-44.zip",
    "https://nrvis.com/download/data/dimacs/gen200-p0-9-55.zip",
    "https://nrvis.com/download/data/dimacs/gen400-p0-9-55.zip",
    "https://nrvis.com/download/data/dimacs/gen400-p0-9-65.zip",
    "https://nrvis.com/download/data/dimacs/gen400-p0-9-75.zip",
    "https://nrvis.com/download/data/dimacs/hamming10-2.zip",
    "https://nrvis.com/download/data/dimacs/hamming10-4.zip",
    "https://nrvis.com/download/data/dimacs/hamming6-2.zip",
    "https://nrvis.com/download/data/dimacs/hamming6-4.zip",
    "https://nrvis.com/download/data/dimacs/hamming8-2.zip",
    "https://nrvis.com/download/data/dimacs/hamming8-4.zip",
    "https://nrvis.com/download/data/dimacs/johnson16-2-4.zip",
    "https://nrvis.com/download/data/dimacs/johnson32-2-4.zip",
    "https://nrvis.com/download/data/dimacs/johnson8-2-4.zip",
    "https://nrvis.com/download/data/dimacs/johnson8-4-4.zip",
    "https://nrvis.com/download/data/dimacs/keller4.zip",
    "https://nrvis.com/download/data/dimacs/keller5.zip",
    "https://nrvis.com/download/data/dimacs/keller6.zip",
    "https://nrvis.com/download/data/dimacs/p-hat1000-1.zip",
    "https://nrvis.com/download/data/dimacs/p-hat1000-2.zip",
    "https://nrvis.com/download/data/dimacs/p-hat1000-3.zip",
    "https://nrvis.com/download/data/dimacs/p-hat1500-1.zip",
    "https://nrvis.com/download/data/dimacs/p-hat1500-2.zip",
    "https://nrvis.com/download/data/dimacs/p-hat1500-3.zip",
    "https://nrvis.com/download/data/dimacs/p-hat300-3.zip",
    "https://nrvis.com/download/data/dimacs/p-hat500-1.zip",
    "https://nrvis.com/download/data/dimacs/p-hat500-2.zip",
    "https://nrvis.com/download/data/dimacs/p-hat500-3.zip",
    "https://nrvis.com/download/data/dimacs/p-hat700-1.zip",
    "https://nrvis.com/download/data/dimacs/p-hat700-2.zip",
    "https://nrvis.com/download/data/dimacs/p-hat700-3.zip",
    "https://nrvis.com/download/data/dimacs/san1000.zip",
    "https://nrvis.com/download/data/dimacs/san200-0-7-1.zip",
    "https://nrvis.com/download/data/dimacs/san200-0-7-2.zip",
    "https://nrvis.com/download/data/dimacs/san200-0-9-1.zip",
    "https://nrvis.com/download/data/dimacs/san200-0-9-2.zip",
    "https://nrvis.com/download/data/dimacs/san200-0-9-3.zip",
    "https://nrvis.com/download/data/dimacs/san400-0-5-1.zip",
    "https://nrvis.com/download/data/dimacs/san400-0-7-1.zip",
    "https://nrvis.com/download/data/dimacs/san400-0-7-2.zip",
    "https://nrvis.com/download/data/dimacs/san400-0-7-3.zip",
    "httpsm://nrvis.com/download/data/dimacs/san400-0-9-1.zip",
    "https://nrvis.com/download/data/dimacs/sanr200-0-7.zip",
    "https://nrvis.com/download/data/dimacs/sanr200-0-9.zip",
    "https://nrvis.com/download/data/dimacs/sanr400-0-5.zip",
    "https://nrvis.com/download/data/dimacs/sanr400-0-7.zip"
]

# The folder to save the .zip files in
OUTPUT_DIR = "datasets/network-repo/dimacs-zip-files"

# ---------------------

def download_zip_files():
    """
    Downloads all files from URL_LIST into OUTPUT_DIR.
    """
    
    print(f"--- Starting DIMACS Zip Downloader ---")
    
    # 1. Create the output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        print(f"Creating directory: {OUTPUT_DIR}")
        os.makedirs(OUTPUT_DIR)
    else:
        print(f"Directory '{OUTPUT_DIR}' already exists.")

    # Clean the URL list of any stray characters (like 'httpsm://')
    clean_urls = [url.replace("httpsm://", "https://").replace("httpss://", "https://") for url in URL_LIST]
    
    print(f"\nFound {len(clean_urls)} files to process...")
    
    downloaded_count = 0
    skipped_count = 0

    # 2. Loop through each URL in the list
    for url in clean_urls:
        try:
            # Get the filename from the URL (e.g., "C1000-9.zip")
            file_name = os.path.basename(url)
            
            # Create the full local path to save the file
            local_path = os.path.join(OUTPUT_DIR, file_name)
            
            # 3. Check if the file already exists
            if os.path.exists(local_path):
                print(f"- Skipping {file_name} (already exists)")
                skipped_count += 1
                continue
                
            # 4. Download the file
            print(f"- Downloading {file_name}...")
            # Set a timeout for the request
            response = requests.get(url, timeout=10)
            response.raise_for_status() 
            
            # 5. Save the file (in binary write mode)
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            downloaded_count += 1
            
        except requests.exceptions.RequestException as e:
            print(f"  Error downloading {url}: {e}")
        except Exception as e:
            print(f"  An unexpected error occurred with {url}: {e}")

    print("\n--- Download Complete ---")
    print(f"Downloaded: {downloaded_count} new files")
    print(f"Skipped:    {skipped_count} existing files")
    print(f"All .zip files are in: {OUTPUT_DIR}")

if __name__ == "__main__":
    download_zip_files()