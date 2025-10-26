#!/bin/bash
set -e  # Exit on error

# Cấu hình
node="172.19.67.26" # "node1"
timestamp=$(date +%Y%m%d_%H%M%S)
log_dir="logs"
log_file="${log_dir}/pipeline_${timestamp}.log"

# Tạo thư mục logs nếu chưa tồn tại
mkdir -p $log_dir

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
hdfs dfs -test -d /data/mpd/parquet && {
    backup_dir="/data/mpd/backup/parquet_${timestamp}"
    hdfs dfs -mv /data/mpd/parquet $backup_dir
    log "✓ Backed up parquet data to $backup_dir"
} || log "No existing parquet data to backup"

# Pipeline chính
log "=== [1/5] ETL JSON → Parquet ==="
spark-submit --master spark://$node:7077 etl_to_parquet.py
check_status "ETL"

log "=== [2/5] Split Train/Test Data ==="
spark-submit --master spark://$node:7077 split_train_test.py
check_status "Data Split"

log "=== [3/5] Train ALS Model ==="
spark-submit --master spark://$node:7077 train_als_model.py
check_status "Training"

log "=== [4/5] Evaluate Model ==="
spark-submit --master spark://$node:7077 evaluation.py
check_status "Evaluation"

log "=== [5/5] Generate Submission ==="
spark-submit --master spark://$node:7077 generate_submission.py
check_status "Submission Generation"

log "✅ Pipeline completed successfully!"

# Lưu metrics vào file
metrics_file="${log_dir}/metrics_history.csv"
if [ ! -f "$metrics_file" ]; then
    echo "timestamp,map_score,num_playlists,training_time" > "$metrics_file"
fi

# Lấy MAP score từ log file
map_score=$(grep "Mean Average Precision @ 500:" "$log_file" | tail -n1 | awk '{print $NF}')
echo "${timestamp},${map_score},$num_playlists,$SECONDS" >> "$metrics_file"

log "📊 Metrics saved to ${metrics_file}"
