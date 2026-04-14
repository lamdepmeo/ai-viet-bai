# Hướng dẫn thiết lập n8n SEO Workflow

Bộ workflow này giúp bạn tự động hóa việc viết bài SEO/GEO chất lượng cao bằng cách kết hợp SERP phân tích, nghiên cứu sâu qua Linkup và viết bài dạng Chunking bằng Claude 3.5 Sonnet.

## 1. Chuẩn bị
- Một instance n8n đang hoạt động.
- API Key cho:
  - **LLM**: `llm.chiasegpu.vn`
  - **SERP**: `google.serper.dev` (hoặc dịch vụ tương đương)
  - **Research**: `Linkup.so`
- Một file Google Sheet có cột `Keyword` và `Status`.
- Một folder Google Drive để lưu kết quả.

## 2. Các file quan trọng
Tất cả các file hỗ trợ nằm trong folder `d:\AI demo`:
- `seo_workflow.json`: File workflow chính để import vào n8n.
- `seo_geo_rules.md`: File quy tắc tổng hợp SEO & GEO theo triết lý "Content Engineering".

## 3. Cách cài đặt
1. Mở n8n, chọn **Import from File** và chọn file `seo_workflow.json`.
2. Tại node **Config Node**, hãy điền các thông tin:
   - `googleSheetId`: ID của file Google Sheet.
   - `googleDriveFolderId`: ID của folder Drive.
   - Các API Key tương ứng.
3. Node **Read Rules**: Đảm bảo đường dẫn file là chính xác (`d:/AI demo/seo_geo_rules.md`).
4. Thiết lập **Credentials** cho Google Sheets và Google Drive/Docs trong n8n nếu bạn chưa làm.

## 4. Cách thức hoạt động
1. Workflow lấy Keyword từ Google Sheet.
2. Tìm kiếm top 10 kết quả Google (SERP).
3. Cào nội dung từ các website đó để phân tích ý chính.
4. Sử dụng Linkup để tìm kiếm các bằng chứng khoa học/thực tế (Deep Research).
5. AI đọc các quy tắc trong file `.md` đã cung cấp.
6. AI tạo Outline chi tiết.
7. AI viết bài theo từng Heading (Chunking) để đảm bảo độ dài và chất lượng, tránh bị lặp ý.
8. Xuất bài viết hoàn chỉnh ra Google Doc.
