# 🚀 Hướng dẫn Cấu hình MÁY 1 (Master Node)

Sử dụng file này **SAU KHI** Máy 2 đã hoàn tất cài đặt theo file `SETUP_WORKER.md`.

## Bước 1: Thiết lập SSH không mật khẩu

Máy 1 (máy của bạn) cần có khả năng đăng nhập vào Máy 2 để khởi động các dịch vụ.

1.  **Tạo Key (Nếu chưa có):**
    ```bash
    ssh-keygen -t rsa
    ```

2.  **Sao chép Key sang Máy 2 (Khuyến nghị):**
    * Đây là cách tự động và an toàn nhất. Nó sẽ yêu cầu mật khẩu của Máy 2 lần cuối cùng.
    * Thay `user_may_2` và `<IP_MAY_2>`.

    ```bash
    ssh-copy-id user_may_2@<IP_MAY_2>
    ```

3.  **Kiểm tra:**
    * Thử đăng nhập vào Máy 2. Bạn phải vào được thẳng mà không cần hỏi mật khẩu.
    ```bash
    ssh user_may_2@<IP_MAY_2>
    ```

## Bước 2: Cập nhật danh sách Worker

Báo cho Hadoop và Spark biết về worker mới (Máy 2).

1.  **Cập nhật Hadoop Workers:**
    * Mở file: `$HADOOP_HOME/etc/hadoop/workers`
    * Xóa `localhost` (nếu có) và đảm bảo file có nội dung:
    ```
    172.19.67.26
    <IP_MAY_2>
    ```

2.  **Cập nhật Spark Workers:**
    * Mở file: `$SPARK_HOME/conf/workers`
    * Đảm bảo file này có nội dung y hệt file trên:
    ```
    172.19.67.26
    <IP_MAY_2>
    ```

## Bước 3: Khởi động lại Toàn bộ Cụm

Thực hiện từ **Máy 1** (máy của bạn).

1.  **Dừng tất cả dịch vụ (nếu đang chạy):**
    ```bash
    $SPARK_HOME/sbin/stop-all.sh
    $HADOOP_HOME/sbin/stop-dfs.sh
    ```

2.  **Khởi động HDFS:**
    ```bash
    $HADOOP_HOME/sbin/start-dfs.sh
    ```
    *(Bạn sẽ thấy log báo khởi động NameNode/DataNode trên máy này và DataNode trên Máy 2).*

3.  **Khởi động Spark:**
    ```bash
    $SPARK_HOME/sbin/start-all.sh
    ```
    *(Bạn sẽ thấy log báo khởi động Master/Worker trên máy này và Worker trên Máy 2).*

## Bước 4: Kiểm tra Trạng thái Cụm

1.  **Kiểm tra HDFS:**
    * Mở trình duyệt: `http://172.19.67.26:9870`
    * Vào tab **"Datanodes"**. Bạn phải thấy **2 Datanodes** đang hoạt động (Live).

2.  **Kiểm tra Spark:**
    * Mở trình duyệt: `http://172.19.67.26:8080`
    * Bạn phải thấy **Alive Workers: 2**.

## Bước 5: Chạy Pipeline

Nếu cả hai bước kiểm tra trên đều thành công, cụm của bạn đã sẵn sàng.

Chỉ cần chạy pipeline như bình thường từ Máy 1. Spark Master sẽ tự động phân chia công việc (bước 4/5 và 5/5) cho cả hai máy worker.

```bash
./run_pipeline.sh
```