# core/payload_builder.py

def build_interview_payload(llm_results):
    """
    llm_results → list of dict dari evaluate_answer_llm()
    Contoh:
    [
        {"qid": "Q01", "llm_score": 3, ...},
        {"qid": "Q02", "llm_score": 4, ...},
        ...
    ]
    """

    scores = []
    for idx, item in enumerate(llm_results, start=1):
        scores.append({
            "id": idx,
            "score": item["llm_score"]
        })

    final_payload = {
        "minScore": 0,
        "maxScore": 4,
        "scores": scores
    }

    return final_payload
