from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, lit

# ========================================
# 1. Spark Session
# ========================================
spark = (
    SparkSession.builder
    .appName("ETL_Spotify_JSON_to_Parquet")
    .config("spark.sql.shuffle.partitions", "200")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

# ========================================
# 2. Đọc dữ liệu JSON
# ========================================

node = "172.19.67.26" # "node1"
raw_path = f"hdfs://{node}:9000/data/mqd/raw/"
parquet_path = f"hdfs://{node}:9000/data/mqd/parquet"

df_raw = spark.read.json(raw_path)

# ========================================
# 3. Chuẩn hóa dữ liệu
# ========================================
df_tracks = (
    df_raw
    .select(col("pid").alias("playlist_id"), explode("tracks").alias("track"))
    .select(
        col("playlist_id"),
        col("track.track_uri").alias("track_uri"),
        col("track.track_name").alias("track_name"),
        col("track.artist_name").alias("artist_name")
    )
    .withColumn("count", lit(1))
)

# ========================================
# 4. Tạo index cho playlist và track
# ========================================
playlist_indexer = (
    df_tracks.select("playlist_id").distinct().rdd.zipWithUniqueId()
    .toDF(["playlist_id", "playlist_idx"])
)
track_indexer = (
    df_tracks.select("track_uri").distinct().rdd.zipWithUniqueId()
    .toDF(["track_uri", "track_idx"])
)

# Join lại để tạo interaction table
df_interactions = (
    df_tracks
    .join(playlist_indexer, "playlist_id")
    .join(track_indexer, "track_uri")
    .select("playlist_idx", "track_idx", "count")
)

# ========================================
# 5. Lưu ra HDFS dưới dạng Parquet
# ========================================
df_interactions.write.mode("overwrite").parquet(parquet_path)
playlist_indexer.write.mode("overwrite").parquet(f"hdfs://{node}:9000/data/mpd/meta/playlist_indexer/")
track_indexer.write.mode("overwrite").parquet(f"hdfs://{node}:9000/data/mpd/meta/track_indexer/")

print("✅ ETL hoàn tất: dữ liệu Parquet & mapping đã sẵn sàng.")
spark.stop()
