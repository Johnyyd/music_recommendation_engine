from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf, expr
from pyspark.sql.types import StringType
from pyspark.ml.recommendation import ALSModel

# ========================================
# 1. Spark Session
# ========================================
spark = (
    SparkSession.builder
    .appName("Generate_Submission_File")
    .config("spark.sql.shuffle.partitions", "200")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

# ========================================
# 2. Đọc model & dữ liệu meta
# ========================================
node = "172.19.67.26" # "node1"
model_path = f"hdfs://{node}:9000/models/als_implicit/"
playlist_meta_path = f"hdfs://{node}:9000/data/mpd/meta/playlist_indexer/"
track_meta_path = f"hdfs://{node}:9000/data/mpd/meta/track_indexer/"

model = ALSModel.load(model_path)
playlist_indexer = spark.read.parquet(playlist_meta_path)
track_indexer = spark.read.parquet(track_meta_path)

# ========================================
# 3. Sinh top 500 gợi ý cho mỗi playlist
# ========================================
recommendations = model.recommendForAllUsers(500)

# Chuyển array recommendations → list track_idx
recommendations = recommendations.select(
    col("playlist_idx"),
    expr("transform(recommendations, x -> x.track_idx)").alias("recommended_tracks")
)

# Join với playlist_indexer để lấy playlist_id
df_submit = recommendations.join(playlist_indexer, on="playlist_idx")

# Join với track_indexer để map idx → URI
track_dict = track_indexer.collect()
track_map = {row["track_idx"]: row["track_uri"] for row in track_dict}

@udf(returnType=StringType())
def map_to_uri(track_list):
    if not track_list:
        return ""
    uris = [track_map.get(int(i), "") for i in track_list]
    return ",".join([u for u in uris if u])

df_final = df_submit.withColumn("recommended_track_uris", map_to_uri(col("recommended_tracks")))

# ========================================
# 4. Ghi submission.csv
# ========================================
output_path = f"hdfs://{node}:9000/output/submission/"
df_final.select("playlist_id", "recommended_track_uris").write.mode("overwrite").option("header", True).csv(output_path)

print("✅ Gợi ý hoàn tất. File submission.csv đã được lưu vào HDFS.")
spark.stop()
