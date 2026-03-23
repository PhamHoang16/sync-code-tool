# GitHub to Bitbucket Sync Tool

Script Python tự động đồng bộ (sync) các nhánh từ GitHub sang Bitbucket (mạng nội bộ).

## Yêu cầu
- Máy/Server đã cài đặt sẵn `git` và `python3`.

## Hướng dẫn sử dụng nhanh

Có 2 cách sử dụng an toàn (không ghi trực tiếp token vào command hay file lưu trữ) được đề xuất:

### Cách 1: Sử dụng kết nối SSH (Khuyên dùng cho Server)
Bảo mật bằng chứng chỉ SSH Client có sẵn trên máy (cần cấu hình ssh-key trước cho cả Github và Bitbucket).

**1. Đồng bộ 1-1 các nhánh cụ thể (Mapping)**
Kéo nhánh `main`, `dev` từ GitHub đẩy lên `prod`, `stag` trên Bitbucket:
```bash
python3 github_to_bitbucket_sync.py \
  --auth-method ssh \
  --src-url "git@github.com:my-org/repo.git" \
  --dest-url "ssh://git@bitbucket.company.com:7999/proj/repo.git" \
  --src-branches "main" "dev" \
  --dest-branches "prod" "stag"
```

**2. Tự động kéo & đẩy TẤT CẢ các nhánh (`--sync-all`)**
```bash
python3 github_to_bitbucket_sync.py \
  --auth-method ssh \
  --sync-all \
  --src-url "git@github.com:my-org/repo.git" \
  --dest-url "ssh://git@bitbucket.company.com:7999/proj/repo.git"
```

---

### Cách 2: Sử dụng Biến môi trường (Khuyên dùng cho CI/CD)
Phù hợp khi chạy bằng Pipeline (Jenkins, Github Actions,...), sử dụng Personal Access Token (PAT) và App Password.

```bash
# Truyền mã Token thông qua biến môi trường của hệ thống
SYNC_SRC_TOKEN="ghp_xxxx" \
SYNC_DEST_TOKEN="BBDC-xxxx" \
python3 github_to_bitbucket_sync.py \
  --auth-method env \
  --sync-all \
  --src-url "https://github.com/my-org/repo.git" \
  --dest-url "http://bitbucket.company.com/scm/proj/repo.git" \
  --src-user "github_user" \
  --dest-user "bitbucket_user"
```

### Chạy bằng file cấu hình config.json (Tùy chọn)
Nếu câu lệnh quá dài, bạn có thể thiết lập bằng file `config.json` cho cả 2 cách trên. Thuộc tính `auth_method` có thể được cấu hình ngay bên trong file JSON để tool tự nhận diện.

**Ví dụ cấu hình SSH trong config.json (Không lưu token):**
Bạn chỉnh sửa file `config.json` với cấu trúc sau:
```json
{
    "src_url": "git@github.com:my-org/repo.git",
    "dest_url": "ssh://git@bitbucket.company.com:7999/proj/repo.git",
    "auth_method": "ssh",
    "sync_all": true
}
```
Và sau đó chỉ cần gọi 1 lệnh ngắn gọn duy nhất:
```bash
python3 github_to_bitbucket_sync.py --config config.json
```
