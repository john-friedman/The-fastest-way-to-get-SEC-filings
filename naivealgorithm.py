import asyncio
import aiohttp
from datetime import datetime
from datamule import format_accession
import re
import csv
import json

start = '0001172661-25-005305' # this existed before.

# Extract the parts
prefix = start.rsplit('-', 1)[0]  # '0001193125-25'
start_num = int(start.rsplit('-', 1)[1])  # 334399

# Generate accession numbers
ACCESSION_NUMBERS = [
    f'{prefix}-{start_num + (i * 5):06d}'
    for i in range(5)
]

print(ACCESSION_NUMBERS)

USER_AGENT = 'John Holland johnholland@gmail.com' # replace with yours
MAX_REQUESTS_PER_SECOND = 5
DELAY_BETWEEN_REQUESTS = 1.0 / MAX_REQUESTS_PER_SECOND  # 0.2 seconds
OUTPUT_CSV = 'accession_results.csv'  # Output file name

async def check_accession(session, accession, semaphore):
    """Check a single accession number and return when non-empty response found"""
    acc_no_dash = format_accession(accession,'no-dash')
    acc_dash = format_accession(accession,'dash')
    # Try index url
    urls = [
        f"https://www.sec.gov/Archives/edgar/data/{acc_no_dash}/{acc_dash}-index.htm"
    ]
    
    attempt = 0
    while True:
        attempt += 1
        
        async with semaphore:  # Limit concurrent requests
            for url in urls:
                try:
                    async with session.get(url, headers={'User-Agent': USER_AGENT}) as response:
                        content = await response.text()
                        timestamp = datetime.now()
                        
                        ciks = re.findall(r'CIK=(\d+)&', content)
                        ciks = list(set([int(cik) for cik in ciks]))


                        if ciks != []:  # Non-empty check
                            print(f"✓ [{timestamp}] Accession {accession} - SUCCESS on attempt {attempt}")
                            print(f"  URL: {url}")
                            print(f"  Response length: {len(content)} bytes")
                            print(f"  Status: {response.status}")
                            return {
                                'accession': accession,
                                'ciks' : list(ciks),
                                'url': url,
                                'attempt': attempt,
                                'timestamp': timestamp,
                                'status': response.status,
                                'content_length': len(content)
                            }
                        else:
                            pass
                    
                    # Rate limiting delay
                    await asyncio.sleep(DELAY_BETWEEN_REQUESTS)
                    
                except Exception as e:
                    print(f"  [{datetime.now()}] Accession {accession} - Error: {e}")
                    await asyncio.sleep(DELAY_BETWEEN_REQUESTS)
        
        # Wait before retry
        await asyncio.sleep(1)

async def main():
    # Semaphore to limit concurrent requests (rate limiting)
    semaphore = asyncio.Semaphore(MAX_REQUESTS_PER_SECOND)
    
    async with aiohttp.ClientSession() as session:
        # Run all accession checks concurrently
        tasks = [check_accession(session, acc, semaphore) for acc in ACCESSION_NUMBERS]
        results = await asyncio.gather(*tasks)
    
    # Save results to CSV
    if results:
        with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['accession', 'ciks', 'url', 'attempt', 'timestamp', 'status', 'content_length']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in results:
                if result:  # Only write non-None results
                    # Convert ciks list to JSON string for CSV storage
                    row = result.copy()
                    row['ciks'] = json.dumps(row['ciks'])
                    row['timestamp'] = row['timestamp'].isoformat()
                    writer.writerow(row)
        
        print(f"\n✓ Results saved to {OUTPUT_CSV}")
    else:
        print("\nNo results to save")

if __name__ == "__main__":
    asyncio.run(main())