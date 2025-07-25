import json
import pandas as pd
import numpy as np
import os
from datetime import datetime
from glob import glob
from tqdm import tqdm

class TaxiDatasetCreator:
    def __init__(self, json_dir, change_flag_csv_path):
        """
        タクシーデータセット作成クラス
        
        Args:
            json_dir: JSONファイルが格納されているディレクトリ
            change_flag_csv_path: change_flag_filled0.csvのパス (必須)
        """
        self.json_dir = json_dir
        self.change_flag_csv_path = change_flag_csv_path
        
        # ステータス変化の定義
        self.get_on_map = ['0003', '0012', '0014', '0103', '0112', '0114', 
                          '0203', '0212', '0214', '0403', '0412', '0414', 
                          '0503', '0512', '0514', '0603', '0612', '0614', 
                          '0803', '0812', '0814', '1303', '1312', '1314', 
                          '1503', '1512', '1514']
        
        self.get_off_map = ['0300', '1200', '1400', '0301', '1201', '1401', 
                           '0302', '1202', '1402', '0304', '1204', '1404', 
                           '0305', '1205', '1405', '0306', '1206', '1406', 
                           '0308', '1208', '1408', '0313', '1213', '1413', 
                           '0315', '1215', '1415']
        
    def load_change_flag_data(self):
        """change_flag_filled0.csvを読み込む"""
        if not os.path.exists(self.change_flag_csv_path):
            raise FileNotFoundError(f"Required file not found: {self.change_flag_csv_path}")
        
        return pd.read_csv(self.change_flag_csv_path)
    
    def parse_timestamp(self, record_datetime, timestamp_str):
        """
        recordDateTimeとtimestampを組み合わせて完全なdatetimeを作成
        
        Args:
            record_datetime: YYYYMMDDHHmmss形式の文字列
            timestamp_str: エポックタイムのミリ秒文字列
        """
        # recordDateTimeから日付を取得
        base_date = datetime.strptime(record_datetime, "%Y%m%d%H%M%S")
        
        # timestampをintに変換（ミリ秒）
        timestamp_ms = int(timestamp_str)
        
        # datetimeオブジェクトを作成
        return pd.Timestamp(timestamp_ms, unit='ms')
    
    def extract_array_features(self, array_str):
        """
        配列文字列から統計的特徴量を抽出
        
        Args:
            array_str: "[値1, 値2, ...]"形式の文字列
        
        Returns:
            dict: 平均、最大、最小、標準偏差などの統計量
        """
        try:
            # 文字列をリストに変換
            values = json.loads(array_str)
            values_array = np.array(values, dtype=float)
            
            return {
                'mean': np.mean(values_array),
                'max': np.max(values_array),
                'min': np.min(values_array),
                'std': np.std(values_array),
                'median': np.median(values_array)
            }
        except:
            return {
                'mean': np.nan,
                'max': np.nan,
                'min': np.nan,
                'std': np.nan,
                'median': np.nan
            }
    
    def process_json_file(self, json_path):
        """
        単一のJSONファイルを処理してデータフレームを作成
        
        Args:
            json_path: JSONファイルのパス
        
        Returns:
            pd.DataFrame: 処理されたデータ
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # IMEIを取得（car_idとして使用）
            imei = data.get('imei', '')
            record_datetime = data.get('recordDateTime', '')
            
            # dataフィールドが存在しない場合は空のDataFrameを返す
            if 'data' not in data or not data['data']:
                return pd.DataFrame()
            
            # 各データポイントを処理
            rows = []
            for record in data['data']:
                row = {
                    'car_id': imei,
                    'timestamp': self.parse_timestamp(record_datetime, record.get('timeStamp', '0')),
                    'speed': float(record.get('speed', 0))
                }
                
                # 加速度データの特徴量抽出
                for axis in ['X', 'Y', 'Z']:
                    acc_features = self.extract_array_features(record.get(f'acc{axis}', '[]'))
                    for stat, value in acc_features.items():
                        row[f'acc{axis}_{stat}'] = value
                
                # 角速度データの特徴量抽出
                for axis in ['X', 'Y', 'Z']:
                    rad_features = self.extract_array_features(record.get(f'rad{axis}', '[]'))
                    for stat, value in rad_features.items():
                        row[f'rad{axis}_{stat}'] = value
                
                # ウインカー情報（配列の最頻値を使用）
                try:
                    right_blinker = json.loads(record.get('vehicleInformationRightBlinker', '[0]'))
                    left_blinker = json.loads(record.get('vehicleInformationLeftBlinker', '[0]'))
                    
                    # 最頻値を取得（1が多ければON、0が多ければOFF）
                    row['right_blinker'] = 1 if sum(right_blinker) > len(right_blinker) / 2 else 0
                    row['left_blinker'] = 1 if sum(left_blinker) > len(left_blinker) / 2 else 0
                except:
                    row['right_blinker'] = 0
                    row['left_blinker'] = 0
                
                rows.append(row)
            
            return pd.DataFrame(rows)
            
        except Exception as e:
            print(f"Error processing {json_path}: {str(e)}")
            return pd.DataFrame()
    
    def create_dataset(self):
        """
        全てのJSONファイルを処理してデータセットを作成
        
        Returns:
            pd.DataFrame: 完成したデータセット
        """
        # JSONファイルのリストを取得
        json_files = glob(os.path.join(self.json_dir, "*.json"))
        
        if not json_files:
            raise ValueError(f"No JSON files found in {self.json_dir}")
        
        print(f"Found {len(json_files)} JSON files")
        
        # 各JSONファイルを処理
        all_data = []
        for json_file in tqdm(json_files, desc="Processing JSON files"):
            df = self.process_json_file(json_file)
            if not df.empty:
                all_data.append(df)
        
        # 全データを結合
        if not all_data:
            raise ValueError("No data extracted from JSON files")
        
        combined_df = pd.concat(all_data, ignore_index=True)
        print(f"Total records: {len(combined_df)}")
        
        # change_flagデータを読み込み
        change_flag_df = self.load_change_flag_data()
        
        # タイムスタンプをミリ秒に変換（マッチング用）
        combined_df['timestamp_ms'] = combined_df['timestamp'].astype(np.int64) // 10**6
        
        # change_flagデータとマージ
        # car_idとtime_stampでマッチング
        merged_df = pd.merge(
            combined_df,
            change_flag_df[['car_id', 'time_stamp', 'status_management', 'change_flag']],
            left_on=['car_id', 'timestamp_ms'],
            right_on=['car_id', 'time_stamp'],
            how='left'
        )
        
        # ラベルの作成（change_flagが存在する場合はそれを使用）
        merged_df['label'] = 0  # デフォルトは0（変化なし）
        
        # change_flagが1の場合
        merged_df.loc[merged_df['change_flag'] == 1, 'label'] = 1
        
        # status_managementから乗車・降車を判定（change_flagがNaNの場合）
        if 'status_management' in merged_df.columns:
            # ステータス変化を4桁の文字列に変換
            merged_df['status_change'] = merged_df.groupby('car_id')['status_management'].apply(
                lambda x: x.astype(str).str.zfill(2) + x.shift(1).astype(str).str.zfill(2)
            ).reset_index(level=0, drop=True)
            
            # 乗車パターンの検出
            merged_df.loc[merged_df['status_change'].isin(self.get_on_map), 'label'] = 1
            
            # 降車パターンの検出
            merged_df.loc[merged_df['status_change'].isin(self.get_off_map), 'label'] = 2
        
        # 不要なカラムを削除
        columns_to_drop = ['timestamp_ms', 'time_stamp', 'status_management', 
                          'change_flag', 'status_change']
        merged_df = merged_df.drop(columns=[col for col in columns_to_drop if col in merged_df.columns])
        
        # 時間順にソート
        merged_df = merged_df.sort_values(['car_id', 'timestamp']).reset_index(drop=True)
        
        return merged_df
    
    def save_dataset(self, output_path, train_ratio=0.8):
        """
        データセットを作成して保存
        
        Args:
            output_path: 出力ファイルパス（拡張子なし）
            train_ratio: 訓練データの割合
        """
        # データセットを作成
        dataset = self.create_dataset()
        
        # 車両ごとに訓練・テストデータに分割
        train_data = []
        test_data = []
        
        for car_id in dataset['car_id'].unique():
            car_data = dataset[dataset['car_id'] == car_id]
            
            # 時系列を考慮して分割
            split_idx = int(len(car_data) * train_ratio)
            train_data.append(car_data.iloc[:split_idx])
            test_data.append(car_data.iloc[split_idx:])
        
        train_df = pd.concat(train_data, ignore_index=True)
        test_df = pd.concat(test_data, ignore_index=True)
        
        # CSVとして保存
        train_df.to_csv(f"{output_path}_train.csv", index=False)
        test_df.to_csv(f"{output_path}_test.csv", index=False)
        
        # 全データも保存
        dataset.to_csv(f"{output_path}_full.csv", index=False)
        
        print(f"Dataset saved:")
        print(f"  - Full dataset: {output_path}_full.csv ({len(dataset)} records)")
        print(f"  - Train dataset: {output_path}_train.csv ({len(train_df)} records)")
        print(f"  - Test dataset: {output_path}_test.csv ({len(test_df)} records)")
        
        # ラベルの分布を表示
        print("\nLabel distribution:")
        print(dataset['label'].value_counts().sort_index())
        
        return dataset


# 使用例
if __name__ == "__main__":
    # パラメータ設定
    json_directory = "./json"  # JSONファイルが格納されているディレクトリ
    change_flag_csv = "./change_flag_filled0.csv"  # change_flagのCSVファイル
    output_path = "./taxi_dataset"  # 出力ファイルのプレフィックス
    
    # change_flag_filled0.csvの存在確認（必須ファイル）
    if not os.path.exists(change_flag_csv):
        raise FileNotFoundError(f"Required file not found: {change_flag_csv}\n"
                               f"This file is essential for labeling. Please ensure it exists before running.")
    
    # データセット作成
    creator = TaxiDatasetCreator(json_directory, change_flag_csv)
    dataset = creator.save_dataset(output_path, train_ratio=0.8)
    
    # データセットの情報を表示
    print("\nDataset shape:", dataset.shape)
    print("\nColumns:", dataset.columns.tolist())
    print("\nFirst few rows:")
    print(dataset.head())