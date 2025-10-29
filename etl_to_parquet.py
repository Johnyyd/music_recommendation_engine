from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, lit, dense_rank
from pyspark.sql.window import Window
import os

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

node = os.getenv("HDFS_NODE", "172.19.67.26")  # "node1"
raw_path = f"hdfs://{node}:9000/data/mqd/raw/"
parquet_path = f"hdfs://{node}:9000/data/mqd/parquet/"

df_raw = spark.read.option("multiLine", "true").json(raw_path)

# ========================================
# 3. Chuẩn hóa dữ liệu
# ========================================
df_tracks = (
    df_raw
    .select(explode("playlists").alias("pl"))
    .select(col("pl.pid").alias("playlist_id"), explode(col("pl.tracks")).alias("track"))
    .select(
        col("playlist_id"),
        col("track.track_uri").alias("track_uri"),
        col("track.track_name").alias("track_name"),
        col("track.artist_name").alias("artist_name")
    )
    .withColumn("count", lit(1))
    .filter(col("playlist_id").isNotNull())
    .filter(col("track_uri").isNotNull())
    .filter(col("track_uri").startswith("spotify:track:"))
    .dropDuplicates(["playlist_id", "track_uri"]) 
)

# ========================================
# 4. Tạo index cho playlist và track
# ========================================
playlist_indexer = (
    df_tracks
    .select("playlist_id").distinct()
    .withColumn("playlist_idx", dense_rank().over(Window.orderBy(col("playlist_id"))) - 1)
)
track_indexer = (
    df_tracks
    .select("track_uri").distinct()
    .withColumn("track_idx", dense_rank().over(Window.orderBy(col("track_uri"))) - 1)
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
playlist_indexer.write.mode("overwrite").parquet(f"hdfs://{node}:9000/data/mqd/meta/playlist_indexer/")
track_indexer.write.mode("overwrite").parquet(f"hdfs://{node}:9000/data/mqd/meta/track_indexer/")

print("✅ ETL hoàn tất: dữ liệu Parquet & mapping đã sẵn sàng.")
spark.stop()
