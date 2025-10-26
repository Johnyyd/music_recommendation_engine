Đây là phân tích chi tiết về Đề tài 1 (Hệ thống Gợi ý Âm nhạc Cá nhân hóa) trong bối cảnh sử dụng HDFS, Hadoop và PySpark trên cụm 2 máy tính.

---

### 1. Yêu cầu mục đích của dữ liệu

Mục đích của việc sử dụng Bộ dữ liệu Danh sách phát Triệu bài hát (MPD) là để **hỗ trợ nghiên cứu về đề xuất nhạc** và cụ thể là xây dựng một **Hệ thống Gợi ý** (recommendation engine).

Nhiệm vụ trọng tâm là **Tiếp nối Danh sách phát Tự động (Automatic Playlist Continuation)**:
*   Dựa trên các đặc điểm của một danh sách phát đầu vào (ví dụ: tiêu đề và/hoặc tập hợp $K$ bản nhạc ban đầu).
*   Hệ thống phải dự đoán các bản nhạc tiếp theo mà người dùng có khả năng sẽ thêm vào danh sách phát đó.
*   Dữ liệu MPD được thiết kế để giúp các nhà nghiên cứu học hỏi về mối quan hệ giữa người dùng và âm nhạc, ví dụ: tại sao một số bài hát lại đi cùng nhau.

### 2. Độ phức tạp của bộ dữ liệu

Bộ dữ liệu MPD là bộ dữ liệu công khai lớn nhất thế giới về danh sách phát nhạc. Độ phức tạp của nó xuất phát từ quy mô và cấu trúc của dữ liệu:

*   **Quy mô Khổng lồ:** Bộ dữ liệu bao gồm **1 triệu danh sách phát**, chứa hơn **2 triệu bản nhạc độc đáo**, và gần **300.000 nghệ sĩ** (hoặc gần 70 triệu nghệ sĩ theo nguồn).
*   **Ma trận Thưa (Sparsity):** Kích thước khổng lồ của số lượng playlist và bài hát tạo ra một **ma trận tương tác playlist-bài hát cực lớn và rất thưa** (sparse). Đây là một bài toán Dữ liệu lớn (Big Data) thực sự, yêu cầu sử dụng các công cụ tính toán phân tán như PySpark/Hadoop.
*   **Định dạng:** Dữ liệu được phân phối dưới dạng một tập hợp các tệp JSON, đòi hỏi quá trình ETL (Extract, Transform, Load) phức tạp để chuyển đổi thành cấu trúc có thể sử dụng cho mô hình lọc cộng tác.
*   **Hạn chế Dữ liệu:** Dữ liệu đã được lấy mẫu không đồng nhất, được lọc thủ công, và có thêm một số nhiễu (dithering) và các bản nhạc hư cấu (fictitious tracks), và **không đại diện cho sự phân phối thực tế** của playlist trên nền tảng.

### 3. Kết quả cần có sau phân tích

Sau khi phân tích và huấn luyện mô hình, kết quả cần đạt được là một hệ thống gợi ý hoạt động hiệu quả và bài nộp cuối cùng phải tuân thủ nghiêm ngặt các yêu cầu sau:

*   **Sản phẩm Nộp:** Một tệp dự đoán duy nhất có tên **`submission.csv`**.
*   **Cấu trúc tệp:** Tệp này phải có chính xác hai cột: `playlist_id` và `recommended_track_uris`.
*   **Nội dung Đề xuất:** Cột `recommended_track_uris` phải chứa một danh sách **500 URI của các bài hát được gợi ý**, được phân tách bằng dấu phẩy.
*   **Xếp hạng:** Danh sách 500 URI phải được sắp xếp theo thứ tự **từ tự tin nhất đến ít tự tin nhất** (tức là theo mức độ liên quan giảm dần).
*   **Đánh giá Hiệu suất:** Mô hình của nhóm sẽ được đánh giá bằng chỉ số **Mean Average Precision (MAP)**.

### 4. Sử dụng HDFS Hadoop và PySpark đối với 2 máy tính thật nên chia sẻ chức năng, dữ liệu như thế nào

Yêu cầu sử dụng Apache Spark (PySpark) chạy trên HDFS đòi hỏi cấu hình cụm phân tán 2 nút:

| Thành phần | Máy 1 (Master Node) | Máy 2 (Worker Node) | Chia sẻ/Chức năng |
| :--- | :--- | :--- | :--- |
| **HDFS (Dữ liệu)** | **NameNode** (Quản lý siêu dữ liệu) và **DataNode** (Lưu trữ dữ liệu) | **DataNode** (Lưu trữ dữ liệu) | Dữ liệu MPD (JSON) được phân tán và sao chép trên cả hai máy. |
| **PySpark (Chức năng)** | **Driver Program** (Chạy logic PySpark), **Spark Master** (Quản lý tài nguyên cụm), và **Executor** (Thực thi tác vụ) | **Spark Worker** và **Executor** (Thực thi tác vụ) | Driver gửi các tác vụ (ví dụ: lọc cộng tác, ETL) đến Master, Master điều phối các Executor trên cả hai máy để xử lý song song. |

