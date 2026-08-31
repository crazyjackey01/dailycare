ZONE_WEIGHTS = {
    "kitchen": 0.25,
    "frontDoor": 0.25,
    "bedroom": 0.20,
    "bathroom": 0.15,
    "livingRoom": 0.15,
}


def calculate_baseline(records, max_days=7):
    if not records:
        raise ValueError("No past records available")

    recent_records = records[-max_days:]

    baseline = {zone: 0 for zone in ZONE_WEIGHTS}

    for record in recent_records:
        for zone in ZONE_WEIGHTS:
            baseline[zone] += record.get(zone, 0)

    for zone in baseline:
        baseline[zone] = round(baseline[zone] / len(recent_records), 2)

    return baseline


def calculate_deviation(today_value, baseline_value):
    if baseline_value == 0:
        return 0

    return abs(today_value - baseline_value) / baseline_value * 100


def deviation_to_score(deviation):
    if deviation <= 20:
        return 0
    elif deviation <= 40:
        return 25
    elif deviation <= 60:
        return 50
    elif deviation <= 80:
        return 75
    else:
        return 100


def get_multiplier(consecutive_days):
    if consecutive_days <= 1:
        return 1.0
    elif consecutive_days == 2:
        return 1.2
    elif consecutive_days == 3:
        return 1.4
    else:
        return 1.6


def get_risk_level(score):
    if score >= 70:
        return "위험"
    elif score >= 40:
        return "주의"
    else:
        return "정상"


def analyze_pattern(today, past_records, consecutive_abnormal_days=1):
    baseline = calculate_baseline(past_records)

    zones = {}
    daily_score = 0

    for zone, weight in ZONE_WEIGHTS.items():
        today_value = today.get(zone, 0)
        baseline_value = baseline.get(zone, 0)

        deviation = calculate_deviation(today_value, baseline_value)
        abnormality_score = deviation_to_score(deviation)
        weighted_score = abnormality_score * weight

        zones[zone] = {
            "today": today_value,
            "baseline": baseline_value,
            "deviationPercent": round(deviation, 2),
            "abnormalityScore": abnormality_score,
            "weight": weight,
            "weightedScore": round(weighted_score, 2),
        }

        daily_score += weighted_score

    multiplier = get_multiplier(consecutive_abnormal_days)
    final_score = min(100, daily_score * multiplier)

    return {
        "date": today.get("date"),
        "baseline": baseline,
        "zones": zones,
        "dailyPatternRiskScore": round(daily_score, 2),
        "consecutiveAbnormalDays": consecutive_abnormal_days,
        "multiplier": multiplier,
        "finalScore": round(final_score, 2),
        "riskLevel": get_risk_level(final_score),
    }


def generate_rule_based_message(result):
    messages = []

    messages.append(
        f"오늘 생활 패턴 위험도는 {result['finalScore']}점이며, 상태는 '{result['riskLevel']}'입니다."
    )

    for zone, data in result["zones"].items():
        if data["abnormalityScore"] >= 50:
            zone_name = {
                "kitchen": "주방",
                "frontDoor": "현관",
                "bedroom": "침실",
                "bathroom": "화장실",
                "livingRoom": "거실",
            }.get(zone, zone)

            messages.append(
                f"{zone_name} 체류/방문 시간이 평소 대비 {data['deviationPercent']}% 차이를 보였습니다."
            )

    if result["riskLevel"] != "정상":
        messages.append("보호자가 한 번 확인해보는 것이 좋습니다.")

    return "\n".join(messages)