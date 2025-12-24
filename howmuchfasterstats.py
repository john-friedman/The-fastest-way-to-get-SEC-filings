import csv
from datetime import datetime
import statistics

def parse_iso_datetime(dt_string):
    """Parse ISO datetime string to datetime object"""
    if not dt_string:
        return None
    # Handle both formats: with and without milliseconds
    if '.' in dt_string:
        return datetime.strptime(dt_string, '%Y-%m-%dT%H:%M:%S.%fZ')
    else:
        return datetime.strptime(dt_string, '%Y-%m-%dT%H:%M:%SZ')

def calculate_time_diff_seconds(dt1, dt2):
    """Calculate time difference in seconds between two datetime objects"""
    if not dt1 or not dt2:
        return None
    return (dt2 - dt1).total_seconds()

# Read CSV file
detected_index_diffs = []
detected_sgml_diffs = []

with open('etag_results.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        detected_time = parse_iso_datetime(row['detectedTime'])
        index_lmt = parse_iso_datetime(row['index_lmt'])
        sgml_lmt = parse_iso_datetime(row['sgml_lmt'])
        
        # Calculate detected - index (negative means index came before detected)
        if detected_time and index_lmt:
            diff = calculate_time_diff_seconds(index_lmt, detected_time)
            detected_index_diffs.append(diff)
        
        # Calculate detected - sgml (negative means sgml came before detected)
        if detected_time and sgml_lmt:
            diff = calculate_time_diff_seconds(sgml_lmt, detected_time)
            detected_sgml_diffs.append(diff)

# Calculate statistics
def calc_stats(data):
    if not data:
        return None, None, None
    sorted_data = sorted(data)
    return {
        '25th percentile': statistics.quantiles(sorted_data, n=4)[0],
        'mean': statistics.mean(sorted_data),
        '75th percentile': statistics.quantiles(sorted_data, n=4)[2]
    }

print("=" * 80)
print("TIME DIFFERENCE STATISTICS (in seconds)")
print("=" * 80)
print()

print("DETECTED - INDEX (positive = detected came after index):")
print("-" * 80)
stats = calc_stats(detected_index_diffs)
if stats:
    print(f"  25th percentile: {stats['25th percentile']:,.2f} seconds")
    print(f"  Mean:            {stats['mean']:,.2f} seconds")
    print(f"  75th percentile: {stats['75th percentile']:,.2f} seconds")
    print(f"  Sample size:     {len(detected_index_diffs)}")
else:
    print("  No data available")

print()
print("DETECTED - SGML (positive = detected came after sgml):")
print("-" * 80)
stats = calc_stats(detected_sgml_diffs)
if stats:
    print(f"  25th percentile: {stats['25th percentile']:,.2f} seconds")
    print(f"  Mean:            {stats['mean']:,.2f} seconds")
    print(f"  75th percentile: {stats['75th percentile']:,.2f} seconds")
    print(f"  Sample size:     {len(detected_sgml_diffs)}")
else:
    print("  No data available")

print()
print("=" * 80)