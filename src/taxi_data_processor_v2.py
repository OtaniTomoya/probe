import json
import pandas as pd
import numpy as np
import os
from datetime import datetime
from glob import glob
from tqdm import tqdm

class TaxiDatasetCreatorV2:
    def __init__(self, json_dir, change_flag_csv_path, stop_speed_threshold=10.0):
        """
        タクシーデータセット作成クラス（改良版）
        - 加速度データと基本データを分離
        - 停車判定に基づくラベリング
        
        Args:
            json_dir: JSONファイルが格納されているディレクトリ
            change_flag_csv_path: change_flag_filled0.csvのパス (必須)
            stop_speed_threshold: 停車判定速度しきい値 (km/h)
        """
        self.json_dir = json_dir
        self.change_flag_csv_path = change_flag_csv_path
        self.stop_speed_threshold = stop_speed_threshold
        
        # ステータス変化の定義（get_on/get_offイベント検出用）
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
        """タイムスタンプを解析"""
        base_date = datetime.strptime(record_datetime, "%Y%m%d%H%M%S")
        timestamp_ms = int(timestamp_str)
        return pd.Timestamp(timestamp_ms, unit='ms')
    
    def extract_array_values(self, array_str):
        """配列文字列から全ての値を抽出"""
        try:
            values = json.loads(array_str)
            return [float(v) for v in values]
        except:
            return []
    
    def process_json_file(self, json_path):
        """
        単一のJSONファイルを処理して基本データと加速度データを分離
        
        Returns:
            tuple: (基本データDataFrame, 加速度データDataFrame)
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # IMEIを取得
            imei = data.get('imei', '')
            record_datetime = data.get('recordDateTime', '')
            
            if 'data' not in data or not data['data']:
                return pd.DataFrame(), pd.DataFrame()
            
            # 基本データと加速度データを別々に処理
            base_rows = []
            accel_rows = []
            
            for record in data['data']:
                timestamp = self.parse_timestamp(record_datetime, record.get('timeStamp', '0'))
                speed = float(record.get('speed', 0))
                
                # 加速度・角速度データを取得
                acc_x = self.extract_array_values(record.get('accX', '[]'))
                acc_y = self.extract_array_values(record.get('accY', '[]'))
                acc_z = self.extract_array_values(record.get('accZ', '[]'))
                rad_x = self.extract_array_values(record.get('radX', '[]'))
                rad_y = self.extract_array_values(record.get('radY', '[]'))
                rad_z = self.extract_array_values(record.get('radZ', '[]'))
                
                # ウインカー情報
                try:
                    right_blinker_array = json.loads(record.get('vehicleInformationRightBlinker', '[0]'))
                    left_blinker_array = json.loads(record.get('vehicleInformationLeftBlinker', '[0]'))
                    right_blinker = 1 if sum(right_blinker_array) != 0 else 0
                    left_blinker = 1 if sum(left_blinker_array) != 0 else 0
                except:
                    right_blinker = 0
                    left_blinker = 0
                
                # GPSデータ
                latitude = float(record.get('latitude', 0))
                longitude = float(record.get('longitude', 0))
                altitude = float(record.get('altitude', 0))
                heading = float(record.get('heading', 0))
                
                # 基本データ（タイムスタンプごとに1行）
                base_row = {
                    'timestamp': timestamp,
                    'speed': speed,
                    'latitude': latitude,
                    'longitude': longitude,
                    'right_blinker': right_blinker,
                    'left_blinker': left_blinker
                }
                base_rows.append(base_row)
                
                # 加速度データ（各サンプルごとに1行）
                max_length = max(len(acc_x), len(acc_y), len(acc_z), 
                               len(rad_x), len(rad_y), len(rad_z), 1)
                
                # 各サンプルに対して100Hz（0.01秒刻み）でタイムスタンプを設定
                for i in range(max_length):
                    # 各サンプルのタイムスタンプを計算（10ミリ秒ずつ増加）
                    sample_timestamp = timestamp + pd.Timedelta(milliseconds=i * 10)
                    
                    accel_row = {
                        'timestamp': sample_timestamp,
                        'acc_x': acc_x[i] if i < len(acc_x) else np.nan,
                        'acc_y': acc_y[i] if i < len(acc_y) else np.nan,
                        'acc_z': acc_z[i] if i < len(acc_z) else np.nan,
                        'rad_x': rad_x[i] if i < len(rad_x) else np.nan,
                        'rad_y': rad_y[i] if i < len(rad_y) else np.nan,
                        'rad_z': rad_z[i] if i < len(rad_z) else np.nan
                    }
                    accel_rows.append(accel_row)
            
            return pd.DataFrame(base_rows), pd.DataFrame(accel_rows)
            
        except Exception as e:
            print(f"Error processing {json_path}: {str(e)}")
            return pd.DataFrame(), pd.DataFrame()
    
    def identify_stop_segments(self, df):
        """
        停車区間を識別
        停車条件：10km/h未満で10秒間走行し、かつ0km/hの瞬間があること
        """
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # 低速フラグ（10km/h未満）
        df['is_low_speed'] = df['speed'] < self.stop_speed_threshold
        
        # 完全停止フラグ（0km/h）
        df['is_zero_speed'] = df['speed'] == 0
        
        # 停車区間にセグメントIDを割り当て
        df['stop_segment'] = 0
        df['is_stopped'] = 0
        segment_id = 0
        
        # 全データを時系列順に処理（車両IDがないので全データを一つのタイムラインとして扱う）
        car_data = df.copy()
        
        # 低速区間を検出（時間的に連続している区間のみ）
        low_speed_groups = []
        in_low_speed = False
        start_idx = None
        
        for i in range(len(car_data)):
            row = car_data.iloc[i]
            
            # 前のレコードとの時間差をチェック
            if i > 0:
                time_gap = (row['timestamp'] - car_data.iloc[i-1]['timestamp']).total_seconds()
                # 60秒以上のギャップがある場合は新しい区間として扱う
                if time_gap > 60 and in_low_speed:
                    # 現在の低速区間を終了
                    if start_idx is not None:
                        low_speed_groups.append((start_idx, i))
                    in_low_speed = False
                    start_idx = None
            
            if row['is_low_speed'] and not in_low_speed:
                # 低速区間開始
                in_low_speed = True
                start_idx = i
            elif not row['is_low_speed'] and in_low_speed:
                # 低速区間終了
                in_low_speed = False
                if start_idx is not None:
                    low_speed_groups.append((start_idx, i))
                    start_idx = None
        
        # 最後まで低速だった場合
        if in_low_speed and start_idx is not None:
            low_speed_groups.append((start_idx, len(car_data)))
        
        # 各低速区間について停車判定
        for start, end in low_speed_groups:
            segment_data = car_data.iloc[start:end]
            
            if len(segment_data) >= 2:  # 最低2レコード必要
                # 時間差を計算（秒）
                time_diff = (segment_data.iloc[-1]['timestamp'] - segment_data.iloc[0]['timestamp']).total_seconds()
                
                # 0km/hの瞬間があるかチェック
                has_zero_speed = segment_data['is_zero_speed'].any()
                
                # 10秒以上かつ0km/hの瞬間がある場合は停車
                if time_diff >= 10.0 and has_zero_speed:
                    segment_id += 1
                    # この区間のインデックスを取得
                    segment_indices = segment_data.index
                    df.loc[segment_indices, 'stop_segment'] = segment_id
                    df.loc[segment_indices, 'is_stopped'] = 1
        
        # 一時的なカラムを削除
        df = df.drop(columns=['is_low_speed', 'is_zero_speed'])
        
        return df
    
    def apply_event_labels(self, df, change_flag_df):
        """イベントラベルを適用（車両ID無しでタイムスタンプのみでマッチング）"""
        # タイムスタンプをミリ秒に変換
        df['timestamp_ms'] = df['timestamp'].astype(np.int64) // 10**6
        
        # change_flagデータとマージ（タイムスタンプのみでマッチング）
        df = pd.merge(
            df,
            change_flag_df[['time_stamp', 'status_management', 'change_flag']],
            left_on='timestamp_ms',
            right_on='time_stamp',
            how='left'
        )
        
        # ステータス変化を検出（全体で時系列順）
        df = df.sort_values('timestamp').reset_index(drop=True)
        df['status_change'] = (df['status_management'].astype(str).str.zfill(2) + 
                              df['status_management'].shift(1).astype(str).str.zfill(2))
        
        # イベントタイプを識別
        df['event_type'] = 0  # 0: no event
        df.loc[df['change_flag'] == 1, 'event_type'] = 1  # change_flagベース
        df.loc[df['status_change'].isin(self.get_on_map), 'event_type'] = 1  # 乗車
        df.loc[df['status_change'].isin(self.get_off_map), 'event_type'] = 2  # 降車
        
        return df
    
    def label_stop_segments(self, df):
        """停車区間にラベルを付ける（車両ID無しで全体のタイムラインで処理）"""
        df['label'] = 0  # デフォルト: 0 (通常走行)
        
        # 全データを時系列順に処理
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # イベントがある行を取得
        events = df[df['event_type'] > 0].copy()
        
        for idx, event in events.iterrows():
            event_type = event['event_type']
            event_time = event['timestamp']
            
            if event_type == 1:  # 乗車イベント
                # 直前の停車区間を探す
                before_event = df[df['timestamp'] < event_time]
                if not before_event.empty:
                    # 最も近い停車区間を取得
                    stopped_before = before_event[before_event['is_stopped'] == 1]
                    if not stopped_before.empty:
                        last_stop_segment = stopped_before.iloc[-1]['stop_segment']
                        if last_stop_segment > 0:
                            # その停車区間全体にラベル1を付ける
                            segment_mask = df['stop_segment'] == last_stop_segment
                            df.loc[segment_mask, 'label'] = 1
            
            elif event_type == 2:  # 降車イベント
                # 直後の停車区間を探す
                after_event = df[df['timestamp'] > event_time]
                if not after_event.empty:
                    # 最も近い停車区間を取得
                    stopped_after = after_event[after_event['is_stopped'] == 1]
                    if not stopped_after.empty:
                        next_stop_segment = stopped_after.iloc[0]['stop_segment']
                        if next_stop_segment > 0:
                            # その停車区間全体にラベル2を付ける
                            segment_mask = df['stop_segment'] == next_stop_segment
                            df.loc[segment_mask, 'label'] = 2
        
        # 不要なカラムを削除
        columns_to_drop = ['timestamp_ms', 'time_stamp', 'status_management', 
                          'change_flag', 'status_change', 'stop_change', 
                          'stop_segment', 'event_type']
        df = df.drop(columns=[col for col in columns_to_drop if col in df.columns])
        
        return df
    
    def create_dataset(self, max_files=None):
        """
        全てのJSONファイルを処理してデータセットを作成
        
        Args:
            max_files: 処理する最大ファイル数（Noneの場合は全て）
        
        Returns:
            tuple: (基本データDataFrame, 加速度データDataFrame)
        """
        json_files = glob(os.path.join(self.json_dir, "*.json"))
        
        if not json_files:
            raise ValueError(f"No JSON files found in {self.json_dir}")
        
        if max_files is not None:
            json_files = json_files[:max_files]
        
        print(f"Processing {len(json_files)} JSON files")
        
        # データを収集
        all_base_data = []
        all_accel_data = []
        
        for json_file in tqdm(json_files, desc="Processing JSON files"):
            base_df, accel_df = self.process_json_file(json_file)
            if not base_df.empty:
                all_base_data.append(base_df)
            if not accel_df.empty:
                all_accel_data.append(accel_df)
        
        if not all_base_data:
            raise ValueError("No data extracted from JSON files")
        
        # データを結合
        base_df = pd.concat(all_base_data, ignore_index=True)
        accel_df = pd.concat(all_accel_data, ignore_index=True) if all_accel_data else pd.DataFrame()
        
        print(f"Base data records: {len(base_df)}")
        print(f"Acceleration data records: {len(accel_df)}")
        
        # 停車区間を識別
        base_df = self.identify_stop_segments(base_df)
        
        # change_flagデータを読み込み
        change_flag_df = self.load_change_flag_data()
        
        # イベントラベルを適用
        base_df = self.apply_event_labels(base_df, change_flag_df)
        
        # 停車区間にラベルを付ける
        base_df = self.label_stop_segments(base_df)
        
        # 時間順にソート
        base_df = base_df.sort_values('timestamp').reset_index(drop=True)
        accel_df = accel_df.sort_values('timestamp').reset_index(drop=True)
        
        return base_df, accel_df
    
    def save_dataset(self, output_prefix, max_files=None):
        """
        データセットを作成して保存
        
        Args:
            output_prefix: 出力ファイルのプレフィックス
            max_files: 処理する最大ファイル数（Noneの場合は全て）
        """
        # データセットを作成
        base_df, accel_df = self.create_dataset(max_files=max_files)
        
        # 基本データを保存
        base_df.to_csv(f"{output_prefix}_base.csv", index=False)
        print(f"Base dataset saved: {output_prefix}_base.csv ({len(base_df)} records)")
        
        # 加速度データを保存
        if not accel_df.empty:
            accel_df.to_csv(f"{output_prefix}_accel.csv", index=False)
            print(f"Acceleration dataset saved: {output_prefix}_accel.csv ({len(accel_df)} records)")
        
        # ラベルの分布を表示
        print("\nLabel distribution in base data:")
        print(base_df['label'].value_counts().sort_index())
        
        # 停車統計を表示
        print(f"\nStop statistics:")
        print(f"Total stopped records: {(base_df['is_stopped'] == 1).sum()}")
        print(f"Stop percentage: {(base_df['is_stopped'] == 1).sum() / len(base_df) * 100:.2f}%")
        
        return base_df, accel_df


# 使用例
if __name__ == "__main__":
    # パラメータ設定
    json_directory = "./json"
    change_flag_csv = "./data/change_flag_filled0.csv"
    output_path = "./outputs/taxi_dataset_v2"
    
    # change_flag_filled0.csvの存在確認
    if not os.path.exists(change_flag_csv):
        raise FileNotFoundError(f"Required file not found: {change_flag_csv}")
    
    # データセット作成（デモ用に最初の100ファイルのみ）
    creator = TaxiDatasetCreatorV2(json_directory, change_flag_csv, stop_speed_threshold=10.0)
    base_df, accel_df = creator.save_dataset(output_path, max_files=100)
    
    # サンプルデータを表示
    print("\nBase data sample:")
    print(base_df.head())
    
    if not accel_df.empty:
        print("\nAcceleration data sample:")
        print(accel_df.head())