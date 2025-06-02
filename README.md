# 🛍️ Voice Agent for E-commerce Customer Support (Inbound, Multi-Agent)

이 프로젝트는 LiveKit Agents를 기반으로 구축된 다중 에이전트 기반 Inbound 음성 상담 시스템입니다. 이커머스 고객이 전화로 문의하면 AI 에이전트가 자동으로 응답하고, 문의 내용에 따라 적절한 전문가 역할의 Agent로 연결해줍니다.


## 📦 주요 기능
- ☎️ Twilio Voice 기반 Inbound 콜 처리
- 🧠 다중 LLM Agent 구성 (Triage → Pre/Post/After Sales)
- 🔁 Agent 간 자연스러운 전환과 context 유지
- 🗣️ Deepgram STT, Cartesia TTS, Silero VAD 통합
- 🧪 샘플 상품/주문/반품 데이터로 테스트 가능

## 🧠 Agent 구성

- TriageAgent (초기 진입점): 적절한 세부 에이전트로 연결
- PrePurchaseAgent: 상품 및 구매 전 문의 처리
- PostPurchaseAgent: 주문 상태 확인 및 구매 후 지원
- AfterSalesAgent: 반품, 환불 등 사후 처리 담당


## ☁️ Twilio & SIP 연동

이 프로젝트는 Twilio Programmable Voice + SIP → LiveKit 연결 방식으로 작동합니다. 
[공식 문서](https://docs.livekit.io/sip/accepting-calls-twilio-voice/)를 참고해 설정을 진행하세요.

설정 완료 후 Twilio 번호로 전화를 걸면 에이전트가 자동으로 응답합니다.

## 설치 및 환경 설정

1. 저장소 복제

   ```bash
   git clone https://github.com/Marker-Inc-Korea/ecommerce-triage-agent.git
   cd ecommerce-triage-agent
   ```
2. 의존성 설치

    uv를 이용해 필요한 파이썬 패키지를 한 번에 설치합니다.

   ```bash
   uv sync
   ```
3. 환경 변수 구성

   * `.env.example`를 `.env`로 복사 후 다음 값을 채워 넣습니다:

     ```dotenv
     LIVEKIT_API_KEY=...
     LIVEKIT_API_SECRET=...
     LIVEKIT_URL=wss://your.livekit.server
     ...
     ```

## 💻 Agent 실행

```python
python agent.py dev
```


## 📞 콜 흐름
1.	고객이 Twilio 전화번호로 전화
2.	Twilio → SIP → LiveKit으로 연결
3.	TriageAgent가 인사 및 라우팅
4.	사용자 요청에 따라 전문 Agent로 전환
5.	각 Agent는 툴 호출 (tool call)을 통해 사용자 요청 처리


## 🧪 에이전트 function 예시
- `list_products()` — 음성 친화적인 상품 목록 안내
- `check_order_status(order_id)`
- `request_return(order_id)`
- `transfer_to_*()` — 자연스러운 Agent 전환


## 🏷️ License

MIT © Marker-Inc-Korea