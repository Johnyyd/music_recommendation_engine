from pyspark.sql import SparkSession
from pyspark.sql.functions import col, expr, udf, explode, rand, flatten, collect_list
from pyspark.sql.types import ArrayType, StringType, FloatType
import numpy as np
import os

# --- IMPORT CÁC HÀM TỔNG HỢP ---
from pyspark.sql.functions import avg, count, stddev, min, max

def calculate_map(predictions, actual, k=500):
    """
    Tính Mean Average Precision cho các recommendations
    """
    if not predictions or not actual:
        return 0.0
    
    predictions = predictions[:k]
    ap = 0.0
    hits = 0
    
    for i, pred in enumerate(predictions, 1):
        if pred in actual:
            hits += 1
            ap += hits / i
    
    return ap / min(len(actual), k) if hits > 0 else 0.0

def evaluate_model(spark, model_path, test_data_path, track_meta_path):
    """
    Đánh giá mô hình bằng Mean Average Precision
    """
    # Load model và test data
    from pyspark.ml.recommendation import ALSModel
    model = ALSModel.load(model_path)
    test_data = spark.read.parquet(test_data_path)
    track_meta = spark.read.parquet(track_meta_path)

    # --- SỬA LỖI DATA SKEW (SALTING) ---
    N_SALT = 50 # Tăng số này nếu vẫn bị skew (ví dụ: 20)

    # 1. Tạo Ground Truth (Đã Salted)
    test_truth_idx_salted = (
        test_data
        .withColumn("salt", (rand() * N_SALT).cast("int"))
        .groupBy("playlist_idx", "salt")
        .agg(expr("collect_list(track_idx) as partial_tracks"))
    )
    test_truth_idx = (
        test_truth_idx_salted
        .groupBy("playlist_idx")
        .agg(flatten(collect_list("partial_tracks")).alias("actual_track_idxs"))
    )
    
    # Generate recommendations
    recommendations = model.recommendForAllUsers(500)
    recommendations = recommendations.select(
        col("playlist_idx"),
        expr("transform(recommendations, x -> x.track_idx)").alias("recommended_track_idxs")
    )
    
    # Join predictions với ground truth
    evaluation_data_idx = recommendations.join(test_truth_idx, "playlist_idx")
    
    # --- PHẦN CODE SỬA LẠI (LOẠI BỎ .COLLECT() VÀ THÊM SALTING) ---

    # 2. Explode + Join + GroupBy (Đã Salted) cho predicted_tracks
    predicted_with_uri_salted = (
        evaluation_data_idx.select("playlist_idx", "recommended_track_idxs")
        .withColumn("track_idx", explode(col("recommended_track_idxs")))
        .join(track_meta, "track_idx") # Join với track_meta để lấy URI
        .withColumn("salt", (rand() * N_SALT).cast("int"))
        .groupBy("playlist_idx", "salt")
        .agg(expr("collect_list(track_uri) as partial_tracks"))
    )
    predicted_with_uri = (
        predicted_with_uri_salted
        .groupBy("playlist_idx")
        .agg(flatten(collect_list("partial_tracks")).alias("predicted_tracks"))
    )
    
    # 3. Explode + Join + GroupBy (Đã Salted) cho actual_tracks
    actual_with_uri_salted = (
        evaluation_data_idx.select("playlist_idx", "actual_track_idxs")
        .withColumn("track_idx", explode(col("actual_track_idxs")))
        .join(track_meta, "track_idx") # Join với track_meta để lấy URI
        .withColumn("salt", (rand() * N_SALT).cast("int"))
        .groupBy("playlist_idx", "salt")
        .agg(expr("collect_list(track_uri) as partial_tracks"))
    )
    actual_with_uri = (
        actual_with_uri_salted
        .groupBy("playlist_idx")
        .agg(flatten(collect_list("partial_tracks")).alias("actual_tracks"))
    )

    # 4. Join hai bảng (đã map sang URI) lại với nhau
    evaluation_data_final = predicted_with_uri.join(actual_with_uri, "playlist_idx")
    
    # 5. Tính MAP cho từng hàng
    map_udf = udf(lambda pred, actual: calculate_map(pred, actual, k=500), FloatType())
    
    map_scores_df = evaluation_data_final.withColumn(
        "map_score",
        map_udf(col("predicted_tracks"), col("actual_tracks"))
    )

    # 6. Tính toán các chỉ số trực tiếp trong Spark (Không dùng .collect())
    metrics_df = map_scores_df.select(
        avg("map_score").alias("mean_ap"),
        count("map_score").alias("num_playlists"),
        stddev("map_score").alias("std_dev"),
        min("map_score").alias("min_ap"),
        max("map_score").alias("max_ap")
    ).first() # .first() an toàn vì nó chỉ thu thập 1 hàng kết quả

    # --- KẾT THÚC PHẦN CODE SỬA LẠI ---
    
    # Calculate overall MAP
    mean_ap = metrics_df["mean_ap"]
    print(f"Mean Average Precision @ 500: {mean_ap:.4f}")
    
    # Additional metrics
    print("\nAdditional Metrics:")
    print(f"Number of playlists evaluated: {metrics_df['num_playlists']}")
    # Lưu ý: Tính median yêu cầu kỹ thuật phức tạp hơn (approxQuantile),
    # nhưng các chỉ số này đã đủ để đánh giá mà không gây OOM.
    print(f"Standard deviation: {metrics_df['std_dev']:.4f}")
    print(f"Min AP: {metrics_df['min_ap']:.4f}")
    print(f"Max AP: {metrics_df['max_ap']:.4f}")
    
    return mean_ap

if __name__ == "__main__":
    spark = (SparkSession.builder
            .appName("Evaluate_ALS_Model")
            .config("spark.sql.shuffle.partitions", "200")
            .getOrCreate())
    spark.sparkContext.setLogLevel("WARN")
    node = os.getenv("HDFS_NODE", "172.19.67.26")
    model_path = f"hdfs://{node}:9000/model/als_implicit/"
    test_data_path = f"hdfs://{node}:9000/data/mqd/test/"
    track_meta_path = f"hdfs://{node}:9000/data/mqd/meta/track_indexer/"
    evaluate_model(spark, model_path, test_data_path, track_meta_path)
    spark.stop()