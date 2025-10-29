from pyspark.sql import SparkSession
from pyspark.ml.recommendation import ALS
import logging
import sys
from datetime import datetime
import os
from pyspark.sql.functions import col
from pyspark.sql.types import IntegerType, FloatType
from pyspark.storagelevel import StorageLevel

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
    .config("spark.network.timeout", "600s")
    .config("spark.executor.heartbeatInterval", "30s")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

# ========================================
# 3. Đọc dữ liệu đã xử lý
# ========================================
try:
    node = os.getenv("HDFS_NODE", "172.19.67.26")  # "node1"
    parquet_path = f"hdfs://{node}:9000/data/mqd/parquet/"
    training_data = spark.read.parquet(parquet_path)
    
    # Sanitize schema and values
    training_data = (
        training_data
        .dropna(subset=["playlist_idx", "track_idx", "count"]) 
        .withColumn("playlist_idx", col("playlist_idx").cast(IntegerType()))
        .withColumn("track_idx", col("track_idx").cast(IntegerType()))
        .withColumn("count", col("count").cast(FloatType()))
    )
    
    # Repartition and persist to stabilize shuffles
    training_data = training_data.repartition(64, "playlist_idx").persist(StorageLevel.MEMORY_AND_DISK)
    
    # Set checkpoint directory to HDFS to prevent lineage bloat
    spark.sparkContext.setCheckpointDir(f"hdfs://{node}:9000/tmp/spark_checkpoints")
    
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
    rank=32,
    regParam=0.08,
    alpha=20.0,
    maxIter=10,
    coldStartStrategy="drop",
    nonnegative=True,
    numUserBlocks=16,
    numItemBlocks=16,
    seed=42
)

model = als.fit(training_data)

# ========================================
# 5. Lưu model và backup
# ========================================
try:
    # Lưu model chính
    model_path = f"hdfs://{node}:9000/model/als_implicit/"
    model.save(model_path)
    
    # Tạo backup với timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"hdfs://{node}:9000/model/backup/als_implicit_{timestamp}/"
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