Việc chia sẻ này cho phép tận dụng tính địa phương của dữ liệu (data locality), nghĩa là PySpark Executor cố gắng xử lý dữ liệu nằm trên cùng một DataNode để giảm thiểu việc truyền dữ liệu qua mạng.

### 5. Cấu hình 2 máy tính (PySpark Cluster) nên được cấu hình, cài đặt (không phải phần cứng máy tính) như thế nào

Cấu hình phi phần cứng cho cụm 2 máy tính (Hadoop/Spark Standalone Cluster) bao gồm:

1.  **Hệ điều hành và Java:** Cài đặt HĐH (ví dụ: Linux) và **Java Development Kit (JDK)** trên cả hai máy, vì Hadoop và Spark phụ thuộc vào Java.
2.  **Kết nối SSH:** Thiết lập kết nối **SSH không cần mật khẩu** (passwordless SSH) giữa Máy 1 (Master) và Máy 2 (Worker). Điều này cần thiết để Master có thể khởi động, dừng và quản lý các dịch vụ trên Worker từ xa.
3.  **Cài đặt HDFS:**
    *   Cài đặt Hadoop trên cả hai máy.
    *   Cấu hình `core-site.xml` và `hdfs-site.xml` để chỉ định Máy 1 là NameNode và cả hai máy là DataNode.
    *   Format NameNode trên Máy 1 và khởi động dịch vụ HDFS.
4.  **Cài đặt PySpark:**
    *   Cài đặt Apache Spark trên cả hai máy.
    *   Cấu hình tệp `slaves` hoặc `workers` (trong cấu hình Spark) để chỉ định địa chỉ mạng của Máy 2.
    *   Máy 1 được cấu hình là Spark Master, Máy 2 được cấu hình là Spark Worker.
    *   Cài đặt Python và các thư viện cần thiết (ví dụ: `pyspark`) trên cả hai máy.
    *   Khởi động dịch vụ Spark Master trên Máy 1 và Spark Worker trên Máy 2.

### 6. Đề xuất kết hợp các công nghệ nhẹ, dễ cài đặt, tốc độ cao nhằm giảm sức ép đối với 2 máy tính thật

Để giảm áp lực tính toán và I/O cho cụm 2 máy tính, các công nghệ và kỹ thuật sau nên được áp dụng, ưu tiên tính tương thích với hệ sinh thái Spark/HDFS:

1.  **Định dạng Dữ liệu Cột:** Ngay sau khi nhập dữ liệu JSON MPD, sử dụng PySpark để chuyển đổi toàn bộ bộ dữ liệu sang định dạng lưu trữ cột nén, chẳng hạn như **Apache Parquet**. Parquet cải thiện tốc độ truy vấn đáng kể và giảm tải I/O so với JSON thô, đặc biệt khi chỉ cần chọn một tập hợp con các cột (ví dụ: `playlist_id`, `track_uri`) cho quá trình huấn luyện lọc cộng tác.
2.  **Tận dụng Caching và Persisting của Spark:** Đối với các DataFrame quan trọng (ví dụ: ma trận tương tác đã được chuẩn hóa), sử dụng **`cache()`** hoặc **`persist(StorageLevel.MEMORY_AND_DISK)`** của PySpark. Kỹ thuật này giữ dữ liệu trong bộ nhớ RAM của các Executor (trên cả hai máy tính), tránh việc đọc lặp lại từ HDFS, từ đó tăng tốc độ huấn luyện mô hình ALS.
3.  **Pandas UDF:** Đối với một số bước tiền xử lý hoặc sau xử lý (ví dụ: xử lý chuỗi URI, tách dấu phẩy trong cột URI cuối cùng) cần logic phức tạp trên các hàng riêng lẻ, có thể sử dụng **Pandas UDF (User Defined Functions)** để tận dụng tốc độ của Pandas/Numpy cục bộ, mặc dù vẫn được chạy trong môi trường phân tán của PySpark.

### 7. Có thể sử dụng dây LAN để kết nối 2 máy tính thật

**Có, hoàn toàn có thể sử dụng dây LAN để kết nối 2 máy tính thật.**

Việc sử dụng dây LAN là **cực kỳ quan trọng** đối với hiệu suất của cụm Hadoop/Spark 2 nút. Các hệ thống phân tán như HDFS và Spark (thực hiện shuffle dữ liệu) đòi hỏi băng thông mạng cao và độ trễ thấp để di chuyển các khối dữ liệu và kết quả trung gian giữa các DataNode và Executor. Kết nối LAN có dây (đặc biệt là cáp Ethernet Gigabit hoặc tốt hơn) cung cấp tốc độ cao và độ ổn định vượt trội so với kết nối Wi-Fi, giúp giảm thiểu tắc nghẽn mạng, từ đó tối ưu hóa tốc độ xử lý của PySpark.

