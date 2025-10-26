from pyspark.sql import SparkSession
from pyspark.ml.recommendation import ALS

# ========================================
# 1. Khởi tạo Spark
# ========================================
spark = (
    SparkSession.builder
    .appName("Train_ALS_Model")
    .config("spark.sql.shuffle.partitions", "200")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

# ========================================
# 2. Đọc dữ liệu đã xử lý
# ========================================
node = "172.19.67.26" # "node1"
parquet_path = f"hdfs://{node}:9000/data/mpd/parquet/"
training_data = spark.read.parquet(parquet_path)

# ========================================
# 3. Huấn luyện mô hình ALS implicit
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
# 4. Lưu model lên HDFS
# ========================================
model.save(f"hdfs://{node}:9000/models/als_implicit/")
print("✅ Huấn luyện ALS hoàn tất và model đã được lưu lên HDFS.")
spark.stop()
