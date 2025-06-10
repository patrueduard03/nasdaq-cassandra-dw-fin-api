import nasdaqdatalink
import os
from dotenv import load_dotenv

load_dotenv()

# Set API key
api_key = os.getenv('NASDAQ_DATA_LINK_API_KEY')
if api_key is not None:
    nasdaqdatalink.read_key(api_key)
else:
    raise ValueError("NASDAQ_DATA_LINK_API_KEY environment variable is not set")

try:
    # Test with exact parameters
    df = nasdaqdatalink.get_table(
        'WIKI/PRICES',
        ticker='AAPL',
        **{
            'date.gte': '2017-01-01',
            'date.lte': '2017-01-05'
        }
    )
    print(f"Success! Got {len(df)} records")
    if not df.empty:
        print(df.head())
except Exception as e:
    print(f"Error: {e}")