# naver-blog-archiver v2

네이버 블로그를 SQLite DB + 로컬 이미지로 **증분 백업**하고, 다크 테마 웹 UI로 열람·검색하는 도구.

원본: https://github.com/guzus/naver-blog-archiver 를 포크해 개선한 것을 전면 재작성.

![다크 웹 UI](https://img.shields.io/badge/UI-dark-1E1E24) ![단일 파일](https://img.shields.io/badge/구조-단일파일-3DDC97)

## 주요 기능

| 기능 | 설명 |
|---|---|
| 증분 동기화 | 새 글/변경된 글만 수집. 매번 전체 재다운로드하던 레거시 문제 해결 |
| 수정 감지 + 이력 | 제목·미리보기 변화로 수정 감지, 이전 버전 스냅샷을 `posts_history`에 보존 |
| 삭제 글 보존 | 블로그에서 삭제/비공개된 글도 아카이브에는 남고 `missing` 배지로 표시 |
| 이미지 원본 화질 | `blogfiles` 호스트/`type=w3840`으로 원본 다운로드. 실제 확장자(jpg/png/gif/webp) 저장 |
| 풍부한 메타데이터 | 정확한 발행시각, 카테고리, 공감·댓글 수, 에디터 버전, 썸네일 |
| 웹 UI | 대시보드·검색·카테고리 필터·오프라인 본문 뷰어(로컬 이미지)·동기화 진행 표시 |
| 네이버 재발행 | 글 페이지의 "재발행용 복사" → 글쓰기 창에 Ctrl+V로 서식·이미지 복원 (글쓰기 API는 2020년 종료라 클립보드 방식) |
| 내보내기 | Jekyll(레거시 SavedPost 포맷 호환) / 순수 Markdown / JSON 덤프 |
| 카테고리 slug | googletrans 제거 → 내장 한글 로마자 변환 + 웹 UI에서 직접 수정 가능 |
| GitHub Pages 자동 배포 | `publish` 한 번으로 내보내기→블로그 저장소 반영→commit→push. 동기화 후 자동 배포 옵션 |

## 설치

```bash
pip install -r requirements.txt
```

## 사용법

```bash
# 동기화 (기본: 증분 — 새 글/변경 글만)
python _code/blog_archiver.py sync
python _code/blog_archiver.py sync --full        # 전체 재수집 (수정 이력 보존)
python _code/blog_archiver.py sync --limit 5     # 테스트용 개수 제한

# 웹 UI (브라우저 자동 오픈, 기본 포트 8765)
python _code/blog_archiver.py web

# 내보내기
python _code/blog_archiver.py export --format jekyll     # GitHub Pages용
python _code/blog_archiver.py export --format markdown   # 로컬 보관/옵시디언용
python _code/blog_archiver.py export --format json       # DB 전체 덤프

# 기타
python _code/blog_archiver.py stats              # 아카이브 통계
python _code/blog_archiver.py publish            # Jekyll 내보내기 → 블로그 저장소 commit+push
python _code/blog_archiver.py search "검색어"     # 제목·본문 검색
python _code/blog_archiver.py rebuild            # 저장된 HTML로 markdown 재생성 (재다운로드 없음)
```

첫 실행 시 `config.json`이 생성된다. 블로그 ID·요청 간격·제외 카테고리 등은
`config.json` 또는 웹 UI의 **설정** 페이지에서 변경.

## 저장 구조

```
archive/<blog_id>/
├─ archive.db          # SQLite: 글 본문(HTML+Markdown)·이미지 메타·카테고리·수정이력·동기화 로그
├─ images/<logNo>/     # 글별 이미지 (원본 화질, 실제 확장자)
└─ exports/            # 내보내기 산출물 (jekyll/, markdown/, archive_dump.json)
```

- **백업은 전부 저장**된다. `excluded_categories` 설정은 Jekyll 내보내기에만 적용.
- 이미지 파일명은 원본 URL 해시 기반 → 글이 수정돼도 기존 이미지는 재다운로드하지 않음.

## GitHub Pages 자동 연동

`config.json`의 `jekyll_repo_dir`에 블로그 저장소 로컬 경로를 지정하면:

- `publish` 명령(또는 웹 UI 내보내기 페이지의 **블로그 배포** 버튼)이
  `_posts/NaverBackup/`, `_images/`, `_pages/categories/`, `_includes/nav_list_main`
  **관리 영역만** 통째로 교체한 뒤 commit·push한다. 직접 쓴 다른 글·파일은 건드리지 않는다.
- `publish_after_sync: true`면 동기화에서 변경이 감지될 때 자동으로 배포까지 이어진다.

## 레거시 (v1)

기존 스크립트(`main.py`, `article.py` 등)는 `legacy/` 폴더로 이동. v1의 문제:
매 실행 전체 재다운로드, 이미지 리사이즈본(`?type=w773`)을 `.png` 확장자로 일괄 저장,
googletrans 의존(빈번한 장애), 글 하나 실패 시 전체 중단, blog_id 하드코딩.

## 주의

- 요청 간격 기본 0.5초. 네이버 서버에 부담을 주지 않도록 과하게 줄이지 말 것.
- 본인 블로그 백업 용도로 만들어졌다. 타인 블로그의 대량 수집은 이용약관을 확인할 것.
- 동영상·첨부파일·스티커는 다운로드하지 않고 DB의 `media` 테이블에 존재만 기록된다.
