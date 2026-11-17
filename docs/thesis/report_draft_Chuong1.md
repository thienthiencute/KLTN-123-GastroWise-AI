## 1.2 Mục tiêu đề tài

Để hiện thực hóa giải pháp nền tảng ẩm thực thông minh một cách toàn diện, nhóm nghiên cứu xác định hệ thống GastroWise không chỉ là một trang web tra cứu đơn thuần, mà là một hệ sinh thái kết hợp chặt chẽ giữa quản trị dữ liệu lớn, Trí tuệ Nhân tạo và thuật toán không gian. Mục tiêu được chia thành các giai đoạn cụ thể như sau:

**Xây dựng hạ tầng kết nối và kiến trúc máy chủ (Cloud & Backend Layer):**
Giai đoạn này tập trung vào việc thiết kế bộ khung vững chắc cho toàn bộ hệ thống, đảm bảo tốc độ và khả năng chịu tải:
- Thiết lập kiến trúc Microservices: Phân chia hệ thống thành các dịch vụ nhỏ (Core Service, Routing Service, Auth Service) để dễ dàng bảo trì và mở rộng trong tương lai bằng framework NestJS.
- Hệ thống cơ sở dữ liệu không gian (Spatial Database): Sử dụng PostgreSQL kết hợp với module chuyên dụng PostGIS. Điều này cho phép lưu trữ và tính toán khoảng cách địa lý giữa các nhà hàng dựa trên hệ tọa độ kinh/vĩ độ (Geography Type) với tốc độ cao.
- Bộ nhớ đệm (Cache System): Tích hợp Redis để lưu trữ tạm thời các kết quả truy vấn lộ trình phức tạp, giúp giảm thiểu độ trễ (latency) khi người dùng tra cứu lại dữ liệu cũ.

**Phát triển hệ sinh thái ứng dụng đa nền tảng (User & Admin Interface Layer):**
Mục tiêu là tối ưu hóa trải nghiệm người dùng (UX) và năng suất quản lý cho chủ nhà hàng:
- Giao diện Admin/Merchant: Xây dựng bảng điều khiển quản trị (Dashboard) bằng Next.js (App Router), cho phép chủ quán dễ dàng quản lý thực đơn, theo dõi đánh giá và thống kê doanh thu.
- Ứng dụng Khách hàng (Client UI): Cung cấp giao diện trực quan, cá nhân hóa cho từng người dùng, hỗ trợ thu thập hồ sơ sở thích (preferences) như món ăn yêu thích, các nguyên liệu gây dị ứng để làm cơ sở cho thuật toán gợi ý.

**Tích hợp Trí tuệ Nhân tạo vào nghiệp vụ quản lý (AI Integration):**
Nhóm hướng tới việc áp dụng AI để tự động hóa các tác vụ thủ công, mang lại giá trị thực tiễn cho chủ nhà hàng:
- AI Copilot: Tích hợp trợ lý ảo thông minh trực tiếp vào giao diện quản trị. Trợ lý này không chỉ trả lời văn bản mà còn có khả năng sinh ra giao diện (Generative UI) dưới dạng biểu đồ doanh thu ngay trong khung chat.
- AI Menu Generator: Phát triển công cụ đọc hiểu hình ảnh (Computer Vision). Người dùng chỉ cần tải ảnh món ăn lên, AI sẽ tự động phân tích và sinh ra tên món, đoạn mô tả hấp dẫn (chuẩn Copywriting) và đề xuất mức giá cạnh tranh trên thị trường.

**Nghiên cứu thuật toán gợi ý và tối ưu hóa lộ trình (Smart Routing Algorithm):**
Đây là mục tiêu mang tính khoa học cốt lõi nhất của đề tài, giải quyết trực tiếp bài toán "Du lịch ẩm thực":
- Truy vấn không gian (Spatial Filtering): Lọc ra danh sách các nhà hàng nằm trong bán kính cho phép tính từ vị trí người dùng, thỏa mãn các ràng buộc cứng về ngân sách, thời gian hoạt động và sở thích cá nhân.
- Tối ưu lộ trình đa điểm (Multi-stop Routing Optimization): Ứng dụng các biến thể của thuật toán tìm đường (như Dijkstra kết hợp Heuristic) để vạch ra một lộ trình di chuyển liên hoàn qua nhiều địa điểm ăn uống, đảm bảo tổng khoảng cách di chuyển là ngắn nhất mà vẫn mang lại trải nghiệm ẩm thực đa dạng nhất.

