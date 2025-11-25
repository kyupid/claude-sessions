# Claude Code Session Detector

로컬에서 실행 중인 Claude Code 세션을 실시간으로 모니터링하는 TUI 도구.

## 실행 방법

```bash
# 의존성 설치
pip install -r requirements.txt

# 실행
python claude_sessions.py
```

## 표시 정보

| 컬럼 | 설명 |
|------|------|
| PID | 프로세스 ID |
| Directory | 작업 디렉토리 (~ 축약) |
| Terminal | 터미널 (ttys001 등) |
| Uptime | 실행 시간 |
| Status | Running/Idle |

## 설정

- **업데이트 주기**: 3초 (코드 내 `time.sleep(3)` 수정)
- **종료**: `Ctrl+C`

## 기술 스택

- Python 3.10+
- rich: TUI 렌더링
- psutil: 프로세스 정보 수집

## 파일 구조

```
├── claude_sessions.py   # 메인 실행 파일
├── requirements.txt     # 의존성
└── CLAUDE.md           # 이 문서
```

## 핵심 함수

- `get_claude_sessions()`: psutil로 claude 프로세스 검색
- `create_table()`: rich Table 생성
- `create_display()`: Panel로 감싸서 출력

## 확장 아이디어

- CPU/메모리 사용량 추가
- 세션 종료 기능 (kill)
- 설정 파일 지원
