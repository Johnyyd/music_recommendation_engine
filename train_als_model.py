from pyspark.sql import SparkSession
from pyspark.ml.recommendation import ALS
import logging
import sys
from datetime import datetime
import os

# ========================================
# 1. Cấu hình logging
# ========================================
def setup_logging():
    """Cấu hình logging với rotation"""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"{log_dir}/training_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

setup_logging()

# ========================================
# 2. Khởi tạo Spark
# ========================================
spark = (
    SparkSession.builder
    .appName("Train_ALS_Model")
    .config("spark.sql.shuffle.partitions", "200")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

# ========================================
# 3. Đọc dữ liệu đã xử lý
# ========================================
try:
    node = "172.19.67.26" # "node1"
    parquet_path = f"hdfs://{node}:9000/data/mpd/parquet/"
    training_data = spark.read.parquet(parquet_path)
    
    # Validate dữ liệu
    row_count = training_data.count()
    if row_count == 0:
        raise ValueError("Training data is empty")
    
    logging.info(f"Loaded {row_count} interactions from {parquet_path}")
    logging.info(f"Data schema: {training_data.schema}")
    
except Exception as e:
    logging.error(f"Failed to load training data: {str(e)}")
    spark.stop()
    sys.exit(1)

# ========================================
# 4. Huấn luyện mô hình ALS implicit
# ========================================
als = ALS(
    userCol="playlist_idx",
    itemCol="track_idx",
    ratingCol="count",
    implicitPrefs=True,
    rank=100,
    regParam=0.05,
    alpha=20.0,
    maxIter=20,
    coldStartStrategy="drop",
    nonnegative=True
)

model = als.fit(training_data)

# ========================================
# 5. Lưu model và backup
# ========================================
try:
    # Lưu model chính
    model_path = f"hdfs://{node}:9000/models/als_implicit/"
    model.save(model_path)
    
    # Tạo backup với timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"hdfs://{node}:9000/models/backup/als_implicit_{timestamp}/"
    model.save(backup_path)
    
    logging.info(f"Model saved successfully to {model_path}")
    logging.info(f"Backup created at {backup_path}")
    
    # Log training metrics
    training_summary = {
        "timestamp": timestamp,
        "num_iterations": model.getMaxIter(),
        "rank": model.getRank(),
        "reg_param": model.getRegParam(),
        "alpha": model.getAlpha(),
        "num_blocks": training_data.rdd.getNumPartitions()
    }
    logging.info(f"Training summary: {training_summary}")
    
except Exception as e:
    logging.error(f"Failed to save model: {str(e)}")
    spark.stop()
    sys.exit(1)

spark.stop()
logging.info("Training pipeline completed successfully")
