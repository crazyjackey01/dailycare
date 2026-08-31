import os
import requests


OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434/api/chat")
MODEL_NAME = os.environ.get("OLLAMA_MODEL", "exaone3.5:7.8b")


def build_prompt(analysis_result):
    return f"""
너는 고령자 생활 패턴 모니터링 앱 DailyCare의 보호자 알림 문장을 작성하는 도우미다.

중요 규칙:
- 치매, 고독사라고 단정하지 마라.
- 진단처럼 말하지 마라.
- 보호자가 이해하기 쉽게 3~5문장으로 차분하게 요약해라.
- 데이터 변화와 확인 필요성을 중심으로 말해라.

분석 결과:
- 날짜: {analysis_result["date"]}
- 최종 위험도 점수: {analysis_result["finalScore"]}
- 위험 단계: {analysis_result["riskLevel"]}
- 연속 이상 일수: {analysis_result["consecutiveAbnormalDays"]}일
- 보정 배수: {analysis_result["multiplier"]}

공간별 데이터:
{analysis_result["zones"]}

보호자에게 보여줄 자연어 알림 문장을 작성해라.
"""


def ask_ollama(prompt):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        },
        timeout=20,
    )

    response.raise_for_status()
    data = response.json()
    return data["message"]["content"]