from pyspark.sql import SparkSession
from pyspark.sql.functions import col, expr, explode, collect_list, concat_ws
from pyspark.ml.recommendation import ALSModel
import os

# 1. Spark Session
spark = (
    SparkSession.builder
    .appName("Generate_Submission_File")
    .config("spark.sql.shuffle.partitions", "200")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

# 2. Đọc model & dữ liệu meta
node = os.getenv("HDFS_NODE", "192.168.10.1")
model_path = f"hdfs://{node}:9000/model/als_implicit/"
playlist_meta_path = f"hdfs://{node}:9000/data/mqd/meta/playlist_indexer/"
track_meta_path = f"hdfs://{node}:9000/data/mqd/meta/track_indexer/"

model = ALSModel.load(model_path)
playlist_indexer = spark.read.parquet(playlist_meta_path)
track_indexer = spark.read.parquet(track_meta_path)

# 3. Sinh top 500 gợi ý cho mỗi playlist
recommendations = model.recommendForAllUsers(500)

recommendations = recommendations.select(
    col("playlist_idx"),
    expr("transform(recommendations, x -> x.track_idx)").alias("recommended_track_idxs")
)

# --- PHẦN CODE SỬA LỖI OOM (LOẠI BỎ .COLLECT() VÀ UDF) ---

# 4. Dùng JOIN thay vì .collect() + UDF
# Explode mảng track_idx
df_exploded = recommendations.select(
    col("playlist_idx"),
    explode(col("recommended_track_idxs")).alias("track_idx")
)

# Join với track_indexer để lấy track_uri
df_with_uri = df_exploded.join(track_indexer, on="track_idx", how="left")

# GroupBy lại để tạo mảng track_uri
df_grouped = (
    df_with_uri
    .groupBy("playlist_idx")
    .agg(collect_list("track_uri").alias("track_uri_list"))
)

# Ghép mảng thành chuỗi_string
df_string = df_grouped.withColumn(
    "recommended_track_uris",
    concat_ws(",", col("track_uri_list"))
)

# 5. Join với playlist_indexer để lấy playlist_id
df_final = df_string.join(playlist_indexer, on="playlist_idx")

# --- KẾT THÚC PHẦN SỬA LỖI ---

# 6. Ghi submission.csv
output_path = f"hdfs://{node}:9000/output/submission/"
(
    df_final.select("playlist_id", "recommended_track_uris")
    .write.mode("overwrite")
    .option("header", True)
    .csv(output_path)
)

local_output_path = "output/submission/"
(
    df_final.select("playlist_id", "recommended_track_uris")
    .coalesce(1)
    .write.mode("overwrite")
    .option("header", True)
    .csv(local_output_path)
)

print("✅ Gợi ý hoàn tất. File submission.csv đã được lưu vào HDFS.")
spark.stop()