**Thử nghiệm, đánh giá và triển khai (Deployment & Testing):**
Giai đoạn cuối cùng tập trung vào việc kiểm chứng độ ổn định của sản phẩm trong môi trường thực tế:
- Triển khai tự động (CI/CD): Đóng gói Backend bằng Docker và tự động hóa quy trình triển khai Frontend lên nền tảng đám mây Vercel, đảm bảo hệ thống luôn khả dụng 24/7.
- Kiểm thử hiệu năng và độ chính xác: Đánh giá thời gian phản hồi của thuật toán Routing (đảm bảo dưới 2 giây) và kiểm tra độ chính xác của các đề xuất từ AI Menu Generator.

## 1.3 Phạm vi nghiên cứu

**Phạm vi công nghệ:**
Nhóm xác định việc xây dựng một hệ thống tối ưu hóa lộ trình và gợi ý ẩm thực cá nhân hóa đòi hỏi sự kết hợp khắt khe giữa xử lý dữ liệu không gian phức tạp và giao diện tương tác tốc độ cao. Do đó, phạm vi công nghệ được lựa chọn dựa trên các tiêu chí: tính ổn định, khả năng chịu tải và năng lực phân tích dữ liệu lớn.

*Công nghệ phía Client (Front-end):*
Nhóm tập trung xây dựng giao diện người dùng dựa trên các thư viện hiện đại nhất nhằm tối ưu hóa trải nghiệm tương tác bản đồ và tốc độ tải trang:
- **Framework cốt lõi (Next.js 15 & React):** Nhóm sử dụng Next.js với kiến trúc App Router kết hợp Server-Side Rendering (SSR) để tối ưu hóa SEO cho các trang thông tin nhà hàng và tăng tốc độ hiển thị ban đầu.
- **Quản lý giao diện (Tailwind CSS v4):** Ứng dụng Utility-first CSS giúp tùy chỉnh giao diện Admin Dashboard và User Web một cách linh hoạt, tạo ra các thiết kế hiện đại (Glassmorphism, Dark mode) tương thích với mọi kích thước màn hình.
- **Quản lý trạng thái và dữ liệu (React Query):** Đảm nhiệm việc fetch dữ liệu API, tự động caching và đồng bộ hóa trạng thái giữa Client và Server, giúp trải nghiệm tra cứu món ăn trở nên mượt mà, không giật lag.

*Công nghệ phía Máy chủ (Back-end):*
Lớp Backend đóng vai trò là "bộ não" tính toán thuật toán và điều phối thông tin, được xây dựng theo chuẩn doanh nghiệp:
- **Môi trường thực thi (NestJS & Node.js):** Lựa chọn NestJS vì kiến trúc Module hóa chặt chẽ và Dependency Injection mạnh mẽ, cực kỳ phù hợp để xây dựng mô hình Microservices, giúp tách bạch các dịch vụ (Auth, Core, Routing) rõ ràng.
- **Bảo mật hệ thống (JWT - JSON Web Token):** Triển khai cơ chế xác thực JWT và mã hóa mật khẩu `bcrypt` để bảo vệ tài khoản người dùng và chủ nhà hàng, đảm bảo tính phân quyền nghiêm ngặt.
- **Đóng gói hệ thống (Docker):** Toàn bộ môi trường Backend, Database và Cache được đóng gói bằng Docker Container (`docker-compose`), giúp đồng nhất môi trường từ khâu lập trình (Local) đến lúc vận hành (Production).

*Hệ quản trị cơ sở dữ liệu (Database & Cache):*
Vì đặc thù của đề tài yêu cầu tính toán khoảng cách bản đồ liên tục, nhóm sử dụng các giải pháp lưu trữ chuyên sâu:
- **PostgreSQL & PostGIS:** Sử dụng CSDL quan hệ PostgreSQL kết hợp với tiện ích mở rộng không gian PostGIS. Đây là điểm nhấn công nghệ, cho phép thực hiện các phép toán phức tạp trực tiếp dưới tầng Database như: "Tìm nhà hàng trong bán kính 3km" bằng kiểu dữ liệu `Geography`.
- **Redis Cache:** Triển khai cơ chế lưu trữ bộ nhớ đệm (In-memory caching). Lịch sử các lộ trình đã được AI tính toán sẽ được đưa vào Redis, giúp hệ thống trả về kết quả ngay lập tức ở các truy vấn tương tự mà không cần chạy lại thuật toán.

**Phân tích và lựa chọn giải pháp lưu trữ dữ liệu:**
Trong quá trình thiết kế hệ thống, nhóm đã cân nhắc kỹ lưỡng giữa cơ sở dữ liệu quan hệ (SQL) và phi quan hệ (NoSQL). Dưới đây là bảng phân tích làm cơ sở cho sự lựa chọn:

