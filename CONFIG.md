# Hướng dẫn Cài đặt Cluster HDFS & Spark 2 Node trên WSL (Kết nối LAN trực tiếp)

Tài liệu này hướng dẫn chi tiết cách cài đặt một cluster (cụm) Hadoop HDFS và Spark trên hai máy tính Windows, sử dụng WSL 2 (Ubuntu) cho mỗi node, và kết nối chúng trực tiếp bằng một dây LAN (không qua router).

---

## 🗺️ Bảng kế hoạch: Tên và Địa chỉ IP

Để tránh nhầm lẫn, chúng ta thống nhất tên gọi và địa chỉ IP cho toàn bộ hệ thống:

| Máy | Hệ điều hành | Tên gọi | IP Tĩnh (Sẽ đặt ở Phần 1-3) |
| :--- | :--- | :--- | :--- |
| **Máy 1** | **Windows Host** | `MASTER-HOST` | `192.168.10.1` |
| | **WSL Ubuntu** | `spark-master` | `192.168.10.101` |
| **Máy 2** | **Windows Host** | `WORKER-HOST` | `192.168.10.2` |
| | **WSL Ubuntu** | `spark-worker` | `192.168.10.102` |

---

## 🚧 Phần 1: Cấu hình Mạng Windows Host

**Mục tiêu:** Giúp 2 máy tính Windows "nhìn thấy" nhau qua dây LAN.
**Thực hiện trên:** Cả hai máy tính Windows.

### Bước 1.1: Đặt IP Tĩnh cho Windows

1.  Cắm dây LAN kết nối trực tiếp 2 máy tính.
2.  **Trên `MASTER-HOST` (Máy 1 - Windows):**
    * Mở **Control Panel** -> **Network and Sharing Center** -> **Change adapter settings**.
    * Chuột phải vào card "Ethernet" (đang báo "Unidentified network"), chọn **Properties**.
    * Chọn **"Internet Protocol Version 4 (TCP/IPv4)"** -> **Properties**.
    * Chọn **"Use the following IP address"** và nhập:
        * IP address: `192.168.10.1`
        * Subnet mask: `255.255.255.0`
        * Default gateway: (để trống)
    * Nhấp **OK**.

3.  **Trên `WORKER-HOST` (Máy 2 - Windows):**
    * Làm y hệt Máy 1, nhưng nhập:
        * IP address: `192.168.10.2`
        * Subnet mask: `255.255.255.0`
        * Default gateway: (để trống)
    * Nhấp **OK**.

### Bước 1.2: Kiểm tra kết nối Windows

* **Trên `MASTER-HOST` (Máy 1 - Windows):**
* Mở **Command Prompt (cmd)**.
* Gõ lệnh:
    ```bash
    ping 192.168.10.2
    ```
* Nếu bạn thấy `Reply from 192.168.10.2...`, hai máy Windows đã kết nối thành công.

---

## 🚧 Phần 2: Cấu hình Mạng WSL (Chế độ Cầu nối)

**Mục tiêu:** "Bắc cầu" cho WSL Ubuntu sử dụng kết nối mạng LAN vật lý mà chúng ta vừa tạo.
**Thực hiện trên:** Cả hai máy tính Windows.

### Bước 2.1: Tạo Virtual Switch

1.  **Trên CẢ HAI MÁY Windows (`MASTER-HOST` và `WORKER-HOST`):**
2.  Nhấn phím `Windows`, gõ **"Hyper-V Manager"** và mở nó. (Nếu chưa có, vào "Turn Windows features on or off" để cài đặt).
3.  Trong menu bên phải, chọn **"Virtual Switch Manager..."**.
4.  Chọn **"New virtual network switch"** -> **"External"** -> **"Create Virtual Switch"**.
5.  Đặt tên: `WSLBridge`
6.  Trong "External network", chọn card mạng **"Ethernet"** vật lý (chính là card bạn vừa đặt IP tĩnh ở Phần 1).
7.  Nhấp **OK**. Mạng của bạn có thể bị ngắt kết nối vài giây.

### Bước 2.2: Cấu hình `.wslconfig`

1.  **Trên CẢ HAI MÁY Windows (`MASTER-HOST` và `WORKER-HOST`):**
2.  Mở File Explorer, gõ `%UserProfile%` vào thanh địa chỉ và nhấn Enter (sẽ mở `C:\Users\<Tên_Của_Bạn>`).
3.  Tạo (hoặc mở) file `.wslconfig` (không có tên file, chỉ có đuôi).
4.  Copy và dán nội dung này vào:
    ```ini
    [wsl2]
    vmSwitch = WSLBridge
    ```
