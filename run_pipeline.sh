# !/bin/bash
# Chạy toàn bộ pipeline end-to-end

echo "=== [1/3] ETL JSON → Parquet ==="
spark-submit --master spark://172.19.67.26:7077 etl_to_parquet.py

echo "=== [2/3] Train ALS Model ==="
spark-submit --master spark://172.19.67.26:7077 train_als_model.py

echo "=== [3/3] Generate Submission ==="
spark-submit --master spark://172.19.67.26:7077 generate_submission.py

echo "✅ Toàn bộ pipeline đã hoàn tất!"
