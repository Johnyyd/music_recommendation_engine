from pyspark.sql import SparkSession
from pyspark.sql.functions import col, size, expr
import numpy as np

def calculate_map(predictions, actual, k=500):
    """
    Tính Mean Average Precision cho các recommendations
    
    Args:
        predictions: List các track_uri được gợi ý
        actual: List các track_uri thực tế
        k: Số lượng recommendations để xét (default: 500)
    
    Returns:
        MAP score
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
    
    # Tạo ground truth dictionary
    test_truth = (test_data.groupBy("playlist_idx")
                 .agg(expr("collect_list(track_uri) as actual_tracks")))
    
    # Generate recommendations
    recommendations = model.recommendForAllUsers(500)
    recommendations = recommendations.select(
        col("playlist_idx"),
        expr("transform(recommendations, x -> x.track_idx)").alias("recommended_tracks")
    )
    
    # Convert track_idx to track_uri
    track_dict = {row["track_idx"]: row["track_uri"] 
                 for row in track_meta.collect()}
    
    def convert_to_uris(track_idxs):
        return [track_dict.get(idx, "") for idx in track_idxs]
    
    convert_udf = spark.udf.register("convert_to_uris", 
                                   convert_to_uris, 
                                   "array<string>")
    
    predictions = recommendations.withColumn(
        "predicted_tracks",
        convert_udf(col("recommended_tracks"))
    )
    
    # Join predictions with ground truth
    evaluation_data = predictions.join(test_truth, "playlist_idx")
    
    # Calculate MAP for each playlist
    map_scores = evaluation_data.rdd.map(
        lambda row: calculate_map(
            row["predicted_tracks"],
            row["actual_tracks"]
        )
    ).collect()
    
    # Calculate overall MAP
    mean_ap = np.mean(map_scores)
    print(f"Mean Average Precision @ 500: {mean_ap:.4f}")
    
    # Additional metrics
    print("\nAdditional Metrics:")
    print(f"Number of playlists evaluated: {len(map_scores)}")
    print(f"Median AP: {np.median(map_scores):.4f}")
    print(f"Standard deviation: {np.std(map_scores):.4f}")
    print(f"Min AP: {np.min(map_scores):.4f}")
    print(f"Max AP: {np.max(map_scores):.4f}")
    
    return mean_ap

if __name__ == "__main__":
    # Initialize Spark
    spark = (SparkSession.builder
            .appName("Evaluate_ALS_Model")
            .config("spark.sql.shuffle.partitions", "200")
            .getOrCreate())
    
    spark.sparkContext.setLogLevel("WARN")
    
    # Paths
    node = "172.19.67.26"
    model_path = f"hdfs://{node}:9000/models/als_implicit/"
    test_data_path = f"hdfs://{node}:9000/data/mpd/test/"
    track_meta_path = f"hdfs://{node}:9000/data/mpd/meta/track_indexer/"
    
    # Evaluate
    map_score = evaluate_model(spark, model_path, test_data_path, track_meta_path)
    spark.stop()