5.  **QUAN TRỌNG:** Mở **Command Prompt (cmd)** và gõ lệnh sau để tắt hoàn toàn WSL:
    ```bash
    wsl --shutdown
    ```

---

## 🚧 Phần 3: Cấu hình IP Tĩnh cho WSL Ubuntu

**Mục tiêu:** Đặt IP tĩnh cho 2 máy Ubuntu để chúng có thể liên lạc với nhau.

### Bước 3.1: Đặt IP Tĩnh

1.  **Trên `spark-master` (Máy 1 - WSL Ubuntu):**
    * Khởi động WSL Ubuntu.
    * Gõ lệnh sau (tên file có thể là `00-eth0.yaml` hoặc `01-netcfg.yaml`, hãy dùng phím `Tab` để tự động điền):
        ```bash
        sudo nano /etc/netplan/00-eth0.yaml
        ```
    * Xóa hết nội dung cũ và dán nội dung sau vào:
        ```yaml
        network:
          version: 2
          ethernets:
            eth0:
              dhcp4: no
              addresses: [192.168.10.101/24]
              gateway4: 192.168.10.1
              nameservers:
                addresses: [8.8.8.8, 1.1.1.1]
        ```
        *Lưu ý: `gateway4: 192.168.10.1` trỏ đến IP của `MASTER-HOST` (Windows).*

2.  **Trên `spark-worker` (Máy 2 - WSL Ubuntu):**
    * Khởi động WSL Ubuntu.
    * Gõ lệnh:
        ```bash
        sudo nano /etc/netplan/00-eth0.yaml
        ```
    * Xóa hết nội dung cũ và dán nội dung sau vào:
        ```yaml
        network:
          version: 2
          ethernets:
            eth0:
              dhcp4: no
              addresses: [192.168.10.102/24]
              gateway4: 192.168.10.1
              nameservers:
                addresses: [8.8.8.8, 1.1.1.1]
        ```
        *Lưu ý: `gateway4` của máy Worker CŨNG trỏ về IP của `MASTER-HOST`.*

3.  **Trên CẢ HAI MÁY WSL (`spark-master` và `spark-worker`):**
    * Áp dụng cấu hình:
        ```bash
        sudo netplan apply
        ```

---

## 🚧 Phần 4: Tường lửa & Hostnames

**Mục tiêu:** Mở cổng tường lửa và giúp các máy gọi nhau bằng tên thay vì IP.

### Bước 4.1: Cấu hình Windows Firewall (RẤT QUAN TRỌNG)

1.  **Trên CẢ HAI MÁY Windows (`MASTER-HOST` và `WORKER-HOST`):**
2.  Nhấn `Windows`, gõ **"Windows Defender Firewall with Advanced Security"** và mở nó.
3.  Nhấp vào **"Inbound Rules"** -> **"New Rule..."** (ở menu bên phải).
4.  Chọn **"Port"** -> Next.
5.  Chọn **"TCP"**.
6.  Chọn **"Specific local ports"** và gõ danh sách cổng sau:
    `22, 7077, 8080, 8081, 9000, 9870, 9866, 8088, 8032`
    (Đây là các cổng cho SSH, Spark Master, Spark UI, HDFS NameNode, HDFS DataNode, YARN).
7.  Chọn **"Allow the connection"** -> Next.
8.  **QUAN TRỌNG:** Ở bước "Profile", hãy **tick chọn cả 3 ô**: "Domain", "Private", và **"Public"**. (Vì mạng LAN trực tiếp này bị Windows coi là "Public"). -> Next.
9.  Đặt tên (ví dụ: `Spark Cluster Ports`) và nhấp **Finish**.

### Bước 4.2: Cấu hình `/etc/hosts`

1.  **Trên CẢ HAI MÁY WSL (`spark-master` và `spark-worker`):**
2.  Gõ lệnh:
    ```bash
    sudo nano /etc/hosts
    ```
3.  Thêm 2 dòng sau vào cuối file (sử dụng IP của WSL, không phải Windows):
    ```
    192.168.10.101   spark-master
    192.168.10.102   spark-worker
    ```

### Bước 4.3: Kiểm tra cuối cùng

1.  **Trên `spark-master` (Máy 1 - WSL Ubuntu):**
    ```bash
    ping spark-worker
    ```