### 8. Thuật toán phù hợp cho lọc cộng tác với phản hồi ẩn

Vì dự án này yêu cầu mô hình hóa bằng **lọc cộng tác với phản hồi ẩn (collaborative filtering with implicit feedback)**, thuật toán phù hợp nhất là:

*   **Thuật toán Alternating Least Squares (ALS):**
    *   ALS là thuật toán phân rã ma trận (Matrix Factorization) tiêu chuẩn được cung cấp trong **Spark MLlib** để giải quyết các vấn đề lọc cộng tác quy mô lớn.
    *   ALS có một phiên bản được điều chỉnh đặc biệt để xử lý **phản hồi ẩn** (implicit feedback). Nó giả định rằng sự hiện diện của một bài hát trong playlist là một tín hiệu ẩn về sở thích của người dùng, thay vì xếp hạng rõ ràng.
    *   Sự phù hợp của ALS nằm ở khả năng xử lý hiệu quả ma trận tương tác playlist-bài hát **rất lớn và thưa** do quy mô của bộ dữ liệu MPD.

### 9. Xây dựng quy trình ETL, pipeline hợp lý, phù hợp đối với dự án

Quy trình ETL và pipeline cho dự án này phải được thiết kế để xử lý dữ liệu JSON quy mô lớn bằng PySpark/HDFS và tạo ra các yếu tố cần thiết cho ALS.

#### Giai đoạn 1: ETL và Tiền xử lý Dữ liệu

1.  **Trích xuất (Extract):**
    *   Đọc các tệp JSON MPD lớn từ HDFS bằng PySpark.
2.  **Chuyển đổi (Transform):**
    *   **Làm sạch:** Xử lý các trường dữ liệu JSON lồng nhau để trích xuất các thông tin quan trọng như `playlist_id`, `track_uri`, `track_name`, `artist_name`.
    *   **Chuẩn hóa:** Chuyển đổi dữ liệu thành các cột cần thiết cho mô hình ALS: **(user\_id, item\_id, rating)**.
        *   `user_id`: Là `playlist_id`.
        *   `item_id`: Là `track_uri` hoặc một ID số nguyên được ánh xạ từ `track_uri`.
        *   `rating`: Thiết lập một giá trị phản hồi ẩn (ví dụ: `1`) cho tất cả các tương tác (vì sự hiện diện của bài hát là tín hiệu sở thích).
    *   **Ánh xạ ID:** Sử dụng PySpark `StringIndexer` hoặc kỹ thuật ánh xạ để chuyển đổi các ID văn bản (`playlist_id`, `track_uri`) thành các chỉ số số nguyên (index) để thuật toán ALS có thể sử dụng.
3.  **Tải (Load):**
    *   Lưu trữ ma trận tương tác đã được chuẩn bị vào HDFS, ưu tiên sử dụng định dạng **Parquet** để tối ưu hóa truy cập.

#### Giai đoạn 2: Huấn luyện Mô hình Lọc Cộng tác

1.  **Chia Dữ liệu:** Chia ma trận tương tác thành tập huấn luyện và tập kiểm tra (validation set) để điều chỉnh siêu tham số.
2.  **Huấn luyện ALS:** Áp dụng thuật toán **ALS** (Alternating Least Squares) với các siêu tham số được điều chỉnh cho phản hồi ẩn.
3.  **Tối ưu hóa:** Sử dụng tập kiểm tra để đánh giá hiệu suất của mô hình và chọn ra bộ siêu tham số (rank, regularization, iterations) tốt nhất.

#### Giai đoạn 3: Dự đoán và Định dạng Bài nộp

1.  **Xử lý Tập Thử thách:** Đọc Bộ dữ liệu Thử thách (Test Set) 10.000 danh sách phát. Trích xuất `playlist_id` và các bản nhạc mồi ($K$ tracks).
2.  **Tạo Gợi ý:**
    *   Sử dụng mô hình ALS đã huấn luyện để dự đoán 500 bản nhạc hàng đầu cho từng `playlist_id`.
    *   PySpark có thể sử dụng chức năng `recommendForUserSubset` để tạo đề xuất cho toàn bộ tập kiểm tra.
3.  **Lọc và Xếp hạng:**
    *   **Lọc Bản nhạc Mồi:** Đảm bảo **loại bỏ tất cả các bản nhạc mồi (seed tracks) ban đầu** khỏi danh sách 500 đề xuất.
    *   **Sắp xếp:** Danh sách 500 bản nhạc phải được sắp xếp theo điểm số tự tin/xác suất dự đoán giảm dần.
4.  **Định dạng Cuối cùng:** Tập hợp các `track_uri` thành một chuỗi duy nhất, phân tách bằng dấu phẩy. Lưu kết quả dưới dạng tệp CSV nén gzip (`submission.csv`) với hai cột bắt buộc (`playlist_id` và `recommended_track_uris`).