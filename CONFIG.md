🗺️ Bảng kế hoạch: Tên và Địa chỉ IPĐể tránh nhầm lẫn, chúng ta thống nhất tên gọi và địa chỉ IP cho toàn bộ hệ thống:MáyHệ điều hànhTên gọiIP Tĩnh (Sẽ đặt ở Phần 1-3)Máy 1Windows HostMASTER-HOST192.168.10.1WSL Ubuntuspark-master192.168.10.101Máy 2Windows HostWORKER-HOST192.168.10.2WSL Ubuntuspark-worker192.168.10.102🚧 Phần 1: Cấu hình Mạng Windows HostMục tiêu: Giúp 2 máy tính Windows "nhìn thấy" nhau qua dây LAN.Thực hiện trên: Cả hai máy tính Windows.Bước 1.1: Đặt IP Tĩnh cho WindowsCắm dây LAN kết nối trực tiếp 2 máy tính.Trên MASTER-HOST (Máy 1 - Windows):Mở Control Panel -> Network and Sharing Center -> Change adapter settings.Chuột phải vào card "Ethernet" (đang báo "Unidentified network"), chọn Properties.Chọn "Internet Protocol Version 4 (TCP/IPv4)" -> Properties.Chọn "Use the following IP address" và nhập:IP address: 192.168.10.1Subnet mask: 255.255.255.0Default gateway: (để trống)Nhấp OK.Trên WORKER-HOST (Máy 2 - Windows):Làm y hệt Máy 1, nhưng nhập:IP address: 192.168.10.2Subnet mask: 255.255.255.0Default gateway: (để trống)Nhấp OK.Bước 1.2: Kiểm tra kết nối WindowsTrên MASTER-HOST (Máy 1 - Windows):Mở Command Prompt (cmd).Gõ lệnh:Bashping 192.168.10.2
Nếu bạn thấy Reply from 192.168.10.2..., hai máy Windows đã kết nối thành công.🚧 Phần 2: Cấu hình Mạng WSL (Chế độ Cầu nối)Mục tiêu: "Bắc cầu" cho WSL Ubuntu sử dụng kết nối mạng LAN vật lý mà chúng ta vừa tạo.Thực hiện trên: Cả hai máy tính Windows.Bước 2.1: Tạo Virtual SwitchTrên CẢ HAI MÁY Windows (MASTER-HOST và WORKER-HOST):Nhấn phím Windows, gõ "Hyper-V Manager" và mở nó. (Nếu chưa có, vào "Turn Windows features on or off" để cài đặt).Trong menu bên phải, chọn "Virtual Switch Manager...".Chọn "New virtual network switch" -> "External" -> "Create Virtual Switch".Đặt tên: WSLBridgeTrong "External network", chọn card mạng "Ethernet" vật lý (chính là card bạn vừa đặt IP tĩnh ở Phần 1).Nhấp OK. Mạng của bạn có thể bị ngắt kết nối vài giây.Bước 2.2: Cấu hình .wslconfigTrên CẢ HAI MÁY Windows (MASTER-HOST và WORKER-HOST):Mở File Explorer, gõ %UserProfile% vào thanh địa chỉ và nhấn Enter (sẽ mở C:\Users\<Tên_Của_Bạn>).Tạo (hoặc mở) file .wslconfig (không có tên file, chỉ có đuôi).Copy và dán nội dung này vào:Ini, TOML[wsl2]
vmSwitch = WSLBridge
QUAN TRỌNG: Mở Command Prompt (cmd) và gõ lệnh sau để tắt hoàn toàn WSL:Bashwsl --shutdown
🚧 Phần 3: Cấu hình IP Tĩnh cho WSL UbuntuMục tiêu: Đặt IP tĩnh cho 2 máy Ubuntu để chúng có thể liên lạc với nhau.Bước 3.1: Đặt IP TĩnhTrên spark-master (Máy 1 - WSL Ubuntu):Khởi động WSL Ubuntu.Gõ lệnh sau (tên file có thể là 00-eth0.yaml hoặc 01-netcfg.yaml, hãy dùng phím Tab để tự động điền):Bashsudo nano /etc/netplan/00-eth0.yaml
Xóa hết nội dung cũ và dán nội dung sau vào:YAMLnetwork:
  version: 2
  ethernets:
    eth0:
      dhcp4: no
      addresses: [192.168.10.101/24]
      gateway4: 192.168.10.1
      nameservers:
        addresses: [8.8.8.8, 1.1.1.1]
