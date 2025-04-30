import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime
import pytz
import os
import boto3
from botocore.exceptions import NoCredentialsError
from sklearn.ensemble import RandomForestRegressor

# CONFIG
API_KEY = "a708197448404507be8174001252904"
LOCATION = "Mount Pleasant"
BUCKET_NAME = "weather-etl-gireesh-240421"
REGION = "us-east-2"
S3_PREFIX = "weather_data/"
LOCAL_DIR = "/tmp"
eastern = pytz.timezone('US/Eastern')

# 1. Fetch last 10 hours
def fetch_last_10_hours():
    now = datetime.datetime.now(eastern)
    url = f"https://api.weatherapi.com/v1/history.json?key={API_KEY}&q={LOCATION}&dt={now.strftime('%Y-%m-%d')}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    current_hour = now.hour
    hours_data = data['forecast']['forecastday'][0]['hour']

    last_10 = hours_data[max(0, current_hour - 10):current_hour + 1]

    df = pd.DataFrame({
        'Timestamp': [h['time'] for h in last_10],
        'Temperature': [h['temp_c'] for h in last_10],
        'Humidity': [h['humidity'] for h in last_10]
    })
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df['Timestamp'] = df['Timestamp'].dt.tz_localize('US/Eastern')
    return df

# 2. Predict next hour using Random Forest
def predict_next_hour(df):
    df = df.sort_values('Timestamp')
    df['Timestamp_numeric'] = df['Timestamp'].astype(np.int64) // 10**9

    X = df[['Timestamp_numeric']]
    y = df['Temperature']

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    r2 = model.score(X, y)

    last_timestamp = df['Timestamp'].max()
    future_time_et = last_timestamp + pd.Timedelta(hours=1)
    future_numeric = int(future_time_et.timestamp())
    future_temp = model.predict(np.array([[future_numeric]]))

    return future_temp[0], future_time_et, r2

# 3. Save cleaned actual + forecast CSVs
def save_data(df, predicted_temp, future_time_et):
    full_path = os.path.join(LOCAL_DIR, "weather_data.csv")
    df.to_csv(full_path, index=False)

    forecast_df = pd.DataFrame({
        'forecast_timestamp_et': [future_time_et.isoformat()],
        'predicted_temperature_celsius': [predicted_temp]
    })
    forecast_file = f"prediction_{future_time_et.strftime('%Y%m%d_%H%M')}.csv"
    forecast_path = os.path.join(LOCAL_DIR, forecast_file)
    forecast_df.to_csv(forecast_path, index=False)

    return full_path, forecast_path

# 4. Download all prediction files from S3
def download_predictions_from_s3():
    prediction_folder = os.path.join(LOCAL_DIR, "predictions")
    os.makedirs(prediction_folder, exist_ok=True)

    s3 = boto3.client('s3', region_name=REGION)
    response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=S3_PREFIX)

    if 'Contents' not in response:
        print("⚠️ No prediction files found in S3.")
        return []

    prediction_files = []
    for obj in response['Contents']:
        key = obj['Key']
        if key.endswith('.csv') and 'prediction_' in key:
            local_path = os.path.join(prediction_folder, os.path.basename(key))
            s3.download_file(BUCKET_NAME, key, local_path)
            prediction_files.append(local_path)

    print(f"✅ Downloaded {len(prediction_files)} prediction files.")
    return prediction_files

# 5. Plot

def create_combined_plot(df, predicted_temp, future_time_et, r2):
    import matplotlib.dates as mdates

    fig, ax1 = plt.subplots(figsize=(16, 10))
    plt.rcParams.update({'font.size': 12})

    df = df.sort_values('Timestamp')
    ax1.plot(df['Timestamp'], df['Temperature'], label='Temperature (°C)', color='blue', marker='o')

    for x, y in zip(df['Timestamp'], df['Temperature']):
        ax1.text(x, y + 0.3, f'{y:.1f}', ha='center', fontsize=10, color='blue')

    prediction_folder = os.path.join(LOCAL_DIR, "predictions")
    all_preds = []
    if os.path.exists(prediction_folder):
        for file in os.listdir(prediction_folder):
            if file.endswith('.csv'):
                pred_df = pd.read_csv(os.path.join(prediction_folder, file))
                pred_df['forecast_timestamp_et'] = pd.to_datetime(pred_df['forecast_timestamp_et'])
                if pred_df['forecast_timestamp_et'].dt.tz is None:
                    pred_df['forecast_timestamp_et'] = pred_df['forecast_timestamp_et'].dt.tz_localize('US/Eastern')
                all_preds.append(pred_df)

    if all_preds:
        pred_combined = pd.concat(all_preds)
        pred_combined = pred_combined.sort_values('forecast_timestamp_et')
        ax1.scatter(pred_combined['forecast_timestamp_et'], pred_combined['predicted_temperature_celsius'],
                    color='red', label='Predicted Temps', marker='x', s=100)

        for x, y in zip(pred_combined['forecast_timestamp_et'], pred_combined['predicted_temperature_celsius']):
            ax1.text(x, y - 0.8, f'{y:.1f}°C', ha='center', fontsize=11, color='red')

    ax1.set_ylabel("Temperature (°C)", color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.set_yticks(range(0, 41, 5))

    ax2 = ax1.twinx()
    ax2.plot(df['Timestamp'], df['Humidity'], label='Humidity (%)', color='orange', marker='s')
    for x, y in zip(df['Timestamp'], df['Humidity']):
        ax2.text(x, y + 0.5, f'{y:.0f}', ha='center', fontsize=10, color='orange')

    ax2.set_ylabel("Humidity (%)", color='orange')
    ax2.tick_params(axis='y', labelcolor='orange')
    ax2.set_yticks(range(0, 101, 10))

    plt.annotate(f"R² = {r2:.3f}",
                 xy=(0.99, 0.01), xycoords='axes fraction',
                 ha='right', va='bottom',
                 fontsize=11,
                 bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="black"))

    all_times = list(df['Timestamp'])
    if all_preds:
        all_times += list(pred_combined['forecast_timestamp_et'])

    ax1.set_xticks(all_times)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M', tz=eastern))
    ax1.set_xlabel("Timestamp")
    ax1.set_title("Temperature, Humidity, and Future Temperature Forecast", fontsize=15)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    plt.xticks(rotation=45)
    plt.tight_layout()

    plot_path = os.path.join(LOCAL_DIR, "combined_weather_plot.png")
    plt.savefig(plot_path)
    plt.close()
    return plot_path

# 6. Upload

def upload_to_s3(*files):
    s3 = boto3.client('s3', region_name=REGION)
    for f in files:
        key = S3_PREFIX + os.path.basename(f)
        try:
            s3.upload_file(f, BUCKET_NAME, key)
            print(f"✅ Uploaded: {key}")
        except NoCredentialsError:
            print(f"❌ AWS credentials missing for: {f}")

# Run all

def run_etl():
    print("🔄 Starting ETL process...")
    df = fetch_last_10_hours()
    predicted_temp, future_time_et, r2 = predict_next_hour(df)
    print(f"📈 Forecast @ {future_time_et.strftime('%Y-%m-%d %H:%M')} → {predicted_temp:.2f} °C | R² = {r2:.3f}")
    csv_full, csv_forecast = save_data(df, predicted_temp, future_time_et)
    upload_to_s3(csv_full, csv_forecast)
    download_predictions_from_s3()
    plot_path = create_combined_plot(df, predicted_temp, future_time_et, r2)
    upload_to_s3(plot_path)
    print("✅ ETL complete.")

if __name__ == "__main__":
    run_etl()