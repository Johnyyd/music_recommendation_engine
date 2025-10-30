#!/bin/bash
echo "========================================="
echo "🔬 BẮT ĐẦU KIỂM TRA MÔI TRƯỜNG CLUSTER"
echo "========================================="

# --- Hàm trợ giúp ---
check_var() {
  if [ -z "$1" ]; then
    echo "    ❌ ERROR: Biến môi trường $2 chưa được thiết lập (chưa set)."
    return 1
  else
    echo "    ✅ $2: $1"
    return 0
  fi
}

check_cmd() {
  if ! command -v $1 &> /dev/null; then
    echo "    ❌ ERROR: Lệnh '$1' không tồn tại. Vui lòng kiểm tra cài đặt và PATH."
    return 1
  else
    echo "    ✅ Lệnh '$1' đã tìm thấy."
    return 0
  fi
}

# --- 1. Kiểm tra Java ---
echo
echo "--- 1. Kiểm tra Java ---"
if check_cmd java; then
  java -version 2>&1 | grep "version"
  check_var "$JAVA_HOME" "JAVA_HOME"
fi

# --- 2. Kiểm tra Hadoop ---
echo
echo "--- 2. Kiểm tra Hadoop ---"
if check_cmd hadoop; then
  hadoop version | grep "Hadoop"
  check_var "$HADOOP_HOME" "HADOOP_HOME"
fi

# --- 3. Kiểm tra Spark ---
echo
echo "--- 3. Kiểm tra Spark ---"
if check_cmd spark-submit; then
  spark-submit --version 2>&1 | grep "version"
  check_var "$SPARK_HOME" "SPARK_HOME"
fi

# --- 4. Kiểm tra Python & Libraries (cho PySpark) ---
echo
echo "--- 4. Kiểm tra Python & Libraries ---"
if check_cmd python3; then
  python3 --version
  
  # Kiểm tra pyspark (bắt buộc)
  if python3 -c "import pyspark" &> /dev/null; then
    echo "    ✅ Thư viện 'pyspark' đã được cài đặt."
  else
    echo "    ❌ ERROR: Thư viện 'pyspark' chưa được cài đặt (chạy 'pip3 install pyspark')."
  fi
  
  # Kiểm tra numpy (bắt buộc cho evaluation.py)
  if python3 -c "import numpy" &> /dev/null; then
    echo "    ✅ Thư viện 'numpy' đã được cài đặt."
  else
    echo "    ❌ ERROR: Thư viện 'numpy' chưa được cài đặt (chạy 'pip3 install numpy')."
  fi
fi

# --- 5. Kiểm tra HDFS (chỉ kiểm tra nếu lệnh hdfs tồn tại) ---
echo
echo "--- 5. Kiểm tra kết nối HDFS ---"
if check_cmd hdfs; then
  echo "    Đang thử kết nối tới NameNode tại $HDFS_NODE (172.19.67.26)..."
  if hdfs dfs -ls hdfs://172.19.67.26:9000/ &> /dev/null; then
    echo "    ✅ Kết nối HDFS thành công!"
  else
    echo "    ❌ ERROR: Không thể kết nối tới NameNode tại hdfs://172.19.67.26:9000/."
    echo "    Hãy đảm bảo HDFS đang chạy và cấu hình 'core-site.xml' chính xác."
  fi
fi

echo
echo "========================================="
echo "✅ KIỂM TRA MÔI TRƯỜNG HOÀN TẤT"
echo "========================================="
echo "Lưu ý: Hãy chạy script này trên CẢ HAI MÁY và so sánh kết quả."
echo "Các phiên bản Java, Hadoop, Spark, và Python phải GIỐNG HỆT nhau."