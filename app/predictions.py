# --- Imports ---
import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from datetime import datetime
import requests
import json
from flask import jsonify
# --- API Setup ---
API_KEY = 'aeff1e28c4cc893b57afe082368ae090'  # 🔁 Replace this with your actual API key
CITY = 'Bangalore'  # Change to your city name
URL = f'http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric'

# --- Load historical data ---
df = pd.read_csv('D:/skicast_project/data/skicastfinaldata.csv')
if 'Unnamed: 0' in df.columns:
    df = df.drop(columns=['Unnamed: 0'])
df['date'] = pd.to_datetime(df['date'])
df = df.set_index('date')
df = df.sort_index()
df = df.interpolate(method='time')

# --- Fetch today's weather data from API ---
response = requests.get(URL)
if response.status_code == 200:
    weather = response.json()
    today_data = {
        'date': pd.to_datetime(datetime.utcnow().date()),
        'tavg': weather['main']['temp'],
        'tmin': weather['main']['temp_min'],
        'tmax': weather['main']['temp_max'],
        'prcp': weather.get('rain', {}).get('1h', 0.0),
        'wspd': weather['wind']['speed'],
        'wdir': weather['wind'].get('deg', 0.0),
        'pres': weather['main']['pressure']
    }
    
else:
    raise Exception(f"API call failed with status code {response.status_code}")

# --- Append today's data ---
today_date = pd.to_datetime(datetime.utcnow().date())

if today_date not in df.index:
    today_df = pd.DataFrame([today_data])
    today_df = today_df.set_index('date')
    
    df = pd.concat([df, today_df])
    df = df.sort_index()
    df.to_csv('D:/skicast_project/data/skicastfinaldata.csv')

# --- Feature Engineering ---
lags = [1, 2, 3, 4, 5, 6, 7, 14]
for lag in lags:
    for col in ['tavg', 'tmin', 'tmax', 'prcp', 'wspd', 'pres']:
        df[f'{col}_lag{lag}'] = df[col].shift(lag)

rolling_windows = [3, 7]
for window in rolling_windows:
    for col in ['tavg', 'prcp', 'wspd', 'pres']:
        df[f'{col}_roll{window}'] = df[col].rolling(window).mean()

df = df.dropna()

# --- Prepare features and targets ---
features = df.drop(['tavg', 'tmin', 'tmax', 'prcp', 'wspd'], axis=1)
target_columns = ['tavg', 'tmin', 'tmax', 'prcp', 'wspd']

# Train/Test split
split_point = int(len(df) * 0.9)
X_train = features.iloc[:split_point]
X_test = features.iloc[split_point:]

# --- Train models for each target ---
models = {}
metrics = {}
for target in target_columns:
    y_train = df[target].iloc[:split_point]
    y_test = df[target].iloc[split_point:]

    model = XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    models[target] = model
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    metrics[target] = {'RMSE': rmse, 'MAE': mae, 'R2': r2}
    

# --- 7-Day Forecast starting from Tomorrow ---
def get_predictions():
    future_df = df.copy()
    future_days = 7
    start_date = future_df.index[-1] + pd.Timedelta(days=1)
    future_predictions = pd.DataFrame(index=pd.date_range(start=start_date, periods=future_days))
    feature_cols = X_train.columns.tolist()

    for day_index, future_date in enumerate(future_predictions.index):
        last_row = future_df.iloc[-1]
        new_row = build_feature_row(future_df, last_row)
        new_X = pd.DataFrame([new_row])[feature_cols]

        for target in target_columns:
            pred = models[target].predict(new_X)[0]
            pred_rounded = round(pred, 2)  
            future_predictions.loc[future_date, target] = pred_rounded
            future_df.loc[future_date, target] = pred_rounded
        
        preserve_constants(future_df, future_date, last_row)
    return convert_to_dict(future_predictions)


def build_feature_row(future_df, last_row):
    new_row = {}

    # Lag features
    for lag in lags:
        for col in ['tavg', 'tmin', 'tmax', 'prcp', 'wspd', 'pres']:
            new_row[f'{col}_lag{lag}'] = future_df[col].iloc[-lag] if lag <= len(future_df) else last_row[col]

    # Rolling features
    for window in rolling_windows:
        for col in ['tavg', 'prcp', 'wspd', 'pres']:
            lag_values = [
                new_row[f'{col}_lag{i}']
                for i in range(1, window + 1)
                if f'{col}_lag{i}' in new_row
            ]
            new_row[f'{col}_roll{window}'] = np.mean(lag_values) if lag_values else last_row.get(f'{col}_roll{window}', 0)

    # Constant features
    new_row['wdir'] = last_row['wdir']
    new_row['pres'] = last_row['pres']

    return new_row


def preserve_constants(future_df, future_date, last_row):
    future_df.loc[future_date, 'pres'] = last_row['pres']
    future_df.loc[future_date, 'wdir'] = last_row['wdir']


def convert_to_dict(pred_df):
    pred_df.index = range(1, len(pred_df) + 1)
    return {
        str(day): {
            'avg_temp': round(float(row['tavg']), 2), 
            'min_temp': round(float(row['tmin']), 2),  
            'max_temp': round(float(row['tmax']), 2),  
            'precip': round(float(row['prcp']), 2),  
            'wind': round(float(row['wspd']), 2)  
        }
        for day, row in pred_df.iterrows()
    }