*Bảng 1-1: Phân tích và lựa chọn giải pháp lưu trữ dữ liệu*

| Tiêu chí so sánh | Hệ quản trị CSDL Quan hệ (SQL - PostgreSQL) | Hệ quản trị CSDL Phi quan hệ (NoSQL - MongoDB) |
|---|---|---|
| **Cấu trúc dữ liệu** | Có cấu trúc chặt chẽ, định nghĩa qua các bảng và sơ đồ (Schema), bảo toàn tính toàn vẹn. | Linh hoạt, dạng tài liệu (Document), cấu trúc có thể thay đổi liên tục. |
| **Tính nhất quán** | Tuân thủ nghiêm ngặt tính chất ACID, chống sai lệch dữ liệu. | Ưu tiên tính sẵn sàng và khả năng mở rộng (BASE consistency). |
| **Xử lý dữ liệu không gian** | **Rất mạnh (thông qua PostGIS)**, hỗ trợ gốc các chuẩn hình học, tính toán khoảng cách tọa độ GPS nhanh chóng. | Có hỗ trợ cơ bản (GeoJSON 2dsphere) nhưng thiếu các hàm phân tích không gian phức tạp. |
| **Độ tin cậy** | Phù hợp cho các dữ liệu cần liên kết chặt chẽ (Nhà hàng - Món ăn - Đánh giá). | Phù hợp cho dữ liệu log, tốc độ ghi nhanh nhưng khó truy vấn chéo (Join). |

*Lý do lựa chọn:* Nhóm quyết định sử dụng **PostgreSQL kết hợp PostGIS** vì cốt lõi của đề tài là thuật toán tìm đường. PostGIS cung cấp các hàm toán học không gian vượt trội giúp truy vấn tọa độ nhà hàng chính xác tuyệt đối. Đồng thời, để khắc phục nhược điểm cứng nhắc của SQL, nhóm sử dụng kiểu dữ liệu `JSONB` trong PostgreSQL để lưu trữ "Sở thích người dùng", mang lại sự linh hoạt không kém NoSQL.

**Phân tích và lựa chọn kiến trúc phần mềm:**
Để hệ thống có khả năng xử lý đồng thời lượng lớn người dùng tra cứu bản đồ, nhóm đã phân tích hai mô hình kiến trúc:

*Bảng 1-2: Phân tích mô hình kiến trúc hệ thống*

| Kiến trúc Monolithic (Nguyên khối) | Kiến trúc Microservices (Vi dịch vụ) |
|---|---|
| Toàn bộ tính năng (Auth, Menu, Routing) nằm chung trong một mã nguồn. | Chia nhỏ thành nhiều dịch vụ độc lập, giao tiếp qua API Gateway. |
| Dễ dàng phát triển ở giai đoạn đầu, triển khai đơn giản. | Phức tạp trong việc thiết lập hạ tầng và kết nối ban đầu. |
| Khi một tính năng bị lỗi, toàn bộ hệ thống có nguy cơ sập (Crash). | Lỗi ở dịch vụ này (VD: Lỗi AI) không làm sập dịch vụ khác (VD: Xem Menu). |
| Khó mở rộng tài nguyên cho một tính năng cụ thể. | Dễ dàng cấp thêm tài nguyên riêng cho dịch vụ nặng (như Thuật toán Routing). |

*Lý do lựa chọn:* Nhóm lựa chọn **Kiến trúc Microservices** bằng NestJS. Thuật toán tối ưu lộ trình và xử lý AI tiêu tốn rất nhiều CPU. Việc tách chúng thành các dịch vụ độc lập giúp hệ thống chính (tra cứu món ăn) không bị nghẽn khi có nhiều người đang chạy tính năng tạo lộ trình cùng lúc.

**Đối tượng nghiên cứu:**
Đối tượng nghiên cứu của đề tài được phân tách thành ba thành phần cốt lõi, tương ứng với luồng xử lý thông tin của hệ thống:

*Đối tượng dữ liệu không gian và thực thể ẩm thực:*
Đây là nguồn dữ liệu gốc, mang tính định lượng để phục vụ thuật toán:
- **Vị trí và Thông tin Nhà hàng:** Tọa độ GPS (Kinh độ/Vĩ độ), thời gian mở/đóng cửa, sức chứa và mức giá trung bình.
- **Thực đơn (Menu Items):** Danh mục món ăn, hình ảnh, nguyên liệu chế biến và mức giá chi tiết.

