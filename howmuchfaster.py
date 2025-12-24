import time
import csv
from datetime import datetime
import requests
from datamule import format_accession, Sheet

batch_size = 100
user_agent = 'John Holland johnholland@gmail.com' # Put your user agent here

# Initialize Sheet
sheet = Sheet('time')

filings = sheet.get_table(
    'sec-filings-lookup',
    filingDate='2025-12-23',
    returnCols=['accessionNumber', 'cik', 'detectedTime']
)

# Get unique accessions first
unique_accessions = list({f['accessionNumber']: f for f in filings}.values())[:batch_size]

def parse_http_date(http_date):
    """Convert HTTP date format to ISO datetime string"""
    if not http_date:
        return None
    try:
        dt = datetime.strptime(http_date, '%a, %d %b %Y %H:%M:%S %Z')
        return dt.isoformat() + 'Z'
    except:
        return http_date

results = []

for filing in unique_accessions:
    acc_no_dash = str(filing['accessionNumber'])
    acc_dash = format_accession(acc_no_dash, 'dash')
    company_cik = filing['cik']

    company_cik = company_cik.split(',')[0]

    # Construct URLs
    index_url = f"https://www.sec.gov/Archives/edgar/data/{acc_no_dash}/{acc_dash}-index.htm"
    sgml_url = f"https://www.sec.gov/Archives/edgar/data/{company_cik}/{acc_dash}.txt"
    
    # Fetch Last-Modified headers (5 req/sec = 0.2s between requests)
    try:
        r_index = requests.head(index_url, headers={'User-Agent': user_agent})
        index_lmt = parse_http_date(r_index.headers.get('Last-Modified'))
        time.sleep(0.2)
        
        r_sgml = requests.head(sgml_url, headers={'User-Agent': user_agent})
        sgml_lmt = parse_http_date(r_sgml.headers.get('Last-Modified'))
        time.sleep(0.2)
        
        results.append({
            'accessionNumber': acc_no_dash,
            'detectedTime': filing['detectedTime'],
            'index_lmt': index_lmt,
            'sgml_lmt': sgml_lmt
        })
        print(f"Processed {len(results)}")
    except Exception as e:
        print(f"Error for {acc_no_dash}: {e}")

# Save results to CSV file
with open('etag_results.csv', 'w', newline='') as f:
    fieldnames = ['accessionNumber', 'detectedTime', 'index_lmt', 'sgml_lmt']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    
    writer.writeheader()
    writer.writerows(results)

print(f"Saved {len(results)} results to etag_results.csv")