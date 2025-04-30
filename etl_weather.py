import requests
import pandas as pd
import boto3
from datetime import datetime, timezone

# CONFIGURATION
API_KEY = "6322760b8c6c7b02de373f56c1a2cd08"  # OpenWeather API key
CITY = "Mount Pleasant"
STATE = "MI"
COUNTRY = "US"
S3_BUCKET = "weather-etl-gireesh-240421"     # Your S3 bucket
FILE_FORMAT = "csv"                           # Options: 'csv' or 'json'
AWS_REGION = "us-east-2"

def extract_weather():
    """Fetch weather data from OpenWeather API"""
    url = (
        f"http://api.openweathermap.org/data/2.5/weather"
        f"?q={CITY},{STATE},{COUNTRY}&appid={API_KEY}&units=metric"
    )
    response = requests.get(url)
    response.raise_for_status()  # Will raise an error for non-200 codes
    return response.json()

def transform_weather(data):
    """Extract and format relevant fields into a DataFrame"""
    weather = {
        "city": data.get("name"),
        "temperature_celsius": data["main"]["temp"],
        "humidity_percent": data["main"]["humidity"],
        "wind_speed_mps": data["wind"]["speed"],
        "weather_description": data["weather"][0]["main"],
        "timestamp_utc": datetime.now(timezone.utc).isoformat()
    }
    return pd.DataFrame([weather])

def load_to_s3(df):
    """Save transformed data to S3 in the desired format"""
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    filename = f"weather_{timestamp}.{FILE_FORMAT}"
    
    if FILE_FORMAT == "csv":
        file_data = df.to_csv(index=False)
    else:
        file_data = df.to_json(orient="records")

    s3 = boto3.client("s3", region_name=AWS_REGION)
    s3.put_object(Bucket=S3_BUCKET, Key=f"weather_data/{filename}", Body=file_data)

def run_etl():
    """Run the complete ETL process"""
    print("🔄 Starting ETL process...")
    raw_data = extract_weather()
    print("✅ Data extracted.")
    df = transform_weather(raw_data)
    print("✅ Data transformed.")
    load_to_s3(df)
    print("✅ Data uploaded to S3.")

# Run manually
if __name__ == "__main__":
    run_etl()