2.  **Trên `spark-worker` (Máy 2 - WSL Ubuntu):**
    ```bash
    ping spark-master
    ```
* Nếu cả hai đều `ping` thành công (nhận được `... bytes from ...`), bạn đã hoàn thành phần mạng.

---

## 📦 Phần 5: Cài đặt Cluster (Hadoop & Spark)

Giờ đây, bạn có 2 máy Ubuntu trên mạng LAN, việc cài đặt sẽ giống như một cluster bình thường.

### Bước 5.1: Cài đặt Chung (Java, SSH)

1.  **Trên CẢ HAI MÁY WSL (`spark-master` và `spark-worker`):**
    ```bash
    sudo apt update
    sudo apt install openjdk-11-jdk openssh-server -y
    sudo service ssh start
    ```

### Bước 5.2: Cấu hình SSH không mật khẩu (Master -> Worker)

1.  **Trên `spark-master` (Máy 1 - WSL Ubuntu):**
    * Tạo khóa SSH:
        ```bash
        ssh-keygen -t rsa
        ```
        (Nhấn `Enter` 3 lần để chấp nhận mặc định, không đặt mật khẩu).
    * Copy khóa sang máy worker (thay `tringuyen` bằng tên user của bạn trên máy worker):
        ```bash
        ssh-copy-id tringuyen@spark-worker
        ```
        (Nhập mật khẩu của user `tringuyen` trên máy `spark-worker` khi được hỏi).

2.  **Kiểm tra (Trên `spark-master`):**
    ```bash
    ssh spark-worker
    ```
    Nếu bạn đăng nhập thẳng vào `spark-worker` mà **không bị hỏi mật khẩu**, bạn đã thành công. Gõ `exit` để quay lại `spark-master`.

### Bước 5.3: Cài đặt Hadoop (HDFS)

1.  **Trên CẢ HAI MÁY WSL (`spark-master` và `spark-worker`):**
    * Tải Hadoop (ví dụ 3.3.6) và giải nén (giả sử vào `/home/tringuyen/hadoop`).
    * Thêm biến môi trường vào `.bashrc`:
        ```bash
        nano ~/.bashrc
        ```
    * Thêm các dòng sau vào cuối file:
        ```bash
        export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
        export HADOOP_HOME=/home/tringuyen/hadoop
        export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin
        export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
        ```
    * Áp dụng: `source ~/.bashrc`

2.  **Trên `spark-master` (Máy 1 - WSL Ubuntu):**
    * Tạo thư mục dữ liệu HDFS:
        ```bash
        mkdir -p /home/tringuyen/hdfs_data/namenode
        mkdir -p /home/tringuyen/hdfs_data/datanode
        ```
    * Cấu hình `hadoop-env.sh`:
        ```bash
        nano $HADOOP_HOME/etc/hadoop/hadoop-env.sh
        ```
        Tìm dòng `export JAVA_HOME` và sửa thành: `export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64`
    * Cấu hình `core-site.xml`:
        ```bash
        nano $HADOOP_HOME/etc/hadoop/core-site.xml
        ```
        Thêm vào giữa `<configuration>` và `</configuration>`:
        ```xml
        <configuration>
            <property>
                <name>fs.defaultFS</name>
                <value>hdfs://spark-master:9000</value>
            </property>
        </configuration>
        ```
    * Cấu hình `hdfs-site.xml`:
        ```bash
        nano $HADOOP_HOME/etc/hadoop/hdfs-site.xml
        ```
        Thêm vào giữa `<configuration>` và `</configuration>`:
        ```xml
        <configuration>
            <property>
                <name>dfs.replication</name>
                <value>1</value>
            </property>
            <property>
                <name>dfs.namenode.name.dir</name>
                <value>file:///home/tringuyen/hdfs_data/namenode</value>
            </property>
            <property>
                <name>dfs.datanode.data.dir</name>
                <value>file:///home/tringuyen/hdfs_data/datanode</value>
            </property>
        </configuration>
        ```
    * Cấu hình `workers`:
        ```bash
        nano $HADOOP_HOME/etc/hadoop/workers
        ```
        Xóa `localhost` và thay bằng:
        ```
        spark-worker
        ```

3.  **Copy cấu hình sang Worker (Trên `spark-master`):**
    ```bash
    scp -r $HADOOP_HOME/etc/hadoop/* spark-worker:$HADOOP_HOME/etc/hadoop/
    ```

