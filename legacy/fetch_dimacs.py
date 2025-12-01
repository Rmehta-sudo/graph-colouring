import os
import requests
import re
from urllib.parse import urljoin

# --- Configuration ---
# This is the base URL where the 'instances' folder is located
BASE_URL = "https://mat.tepper.cmu.edu/COLOR/"

# Using the directory path from your previous attempts
OUTPUT_DIR = "datasets/dimacs"

# The raw, broken HTML you provided
HTML_BLOB = """
coloring, source.<ul><li><a HREF="instances/DSJC1000.1.col.b"> DSJC1000.1.col.b </a> (1000,99258), ?, <a HREF="#XXDSJ">DSJ</a><li><a HREF="instances/DSJC1000.5.col.b"> DSJC1000.5.col.b </a> (1000,499652), ?, <a HREF="#XXDSJ">DSJ</a><li><a HREF="instances/DSJC1000.9.col.b"> DSJC1000.9.col.b </a> (1000,898898), ?, <a HREF="#XXDSJ">DSJ</a><li><a HREF="instances/DSJC125.1.col.b"> DSJC125.1.col.b </a> (125,1472), ?, <a HREF="#XXDSJ">DSJ</a><li><a HREF="instances/DSJC125.5.col.b"> DSJC125.5.col.b </a> (125,7782), ?, <a HREF="#XXDSJ">DSJ</a><li><a HREF="instances/DSJC125.9.col.b"> DSJC125.9.col.b </a> (125,13922), ?, <a HREF="#XXDSJ">DSJ</a><li><a HREF="instances/DSJC250.1.col.b"> DSJC250.1.col.b </a> (250,6436), ?, <a HREF="#XXDSJ">DSJ</a><li><a HREF="instances/DSJC250.5.col.b"> DSJC250.5.col.b </a> (250,31366), ?, <a HREF="#XXDSJ">DSJ</a><li><a HREF="instances/DSJC250.9.col.b"> DSJC250.9.col.b </a> (250,55794), ?, <a HREF="#XXDSJ">DSJ</a><li><a HREF="instances/DSJC500.1.col.b"> DSJC500.1.col.b </a> (500,24916), ?, <a HREF="#XXDSJ">DSJ</a><li><a HREF="instances/DSJC500.5.col.b"> DSJC500.5.col.b </a> (500,125249), ?, <a HREF="#XXDSJ">DSJ</a><li><a HREF="instances/DSJC500.9.col.b"> DSJC500.9.col.b </a> (500,224874), ?, <a HREF="#XXDSJ">DSJ</a><li><a HREF="instances/DSJR500.1.col.b"> DSJR500.1.col.b </a> (500,7110), ?, <a HREF="#XXDSJ">DSJ</a><li><a HREF="instances/DSJR500.1c.col.b"> DSJR500.1c.col.b </a> (500,242550), ?, <a HREF="#XXDSJ">DSJ</a><li><a HREF="instances/DSJR500.5.col.b"> DSJR500.5.col.b </a> (500, 117724), ?, <a HREF="#XXDSJ">DSJ</a><li><a HREF="instances/flat1000_50_0.col.b"> flat1000_50_0.col.b </a> (1000,245000), 50, <a HREF="#XXCUL">CUL</a><li><a HREF="instances/flat1000_60_0.col.b"> flat1000_60_0.col.b </a> (1000,245830), 60, <a HREF="#XXCUL">CUL</a><li><a HREF="instances/flat1000_76_0.col.b"> flat1000_76_0.col.b </a> (1000,246708), 76, <a HREF="#XXCUL">CUL</a><li><a HREF="instances/flat300_20_0.col.b"> flat300_20_0.col.b </a> (300,21375), 20, <a HREF="#XXCUL">CUL</a><li><a HREF="instances/flat300_26_0.col.b"> flat300_26_0.col.b </a> (300, 21633), 26, <a HREF="#XXCUL">CUL</a><li><a HREF="instances/flat300_28_0.col.b"> flat300_28_0.col.b </a> (300, 21695), 28, <a HREF="#XXCUL">CUL</a><li><a HREF="instances/fpsol2.i.1.col">  fpsol2.i.1.col </a> (496,11654), 65, <a HREF="#XXREG">REG</a><li><a HREF="instances/fpsol2.i.2.col">  fpsol2.i.2.col </a> (451,8691), 30, <a HREF="#XXREG">REG</a><li><a HREF="instances/fpsol2.i.3.col">  fpsol2.i.3.col </a> (425,8688), 30, <a HREF="#XXREG">REG</a><li><a HREF="instances/inithx.i.1.col">  inithx.i.1.col </a> (864,18707), 54, <a HREF="#XXREG">REG</a><li><a HREF="instances/inithx.i.2.col">  inithx.i.2.col </a> (645, 13979), 31, <a HREF="#XXREG">REG</a><li><a HREF="instances/inithx.i.3.col">  inithx.i.3.col </a> (621,13969), 31, <a HREF="#XXREG">REG</a><li><a HREF="instances/latin_square_10.col"> latin_square_10.col </a>     (900,307350), ?, <a HREF="#XXLAT&gt;LAT&lt;/A&gt; (Caution: 3 MB!)&lt;li&gt;&lt;A HREF=" instances/le450_15a.col">  le450_15a.col </a> (450,8168), 15, <a HREF="#XXLEI">LEI</a><li><a HREF="instances/le450_15b.col">  le450_15b.col </a> (450,8169), 15, <a HREF="#XXLEI">LEI</a><li><a HREF="instances/le450_15c.col">  le450_15c.col </a> (450,16680), 15, <a HREF="#XXLEI">LEI</a><li><a HREF="instances/le450_15d.col">  le450_15d.col </a> (450,16750), 15, <a HREF="#XXLEI">LEI</a><li><a HREF="instances/le450_25a.col">  le450_25a.col </a> (450,8260), 25, <a HREF="#XXLEI">LEI</a><li><a HREF="instances/le450_25b.col">  le450_25b.col </a> (450,8263), 25, <a HREF="#XXLEI">LEI</a><li><a HREF="instances/le450_25c.col">  le450_25c.col </a> (450,17343), 25, <a HREF="#XXLEI">LEI</a><li><a HREF="instances/le450_25d.col">  le450_25d.col </a> (450,17425), 25, <a HREF="#XXLEI">LEI</a><li><a HREF="instances/le450_5a.col">  le450_5a.col </a> (450,5714), 5, <a HREF="#XXLEI">LEI</a><li><a HREF="instances/le450_5b.col">  le450_5b.col </a> (450,5734), 5, <a HREF="#XXLEI">LEI</a><li><a HREF="instances/le450_5c.col">  le450_5c.col </a> (450,9803), 5, <a HREF="#XXLEI">LEI</a><li><a HREF="instances/le450_5d.col">  le450_5d.col </a> (450,9757), 5, <a HREF="#XXLEI">LEI</a><li><a HREF="instances/mulsol.i.1.col">  mulsol.i.1.col </a> (197,3925), 49, <a HREF="#XXREG">REG</a><li><a HREF="instances/mulsol.i.2.col">  mulsol.i.2.col </a> (188,3885), 31, <a HREF="#XXREG">REG</a><li><a HREF="instances/mulsol.i.3.col">  mulsol.i.3.col </a> (184,3916), 31, <a HREF="#XXREG">REG</a><li><a HREF="instances/mulsol.i.4.col">  mulsol.i.4.col </a> (185,3946), 31, <a HREF="#XXREG">REG</a><li><a HREF="instances/mulsol.i.5.col">  mulsol.i.5.col </a> (186,3973), 31, <a HREF="#XXREG">REG</a><li><a HREF="instances/school1.col">  school1.col </a> (385,19095), ?, <a HREF="#XXSCH">SCH</a><li><a HREF="instances/school1_nsh.col"> school1_nsh.col </a> (352,14612), ?, <a HREF="#XXSCH">SCH</a><li><a HREF="instances/zeroin.i.1.col">  zeroin.i.1.col </a> (211,4100), 49, <a HREF="#XXREG">REG</a><li><a HREF="instances/zeroin.i.2.col">  zeroin.i.2.col </a> (211, 3541), 30, <a HREF="#XXREG">REG</a><li><a HREF="instances/zeroin.i.3.col">  zeroin.i.3.col </a> (206, 3540), 30, <a HREF="#XXREG">REG</a><li><a HREF="instances/anna.col">   anna.col    </a> (138,493), 11, <a HREF="#XXSGB">SGB</a><li><a HREF="instances/david.col"> david.col   </a> (87,406), 11, <a HREF="#XXSGB">SGB</a><li><a HREF="instances/homer.col"> homer.col   </a> (561,1629), 13, <a HREF="#XXSGB">SGB</a><li><a HREF="instances/huck.col"> huck.col    </a> (74,301), 11, <a HREF="#XXSGB">SGB</a><li><a HREF="instances/jean.col"> jean.col    </a> (80,254), 10, <a HREF="#XXSGB">SGB</a><li><a HREF="instances/games120.col"> games120.col   </a> (120,638), 9, <a HREF="#XXSGB">SGB</a><li><a HREF="instances/miles1000.col"> miles1000.col  </a> (128,3216), 42, <a HREF="#XXSGB">SGB</a><li><a HREF="instances/miles1500.col"> miles1500.col  </a> (128,5198), 73, <a HREF="#XXSGB">SGB</a><li><a HREF="instances/miles250.col"> miles250.col   </a> (128,387), 8, <a HREF="#XXSGB">SGB</a><li><a HREF="instances/miles500.col"> miles500.col   </a> (128,1170), 20, <a HREF="#XXSGB">SGB</a><li><a HREF_instances/miles750.col"> miles750.col   </a> (128,2113), 31, <a HREF="#XXSGB">SGB</a><li><a HREF="instances/queen10_10.col"> queen10_10.col  </a> (100,2940), ?, <a HREF="#XXSGB">SGB</a><li><a HREF="instances/queen11_11.col"> queen11_11.col  </a>(121,3960), 11, <a HREF="#XXSGB">SGB</a><li><a HREF="instances/queen12_12.col"> queen12_12.col  </a>(144,5192), ?, <a HREF="#XXSGB">SGB</a>LET<li><a HREF="instances/queen13_13.col"> queen13_13.col  </a>(169,6656), 13, <a HREF="#XXSGB">SGB</a><li><a HREF="instances/queen14_14.col"> queen14_14.col  </a>(196,8372), ?, <a HREF="#XXSGB">SGB</a><li><a HREF="instances/queen15_15.col"> queen15_15.col  </a>(225,10360), ?, <a HREF="#XXSGB">SGB</a><li><a HREF="instances/queen16_16.col"> queen16_16.col  </a>(256,12640), ?, <a HREF="#XXSGB">SGB</a><li><a HREF="instances/queen5_5.col"> queen5_5.col   </a> (25,160), 5, <a HREF="#XXSGB">SGB</a><li><a HREF="instances/queen6_6.col"> queen6_6.col   </a> (36,290), 7, <a HREF="#XXSGB">SGB</a><li><a HREF="instances/queen7_7.col"> queen7_7.col   </a> (49,476), 7, <a HREF="#XXSGB">SGB</a><li><a HREF="instances/queen8_12.col"> queen8_12.col  </a> (96,1368), 12, <a HREF="#XXSGB">SGB</a><li><a HREF="instances/queen8_8.col"> queen8_8.col   </a> (64, 728), 9, <a HREF="#XXSGB">SGB</a><li><a HREF="instances/queen9_9.col"> queen9_9.col   </a> (81, 2112), 10, <a HREF="#XXSGB">SGB</a><li><a HREF="instances/myciel3.col"> myciel3.col   </a> (11,20), 4, <a HREF="#XXMYC">MYC</a><li><a HREF="instances/myciel4.col"> myciel4.col   </a> (23,71), 5, <a HREF="#XXMYC">MYC</a><li><a HREF="instances/myciel5.col"> myciel5.col   </a> (47,236), 6, <a HREF="#XXMYC">MYC</a><li><a HREF="instances/myciel6.col"> myciel6.col   </a> (95,755), 7, <a HREF="#XXMYC">MYC</a><li><a HREF="instances/myciel7.col"> myciel7.col   </a> (191,2360), 8, <a HREF="#XXMYC">MYC</a></ul>
"""
# ---------------------