*Đối tượng dữ liệu cá nhân hóa (User Preferences):*
Nguồn dữ liệu mang tính định tính, giúp cá nhân hóa trải nghiệm người dùng:
- **Sở thích và Giới hạn:** Gu ẩm thực (chay, mặn, đồ ngọt, món Âu/Á), tiền sử dị ứng (hải sản, đậu phộng), và giới hạn ngân sách chi trả cho một chuyến đi.
- **Lịch sử và Đánh giá (Review/Sentiment):** Dữ liệu phản hồi của khách hàng. Hệ thống áp dụng AI để phân tích sắc thái bình luận (Sentiment Analysis) giúp chủ nhà hàng nắm bắt cảm xúc khách hàng.

*Đối tượng giải pháp phần mềm và Thuật toán AI:*
Nghiên cứu cách thức vận hành các công nghệ thông minh:
- **Thuật toán Tối ưu Lộ trình (Smart Routing):** Nghiên cứu các biến thể của thuật toán Dijkstra hoặc Heuristic kết hợp với trọng số là "Ngân sách" và "Đánh giá", nhằm vạch ra lộ trình đi qua nhiều quán ăn với chi phí rẻ nhất và quãng đường ngắn nhất.
- **Ứng dụng Trí tuệ Nhân tạo (Generative AI & Computer Vision):** Nghiên cứu tích hợp Chatbot AI Copilot có khả năng sinh biểu đồ động (Generative UI) cho quản trị viên, và tính năng tự động trích xuất thông tin món ăn từ hình ảnh (AI Menu Generator) giúp giảm thiểu thao tác nhập liệu thủ công.

## 1.4 Mô tả yêu cầu

Quá trình thu thập và phân tích hệ thống GastroWise đã xác định các yêu cầu chức năng và phi chức năng cốt lõi như sau:

### 1.4.1 Yêu cầu chức năng (Functional Requirements)

- **Phân hệ Khách hàng (User Web):**
  - **Quản lý tài khoản:** Đăng nhập, đăng ký và cập nhật hồ sơ cá nhân. Hệ thống yêu cầu lưu trữ các dữ liệu về sở thích ăn uống, tiền sử dị ứng (Preferences) của người dùng để phục vụ thuật toán cá nhân hóa.
  - **Tra cứu và đánh giá:** Cho phép tìm kiếm nhà hàng theo danh mục, khu vực, khoảng giá. Người dùng có quyền để lại bình luận (Review) và chấm điểm trải nghiệm.
  - **Tối ưu hóa lộ trình (Routing Optimization):** Đây là chức năng cốt lõi, người dùng nhập vào vị trí hiện tại, thời gian mong muốn và ngân sách. Hệ thống sẽ sử dụng thuật toán kết hợp truy vấn không gian (Spatial Queries) thông qua PostGIS để tính toán và trả về một lộ trình di chuyển tối ưu nhất đi qua các điểm ẩm thực thỏa mãn điều kiện.
- **Phân hệ Quản trị và Đối tác (Admin/Merchant FE):**
  - **Quản lý Thực đơn (Menu Management):** Chủ quán có thể thêm, sửa, xóa món ăn. 
  - **Tích hợp Trí tuệ Nhân tạo (Enterprise AI Extensions):**
    - **Trợ lý ảo (AI Copilot):** Tích hợp chatbot nội bộ cung cấp giao diện sinh tự động (Generative UI) dưới dạng widget biểu đồ, giúp quản trị viên truy vấn nhanh số liệu.
    - **Tạo món ăn tự động (AI Menu Generator):** Chức năng phân tích hình ảnh món ăn tải lên, tự động trích xuất thông tin, mô tả chuẩn SEO và đề xuất mức giá bán hợp lý thông qua mô hình học sâu.

### 1.4.2 Yêu cầu phi chức năng (Non-Functional Requirements)

- **Hiệu năng và Thời gian phản hồi:** Các truy vấn về gợi ý nhà hàng và vẽ lộ trình phải được phản hồi trong vòng dưới 2 giây. Sử dụng Redis Cache để lưu trữ bộ đệm các lộ trình đã tính toán nhằm giảm thiểu tải cho Database ở các lượt truy cập sau.
- **Bảo mật hệ thống:** Toàn bộ quá trình xác thực và phân quyền (Authentication/Authorization) phải tuân thủ chuẩn JSON Web Token (JWT). Mật khẩu của người dùng phải được mã hóa băm (Hashing) bằng thuật toán `bcrypt` trước khi lưu vào CSDL PostgreSQL.
- **Tính khả dụng và Triển khai:** Hệ thống cần được đóng gói tự động hóa bằng Docker. Mã nguồn giao diện quản trị (Next.js) được cấu hình CI/CD để triển khai tự động lên nền tảng đám mây (Vercel), đảm bảo tính sẵn sàng hoạt động 24/7 (Uptime > 99%).
