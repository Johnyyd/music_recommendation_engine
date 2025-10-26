from pyspark.sql import SparkSession
import logging
import sys
from datetime import datetime
import os

def setup_logging():
    """Cấu hình logging"""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"{log_dir}/split_data_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

def split_data(spark, input_path, train_path, test_path, test_ratio=0.1):
    """
    Split data thành training và test sets
    """
    try:
        # Đọc dữ liệu
        data = spark.read.parquet(input_path)
        logging.info(f"Loaded {data.count()} records from {input_path}")
        
        # Split theo playlist
        playlists = data.select("playlist_idx").distinct()
        train_playlists, test_playlists = playlists.randomSplit(
            [1 - test_ratio, test_ratio],
            seed=42
        )
        
        # Lưu training data
        train_data = data.join(
            train_playlists,
            on="playlist_idx",
            how="inner"
        )
        train_data.write.mode("overwrite").parquet(train_path)
        
        # Lưu test data
        test_data = data.join(
            test_playlists,
            on="playlist_idx",
            how="inner"
        )
        test_data.write.mode("overwrite").parquet(test_path)
        
        # Log statistics
        train_count = train_data.count()
        test_count = test_data.count()
        logging.info(f"Training set: {train_count} records")
        logging.info(f"Test set: {test_count} records")
        logging.info(f"Split ratio: {test_count/(train_count + test_count):.2f}")
        
    except Exception as e:
        logging.error(f"Error splitting data: {str(e)}")
        raise e

if __name__ == "__main__":
    setup_logging()
    
    try:
        # Initialize Spark
        spark = (SparkSession.builder
                .appName("Split_Train_Test")
                .config("spark.sql.shuffle.partitions", "200")
                .getOrCreate())
        
        spark.sparkContext.setLogLevel("WARN")
        
        # Paths
        node = "172.19.67.26"
        input_path = f"hdfs://{node}:9000/data/mpd/parquet/"
        train_path = f"hdfs://{node}:9000/data/mpd/train/"
        test_path = f"hdfs://{node}:9000/data/mpd/test/"
        
        # Split data
        split_data(spark, input_path, train_path, test_path)
        logging.info("Data split completed successfully")
        
    except Exception as e:
        logging.error(f"Pipeline failed: {str(e)}")
        sys.exit(1)
        
    finally:
        spark.stop()