4.  **Khởi động HDFS (Trên `spark-master`):**
    * Format NameNode (CHỈ LÀM LẦN ĐẦU):
        ```bash
        hdfs namenode -format
        ```
    * Khởi động HDFS:
        ```bash
        start-dfs.sh
        ```

5.  **Kiểm tra HDFS:**
    * **Trên `spark-master`:** gõ `jps`. Bạn phải thấy `NameNode` và `SecondaryNameNode`.
    * **Trên `spark-worker`:** gõ `jps`. Bạn phải thấy `DataNode`.
    * Mở trình duyệt trên máy Windows (ví dụ Máy 1): `http://192.168.10.101:9870`
    * Vào tab "Datanodes", bạn phải thấy "1 Live Nodes".

### Bước 5.4: Cài đặt Spark

1.  **Trên CẢ HAI MÁY WSL (`spark-master` và `spark-worker`):**
    * Tải Spark (ví dụ 3.5.0) và giải nén (giả sử vào `/home/tringuyen/spark`).
    * Thêm biến môi trường vào `.bashrc`:
        ```bash
        nano ~/.bashrc
        ```
    * Thêm vào cuối file:
        ```bash
        export SPARK_HOME=/home/tringuyen/spark
        export PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin
        ```
    * Áp dụng: `source ~/.bashrc`

2.  **Trên `spark-master` (Máy 1 - WSL Ubuntu):**
    * Cấu hình `spark-env.sh`:
        ```bash
        cp $SPARK_HOME/conf/spark-env.sh.template $SPARK_HOME/conf/spark-env.sh
        nano $SPARK_HOME/conf/spark-env.sh
        ```
        Thêm các dòng sau vào cuối file:
        ```bash
        export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
        export HADOOP_CONF_DIR=/home/tringuyen/hadoop/etc/hadoop
        export SPARK_MASTER_HOST='spark-master'
        ```
    * Cấu hình `workers`:
        ```bash
        cp $SPARK_HOME/conf/workers.template $SPARK_HOME/conf/workers
        nano $SPARK_HOME/conf/workers
        ```
        Xóa `localhost` và thay bằng:
        ```
        spark-worker
        ```

3.  **Copy cấu hình sang Worker (Trên `spark-master`):**
    ```bash
    scp -r $SPARK_HOME/conf/* spark-worker:$SPARK_HOME/conf/
    ```

4.  **Khởi động Spark (Trên `spark-master`):**
    ```bash
    start-master.sh
    start-workers.sh
    ```

5.  **Kiểm tra Spark:**
    * **Trên `spark-master`:** gõ `jps`. Bạn phải thấy `Master`.
    * **Trên `spark-worker`:** gõ `jps`. Bạn phải thấy `Worker`.
    * Mở trình duyệt trên máy Windows (ví dụ Máy 1): `http://192.168.10.101:8080`
    * Bạn phải thấy 1 "Alive Worker" với địa chỉ `spark-worker`.

---

## 🚀 Phần 6: Chạy Job của bạn

Bây giờ bạn đã sẵn sàng!

1.  **Trên `spark-master` (Máy 1 - WSL Ubuntu):**
2.  Mở file `run_pipeline.sh` của bạn.
3.  **Sửa 2 chỗ quan trọng:**
    * Tìm dòng `node="172.19.67.26"` và đổi thành `node="spark-master"`.
    * Trong các lệnh `spark-submit`, đổi `--master spark://$node:7077` thành `--master spark://spark-master:7077`.
4.  **Tối ưu RAM (Ví dụ: Máy 1 có 8GB, Máy 2 có 16GB):**
    * Tìm đến bước `[4/5] Evaluate Model` và sửa như sau:
        ```bash
        log "=== [4/5] Evaluate Model ==="
        HDFS_NODE="spark-master" spark-submit \
        --master spark://spark-master:7077 \
        --conf spark.driver.memory=6g \
        --conf spark.executor.memory=12g \
        --conf spark.executor.cores=2 \
        ... (giữ nguyên các tham số khác) ...
        /mnt/c/LUUDULIEU/CODE/github/music_recommendation_engine/evaluation.py
        check_status "Evaluation"
        ```
    * **Giải thích:**
        * `spark.driver.memory=6g`: Driver sẽ chạy trên `spark-master`, lấy 6GB RAM của Máy 1.
        * `spark.executor.memory=12g`: Executor sẽ chạy trên `spark-worker`, lấy 12GB RAM của Máy 2.
5.  Chạy script: `./run_pipeline.sh`
