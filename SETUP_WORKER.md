# 🚀 Hướng dẫn Cài đặt MÁY 2 (Worker Node)

Chào mừng bạn! Hướng dẫn này giúp bạn cài đặt máy của mình (Máy 2) để tham gia vào cụm Hadoop/Spark hiện có, được quản lý bởi **Máy 1 (Master Node)** tại `172.19.67.26`.

Chúng ta sẽ kết nối 2 máy trực tiếp bằng cáp LAN (không dùng router), vì vậy việc **cấu hình IP Tĩnh** là bắt buộc.

---

## Bước 1: Cài đặt Phần mềm Nền tảng

**QUAN TRỌNG:** Các phiên bản phần mềm phải **giống hệt** với Máy 1.

1.  **Cài đặt Java JDK:**
    * Phiên bản yêu cầu: `openjdk version "1.8.0_462"`
    * Kiểm tra bằng lệnh: `java -version`

2.  **Cài đặt Python 3:**
    ```bash
    sudo apt update
    sudo apt install python3 python3-pip
    ```

3.  **Cài đặt Thư viện Python:**
    ```bash
    pip3 install pyspark numpy
    ```

4.  **Cài đặt Hadoop & Spark:**
    * Tải **Hadoop 3.3.5** và **Spark 3.5.7**.
    * Giải nén vào các đường dẫn chuẩn (ví dụ: `/usr/local/hadoop` và `/usr/local/spark`).
    * Thiết lập các biến môi trường `$JAVA_HOME`, `$HADOOP_HOME`, `$SPARK_HOME` và `PATH` trong file `.bashrc` của bạn.

---

## Bước 2: Cấu hình Mạng (IP Tĩnh) - Rất Quan trọng

Vì chúng ta nối 2 máy trực tiếp, bạn phải **thiết lập IP Tĩnh** thủ công cho cổng LAN của máy này.

1.  Vào phần Cài đặt Mạng (Network Settings) trên máy của bạn (ví dụ: `nmtui` trên Linux).
2.  Chọn cổng LAN (Ethernet) và chuyển từ "DHCP" (Tự động) sang "Manual" (Thủ công).
3.  Nhập các thông số sau:
    * **IP Address (Địa chỉ):** `172.19.67.27`
    * **Subnet Mask (Mặt nạ):** `255.255.255.0`
    * **Gateway (Cổng):** (Để trống hoặc điền `172.19.67.26`)

4.  Lưu cài đặt và **cắm dây LAN** nối hai máy.

5.  **Kiểm tra kết nối:** Mở Terminal và chạy:
    ```bash
    ping 172.19.67.26
    ```
    * Bạn **phải** thấy tín hiệu phản hồi (reply) từ Máy 1. Nếu không, hãy kiểm tra lại IP và cáp cắm trước khi tiếp tục.

---

## Bước 3: Cấu hình Mạng (`/etc/hosts`)

Việc này giúp máy của bạn "nhận diện" máy chủ bằng tên.

1.  Mở file hosts:
    ```bash
    sudo nano /etc/hosts
    ```

2.  Thêm 2 dòng sau vào cuối file (chúng ta dùng IP tĩnh đã thiết lập ở Bước 2):
    ```
    172.19.67.26  master-node
    172.19.67.27  worker-node
    ```

---

## Bước 4: Cấu hình HDFS (Để làm DataNode)

Chúng ta sẽ cấu hình máy của bạn để lưu trữ dữ liệu cho HDFS.

**CẢNH BÁO:** **KHÔNG BAO GIỜ** chạy lệnh `hdfs namenode -format` trên máy này.

1.  **File `$HADOOP_HOME/etc/hadoop/core-site.xml`**:
    * File này chỉ định NameNode (Máy 1) là máy chủ HDFS mặc định.

    ```xml
    <configuration>
        <property>
            <name>fs.defaultFS</name>
            <value>hdfs://172.19.67.26:9000</value>
        </property>
    </configuration>
    ```

2.  **File `$HADOOP_HOME/etc/hadoop/hdfs-site.xml`**:
    * File này cấu hình máy của bạn làm DataNode. (Hãy tạo thư mục `/usr/local/hadoop/data/datanode` nếu bạn dùng đường dẫn này).

    ```xml
    <configuration>
        <property>
            <name>dfs.replication</name>
            <value>2</value>
        </property>
        <property>
            <name>dfs.datanode.data.dir</name>
            <value>file:///usr/local/hadoop/data/datanode</value>
        </property>
    </configuration>
    ```

---

## Bước 5: Cấu hình Spark (Để làm Worker)

Cấu hình máy của bạn để nhận tác vụ tính toán từ Spark Master (Máy 1).

1.  **File `$SPARK_HOME/conf/spark-env.sh`**:
    * Sao chép từ `spark-env.sh.template` nếu chưa có.
    * Thêm dòng sau để chỉ định Spark Master (Máy 1):

    ```bash
    #!/usr/bin/env bash
    export SPARK_MASTER_HOST='172.19.67.26'
    ```

---

## Bước 6: Hoàn tất và Liên hệ Máy 1

Việc cài đặt trên Máy 2 đã hoàn tất.

Bây giờ, hãy **báo cho người quản lý Máy 1** (tại `172.19.67.26`) biết rằng bạn đã xong. Họ cần thực hiện các bước sau từ máy của họ:

1.  Chạy lệnh `ssh-copy-id` để thêm "public key" của họ vào máy của bạn (cho phép đăng nhập không cần mật khẩu).
2.  Cập nhật địa chỉ IP của bạn (`172.19.67.27`) vào file `workers` của họ.
3.  Khởi động lại toàn bộ cụm.

*(**Phần dự phòng - Chỉ làm nếu Máy 1 yêu cầu:** Nếu Máy 1 không thể dùng `ssh-copy-id`, họ sẽ gửi cho bạn một chuỗi key (bắt đầu bằng `ssh-rsa...`). Bạn hãy chạy các lệnh sau để dán key đó vào)*:

```bash
# mkdir -p ~/.ssh
# nano ~/.ssh/authorized_keys
# (Dán key vào đây, lưu và thoát)
# chmod 700 ~/.ssh
# chmod 600 ~/.ssh/authorized_keys