Lưu ý: gateway4: 192.168.10.1 trỏ đến IP của MASTER-HOST (Windows).Trên spark-worker (Máy 2 - WSL Ubuntu):Khởi động WSL Ubuntu.Gõ lệnh:Bashsudo nano /etc/netplan/00-eth0.yaml
Xóa hết nội dung cũ và dán nội dung sau vào:YAMLnetwork:
  version: 2
  ethernets:
    eth0:
      dhcp4: no
      addresses: [192.168.10.102/24]
      gateway4: 192.168.10.1
      nameservers:
        addresses: [8.8.8.8, 1.1.1.1]
Lưu ý: gateway4 của máy Worker CŨNG trỏ về IP của MASTER-HOST.Trên CẢ HAI MÁY WSL (spark-master và spark-worker):Áp dụng cấu hình:Bashsudo netplan apply
🚧 Phần 4: Tường lửa & HostnamesMục tiêu: Mở cổng tường lửa và giúp các máy gọi nhau bằng tên thay vì IP.Bước 4.1: Cấu hình Windows Firewall (RẤT QUAN TRỌNG)Trên CẢ HAI MÁY Windows (MASTER-HOST và WORKER-HOST):Nhấn Windows, gõ "Windows Defender Firewall with Advanced Security" và mở nó.Nhấp vào "Inbound Rules" -> "New Rule..." (ở menu bên phải).Chọn "Port" -> Next.Chọn "TCP".Chọn "Specific local ports" và gõ danh sách cổng sau:22, 7077, 8080, 8081, 9000, 9870, 9866, 8088, 8032(Đây là các cổng cho SSH, Spark Master, Spark UI, HDFS NameNode, HDFS DataNode, YARN).Chọn "Allow the connection" -> Next.QUAN TRỌNG: Ở bước "Profile", hãy tick chọn cả 3 ô: "Domain", "Private", và "Public". (Vì mạng LAN trực tiếp này bị Windows coi là "Public"). -> Next.Đặt tên (ví dụ: Spark Cluster Ports) và nhấp Finish.Bước 4.2: Cấu hình /etc/hostsTrên CẢ HAI MÁY WSL (spark-master và spark-worker):Gõ lệnh:Bashsudo nano /etc/hosts
Thêm 2 dòng sau vào cuối file (sử dụng IP của WSL, không phải Windows):192.168.10.101   spark-master
192.168.10.102   spark-worker
Bước 4.3: Kiểm tra cuối cùngTrên spark-master (Máy 1 - WSL Ubuntu):Bashping spark-worker
Trên spark-worker (Máy 2 - WSL Ubuntu):Bashping spark-master
Nếu cả hai đều ping thành công (nhận được ... bytes from ...), bạn đã hoàn thành phần mạng.📦 Phần 5: Cài đặt Cluster (Hadoop & Spark)Giờ đây, bạn có 2 máy Ubuntu trên mạng LAN, việc cài đặt sẽ giống như một cluster bình thường.Bước 5.1: Cài đặt Chung (Java, SSH)Trên CẢ HAI MÁY WSL (spark-master và spark-worker):Bashsudo apt update
sudo apt install openjdk-11-jdk openssh-server -y
sudo service ssh start
Bước 5.2: Cấu hình SSH không mật khẩu (Master -> Worker)Trên spark-master (Máy 1 - WSL Ubuntu):Tạo khóa SSH:Bashssh-keygen -t rsa
(Nhấn Enter 3 lần để chấp nhận mặc định, không đặt mật khẩu).Copy khóa sang máy worker (thay tringuyen bằng tên user của bạn trên máy worker):Bashssh-copy-id tringuyen@spark-worker
(Nhập mật khẩu của user tringuyen trên máy spark-worker khi được hỏi).Kiểm tra (Trên spark-master):Bashssh spark-worker
Nếu bạn đăng nhập thẳng vào spark-worker mà không bị hỏi mật khẩu, bạn đã thành công. Gõ exit để quay lại spark-master.Bước 5.3: Cài đặt Hadoop (HDFS)Trên CẢ HAI MÁY WSL (spark-master và spark-worker):Tải Hadoop (ví dụ 3.3.6) và giải nén (giả sử vào /home/tringuyen/hadoop).Thêm biến môi trường vào .bashrc:Bashnano ~/.bashrc
Thêm các dòng sau vào cuối file:Bashexport JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export HADOOP_HOME=/home/tringuyen/hadoop
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
Áp dụng: source ~/.bashrcTrên spark-master (Máy 1 - WSL Ubuntu):Tạo thư mục dữ liệu HDFS:Bashmkdir -p /home/tringuyen/hdfs_data/namenode
mkdir -p /home/tringuyen/hdfs_data/datanode
Cấu hình hadoop-env.sh:Bashnano $HADOOP_HOME/etc/hadoop/hadoop-env.sh
Tìm dòng export JAVA_HOME và sửa thành: export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64Cấu hình core-site.xml:Bashnano $HADOOP_HOME/etc/hadoop/core-site.xml
Thêm vào giữa <configuration> và </configuration>:XML<property>
    <name>fs.defaultFS</name>
    <value>hdfs://spark-master:9000</value>
