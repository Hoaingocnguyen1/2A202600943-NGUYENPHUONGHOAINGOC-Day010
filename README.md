# Day 10 - Data Pipeline And Data Observability

Chào các bạn đến với bài lab Day 10.

Mục tiêu của bài này là xây dựng một ETL pipeline nhỏ nhưng đầy đủ cho một hệ thống RAG:

- Lấy dữ liệu học thuật từ nguồn bên ngoài
- Làm sạch và chuẩn hóa thành cleaned dataset
- Tạo embedding và nạp vào ChromaDB
- Xây agent để trả lời câu hỏi trên bộ dữ liệu
- Đánh giá chất lượng của agent trước và sau khi dữ liệu bị corrupt
- Tạo báo cáo data quality, freshness và metrics comparison

Cấu trúc chính:

- `src/core/`: config và utility dùng chung
- `src/ingestion/`: load source, clean, corrupt data
- `src/retrieval/`: embeddings, vector store, LLM providers, agent
- `src/evaluation/`: test set và scoring
- `src/observability/`: quality checks, freshness, reports
- `src/pipelines/`: flow baseline và flow corruption
- `script/`: entrypoint để chạy lab
- `data/`: nơi chứa artifact đầu ra

Tài liệu hướng dẫn:

- [Guide.md](Guide.md)
- [Rubric.md](Rubric.md)

Gợi ý cách bắt đầu:

```bash
uv sync
uv run python script/run_phase1.py
```

Nếu dùng `pip` thay vì `uv`, các bạn có thể cài bằng:

```bash
pip install -r requirements.txt
```

Nếu code chưa chạy được thì đó là bình thường. Các bạn cần hoàn thành các file pseudo-code trước, sau đó mới có thể chạy end-to-end.

## CLI

Ngoài 2 script cố định, có một CLI gộp để dễ reproduce:

```bash
# chạy baseline
python script/run.py phase1
# chạy corruption flow
python script/run.py corruption
# chạy cả hai, ép fetch lại nguồn và bật Ragas
python script/run.py all --refresh-source --run-ragas
# override provider/model
python script/run.py phase1 --provider openai --model gpt-4o-mini
```

Các flag chỉ set biến môi trường tương ứng (`REFRESH_SOURCE`, `REFRESH_TEST_SET`, `RUN_RAGAS`, `LLM_PROVIDER`, `LLM_MODEL`) trước khi gọi pipeline.

## Tests

Bộ test chạy hoàn toàn offline (không cần API key hay network):

```bash
pytest
```

Bao phủ: parse Crossref, cleaning, test-set builder, corruption, data-quality và freshness checks.
