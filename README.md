# Music Recommendation Engine

Hệ thống gợi ý âm nhạc sử dụng Collaborative Filtering trên Spotify Million Playlist Dataset.

## Giới thiệu

Project này xây dựng một hệ thống gợi ý (recommendation engine) để dự đoán các bài hát phù hợp cho một playlist dựa trên dữ liệu từ Spotify Million Playlist Dataset Challenge. Sử dụng Alternating Least Squares (ALS) với implicit feedback để xử lý bài toán collaborative filtering quy mô lớn.

## Yêu cầu hệ thống

- Apache Spark 3.x
- Apache Hadoop 3.x
- Python 3.8+
- 16GB RAM trở lên
- Ổ cứng có ít nhất 100GB trống

## Cài đặt

1. Cài đặt dependencies:
```bash
pip install pyspark==3.3.0
pip install numpy pandas
```

2. Cấu hình Hadoop và Spark:
- Copy files từ thư mục `configs/` vào các thư mục cấu hình tương ứng
- Cập nhật địa chỉ node trong files cấu hình

3. Chuẩn bị dữ liệu:
- Tải Spotify Million Playlist Dataset
- Giải nén và upload lên HDFS theo đường dẫn trong `configs/hdfs_paths.conf`

## Chạy hệ thống

1. Khởi động Hadoop & Spark:
```bash
./temp/start.sh
```

2. Chạy toàn bộ pipeline:
```bash
./run_pipeline.sh
```

Pipeline bao gồm 3 bước:
1. ETL: Chuyển đổi dữ liệu JSON thành Parquet
2. Training: Huấn luyện mô hình ALS
3. Inference: Tạo file submission.csv

## Cấu trúc project

```
├── configs/                 # Cấu hình Hadoop & Spark
├── temp/                   # Scripts khởi động cluster
├── etl_to_parquet.py      # ETL pipeline
├── train_als_model.py     # Training mô hình
├── generate_submission.py  # Tạo file submission
└── run_pipeline.sh        # Script chạy end-to-end
```

## Đánh giá

Mô hình được đánh giá bằng Mean Average Precision (MAP). Xem thêm chi tiết trong `evaluation.py`.

## Tác giả

Nguyễn Minh Trí | Ngô Quốc Huy

## License

MIT License