</property>
Cấu hình hdfs-site.xml:Bashnano $HADOOP_HOME/etc/hadoop/hdfs-site.xml
Thêm vào giữa <configuration> và </configuration>:XML<property>
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
Cấu hình workers:Bashnano $HADOOP_HOME/etc/hadoop/workers
Xóa localhost và thay bằng:spark-worker
Copy cấu hình sang Worker (Trên spark-master):Bashscp -r $HADOOP_HOME/etc/hadoop/* spark-worker:$HADOOP_HOME/etc/hadoop/
Khởi động HDFS (Trên spark-master):Format NameNode (CHỈ LÀM LẦN ĐẦU):Bashhdfs namenode -format
Khởi động HDFS:Bashstart-dfs.sh
Kiểm tra HDFS:Trên spark-master: gõ jps. Bạn phải thấy NameNode và SecondaryNameNode.Trên spark-worker: gõ jps. Bạn phải thấy DataNode.Mở trình duyệt trên máy Windows (ví dụ Máy 1): http://192.168.10.101:9870Vào tab "Datanodes", bạn phải thấy "1 Live Nodes".Bước 5.4: Cài đặt SparkTrên CẢ HAI MÁY WSL (spark-master và spark-worker):Tải Spark (ví dụ 3.5.0) và giải nén (giả sử vào /home/tringuyen/spark).Thêm biến môi trường vào .bashrc:Bashnano ~/.bashrc
Thêm vào cuối file:Bashexport SPARK_HOME=/home/tringuyen/spark
export PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin
Áp dụng: source ~/.bashrcTrên spark-master (Máy 1 - WSL Ubuntu):Cấu hình spark-env.sh:Bashcp $SPARK_HOME/conf/spark-env.sh.template $SPARK_HOME/conf/spark-env.sh
nano $SPARK_HOME/conf/spark-env.sh
Thêm các dòng sau vào cuối file:Bashexport JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export HADOOP_CONF_DIR=/home/tringuyen/hadoop/etc/hadoop
export SPARK_MASTER_HOST='spark-master'
Cấu hình workers:Bashcp $SPARK_HOME/conf/workers.template $SPARK_HOME/conf/workers
nano $SPARK_HOME/conf/workers
Xóa localhost và thay bằng:spark-worker
Copy cấu hình sang Worker (Trên spark-master):Bashscp -r $SPARK_HOME/conf/* spark-worker:$SPARK_HOME/conf/
Khởi động Spark (Trên spark-master):Bashstart-master.sh
start-workers.sh
Kiểm tra Spark:Trên spark-master: gõ jps. Bạn phải thấy Master.Trên spark-worker: gõ jps. Bạn phải thấy Worker.Mở trình duyệt trên máy Windows (ví dụ Máy 1): http://192.168.10.101:8080Bạn phải thấy 1 "Alive Worker" với địa chỉ spark-worker.
