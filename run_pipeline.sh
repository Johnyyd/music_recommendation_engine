#!/bin/bash
set -e  # Thoát nếu có lỗi

# Cấu hình
node="172.19.67.26" # SỬ DỤNG IP MASTER để truy cập HDFS
master_url="spark://172.19.67.26:7077" # SỬ DỤNG IP MASTER để Master lắng nghe
timestamp=$(date +%Y%m%d_%H%M%S)
log_dir="logs"
log_file="${log_dir}/pipeline_${timestamp}.log"

# Tham số Executor (Tối ưu hóa cho 2 node)
NUM_EXECUTORS=2        
EXECUTOR_CORES=2       
EXECUTOR_MEMORY="3g"   
DRIVER_MEMORY="5g"     
SHUFFLE_PARTITIONS=64

# ========================================
# KIỂM TRA & TẠO THƯ MỤC
# ========================================

# Tạo thư mục logs cục bộ
mkdir -p $log_dir

# Đảm bảo thư mục tạm cho Spark tồn tại trên cục bộ
mkdir -p /tmp/spark || true

# Tạo tất cả các thư mục HDFS cần thiết cho dữ liệu, model, và checkpoints
log "--- Đang kiểm tra và tạo các thư mục HDFS cần thiết ---"
hdfs dfs -mkdir -p /data/mqd/raw || true
hdfs dfs -mkdir -p /data/mqd/parquet || true
hdfs dfs -mkdir -p /data/mqd/meta/playlist_indexer || true
hdfs dfs -mkdir -p /data/mqd/meta/track_indexer || true
hdfs dfs -mkdir -p /data/mqd/train || true
hdfs dfs -mkdir -p /data/mqd/test || true
hdfs dfs -mkdir -p /data/mqd/backup || true
hdfs dfs -mkdir -p /model/backup || true
hdfs dfs -mkdir -p /tmp/spark_checkpoints || true

# ========================================
# BẮT ĐẦU PIPELINE
# ========================================

# Hàm log
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$log_file"
}

# Hàm kiểm tra exit code
check_status() {
    if [ $? -ne 0 ]; then
        log "❌ ERROR: Step $1 failed"
        exit 1
    fi
}

# Backup dữ liệu hiện có
log "=== [0/5] Backing up existing data ==="
# Lưu ý: Lệnh này đã bao gồm kiểm tra thư mục.
hdfs dfs -test -d /data/mqd/parquet && {
    backup_dir="/data/mqd/backup/parquet_${timestamp}"
    hdfs dfs -mv /data/mqd/parquet $backup_dir
    log "✓ Backed up parquet data to $backup_dir"
} || log "No existing parquet data to backup"
check_status "Backup"

# Pipeline chính
log "=== [1/5] ETL JSON → Parquet ==="
HDFS_NODE="$node" spark-submit \
  --master "$master_url" \
  --conf spark.sql.shuffle.partitions=$SHUFFLE_PARTITIONS \
  /mnt/c/LUUDULIEU/CODE/github/music_recommendation_engine/etl_to_parquet.py
check_status "ETL"

log "=== [2/5] Split Train/Test Data ==="
HDFS_NODE="$node" spark-submit \
  --master "$master_url" \
  --conf spark.sql.shuffle.partitions=$SHUFFLE_PARTITIONS \
  /mnt/c/LUUDULIEU/CODE/github/music_recommendation_engine/split_train_test.py
check_status "Data Split"

log "=== [3/5] Train ALS Model ==="
HDFS_NODE="$node" spark-submit \
  --master "$master_url" \
  --num-executors $NUM_EXECUTORS \
  --executor-cores $EXECUTOR_CORES \
  --executor-memory $EXECUTOR_MEMORY \
  --driver-memory $DRIVER_MEMORY \
  --conf spark.driver.maxResultSize="2g" \
  --conf spark.sql.shuffle.partitions=64 \
  --conf spark.default.parallelism=64 \
  --conf spark.local.dir=/tmp/spark \
  /mnt/c/LUUDULIEU/CODE/github/music_recommendation_engine/train_als_model.py
check_status "Training"

log "=== [4/5] Evaluate Model ==="
HDFS_NODE="$node" spark-submit \
  --master "$master_url" \
  --num-executors $NUM_EXECUTORS \
  --executor-cores $EXECUTOR_CORES \
  --executor-memory $EXECUTOR_MEMORY \
  --driver-memory $DRIVER_MEMORY \
  --conf spark.driver.maxResultSize="2g" \
  --conf spark.sql.shuffle.partitions=64 \
  --conf spark.default.parallelism=64 \
  --conf spark.local.dir=/tmp/spark \
  /mnt/c/LUUDULIEU/CODE/github/music_recommendation_engine/evaluation.py
check_status "Evaluation"

log "=== [5/5] Generate Submission ==="
HDFS_NODE="$node" spark-submit \
  --master "$master_url" \
  --num-executors $NUM_EXECUTORS \
  --executor-cores $EXECUTOR_CORES \
  --executor-memory $EXECUTOR_MEMORY \
  --driver-memory $DRIVER_MEMORY \
  --conf spark.driver.maxResultSize="2g" \
  --conf spark.sql.shuffle.partitions=128 \
  --conf spark.default.parallelism=128 \
  --conf spark.local.dir=/tmp/spark \
  /mnt/c/LUUDULIEU/CODE/github/music_recommendation_engine/generate_submission.py
check_status "Submission Generation"

log "✅ Pipeline completed successfully!"

# Lưu metrics vào file
metrics_file="${log_dir}/metrics_history.csv"
# (Giữ nguyên phần lưu metrics)
if [ ! -f "$metrics_file" ]; then
    echo "timestamp,map_score,num_playlists,training_time" > "$metrics_file"
fi

map_score=$(grep "Mean Average Precision @ 500:" "$log_file" | tail -n1 | awk '{print $NF}')
echo "${timestamp},${map_score},$num_playlists,$SECONDS" >> "$metrics_file"

log "📊 Metrics saved to ${metrics_file}"