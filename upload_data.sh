#!/bin/bash

# ========================================
# Cấu hình Đường dẫn
# ========================================
# IP của NameNode (Master Node) và cổng mặc định 9000
NAMENODE_URI="hdfs://172.19.67.26:9000"

# Đường dẫn file JSON cục bộ trên WSL/Linux
# Đường dẫn này được lấy từ vị trí mà bạn đã mount ổ đĩa Windows (thường là /mnt/c)
LOCAL_FILE="/mnt/c/LUUDULIEU/CODE/THBigData/data/music_recommendation_engine_data/spotify_million_playlist_dataset/data/mpd.slice.*.json"

# Đường dẫn đích trong HDFS (nơi các script Spark sẽ đọc)
HDFS_DESTINATION="/data/mqd/raw/"

# ========================================
# Thực thi
# ========================================

# 1. Kiểm tra file cục bộ có tồn tại không
if [ ! -f "$LOCAL_FILE" ]; then
    echo "❌ LỖI: Không tìm thấy file cục bộ tại: $LOCAL_FILE"
    exit 1
fi

# 2. Xóa thư mục HDFS đích nếu nó tồn tại (để đảm bảo sạch sẽ)
echo "--- Đang dọn dẹp thư mục đích HDFS..."
hdfs dfs -rm -r -f "$HDFS_DESTINATION" || true

# 3. Tạo thư mục đích trong HDFS
echo "--- Đang tạo thư mục HDFS: $HDFS_DESTINATION"
hdfs dfs -mkdir -p "$HDFS_DESTINATION"

# 4. Upload dữ liệu
echo "--- Đang tải file lên HDFS..."
# Sử dụng lệnh -put để sao chép file cục bộ lên HDFS
hdfs dfs -put "$LOCAL_FILE" "$HDFS_DESTINATION"

if [ $? -eq 0 ]; then
    echo "✅ Tải dữ liệu thành công lên HDFS: ${NAMENODE_URI}${HDFS_DESTINATION}"
else
    echo "❌ LỖI: Tải dữ liệu thất bại."
fi