def download_files_from_html():
    """
    Parses the HTML blob to find and download all graph files.
    """
    print(f"--- Starting Simple DIMACS Downloader ---")
    
    # 1. Create the output directory
    if not os.path.exists(OUTPUT_DIR):
        print(f"Creating directory: {OUTPUT_DIR}")
        os.makedirs(OUTPUT_DIR)
    else:
        print(f"Directory '{OUTPUT_DIR}' already exists.")

    # 2. Find all file paths using regex
    # This regex looks for 'HREF="...instances/filename..."'
    # It handles <a href="..."> and <A HREF="..."> (re.IGNORECASE)
    # It handles spaces after the quote, like in the broken le450_15a link
    pattern = r'HREF="\s*(instances/[^"]+)"'
    
    file_paths = re.findall(pattern, HTML_BLOB, re.IGNORECASE)
    
    # Use a set to remove any duplicates, then sort for clean output
    unique_paths = sorted(list(set(file_paths)))
    
    if not unique_paths:
        print("Error: Could not find any 'instances/...' links in the HTML.")
        return

    print(f"Found {len(unique_paths)} unique files to download.")

    # 3. Loop and download each file
    downloaded_count = 0
    skipped_count = 0
    
    for path in unique_paths:
        # Construct the full URL, e.g.,
        # https://mat.tepper.cmu.edu/COLOR/ + instances/anna.col
        file_url = urljoin(BASE_URL, path)
        
        # Get just the filename (e.g., 'anna.col')
        file_name = os.path.basename(path)
        
        # Create the full local path to save the file
        local_path = os.path.join(OUTPUT_DIR, file_name)

        # 4. Check if file already exists
        if os.path.exists(local_path):
            print(f"- Skipping {file_name} (already exists)")
            skipped_count += 1
            continue
        
        # 5. Download the file
        try:
            print(f"- Downloading {file_name}...")
            response = requests.get(file_url)
            response.raise_for_status()  # Check for errors (like 404)

            # Save the file to disk
            with open(local_path, 'wb') as f:
                f.write(response.content)
            downloaded_count += 1

        except requests.exceptions.RequestException as e:
            print(f"  Error downloading {file_name}: {e}")
        except Exception as e:
            print(f"  Error saving {file_name}: {e}")

    print("\n--- Download Complete ---")
    print(f"Downloaded: {downloaded_count} new files")
    print(f"Skipped:    {skipped_count} existing files")
    print(f"All files are in: {OUTPUT_DIR}")


if __name__ == "__main__":
    download_files_from_html()