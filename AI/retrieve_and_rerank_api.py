from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel
from rank_bm25 import BM25Okapi

app = FastAPI()

# API 요청 형식
class QueryRequest(BaseModel):
    question: str
    top_k: int

# Top K 구하기
def get_top_k_similar_pairs(question, pairs, model, tokenizer, k=3):
    inputs = tokenizer([[question, pair[0]] for pair in pairs], padding=True, truncation=True, return_tensors='pt', max_length=512)
    
    with torch.no_grad():
        scores = model(**inputs, return_dict=True).logits.view(-1, ).float()

    scores = scores.numpy()
    
    top_k_indices = np.argsort(scores)[-k:][::-1]
    top_k_pairs = [(pairs[i][0], pairs[i][1], float(scores[i])) for i in top_k_indices]
    
    return top_k_pairs

# 한국어 reranker
model_path_ko = "Dongjin-kr/ko-reranker"
tokenizer_ko = AutoTokenizer.from_pretrained(model_path_ko)
model_ko = AutoModelForSequenceClassification.from_pretrained(model_path_ko)
model_ko.eval()

# 다국어 reranker
model_path_bge = "BAAI/bge-reranker-v2-m3"
tokenizer_bge = AutoTokenizer.from_pretrained(model_path_bge)
model_bge = AutoModelForSequenceClassification.from_pretrained(model_path_bge)
model_bge.eval()

# 질문 & 답변 예시 (실제 DB 에서 가져올 예정)
pairs = [
    ['아세트아미노펜 복용 전 주의사항이 있나요?', '아세트아미노펜은 과다 복용 시 간 손상을 초래할 수 있습니다.'],
    ['아세트아미노펜을 공복에 먹어도 괜찮나요?', '공복에 복용할 수 있지만, 속이 불편하다면 음식과 함께 복용하는 것이 좋습니다.'],
    ['아세트아미노펜을 알코올과 함께 복용해도 되나요?', '알코올과 함께 복용할 경우 간 손상의 위험이 증가할 수 있습니다.'],
    ['아세트아미노펜 복용 시 주의할 점은?', '과다 복용은 간에 손상을 줄 수 있으니 주의가 필요합니다.'],
    ['아세트아미노펜을 하루에 몇 번 먹을 수 있나요?', '성인은 보통 4-6시간 간격으로 복용할 수 있지만, 최대 용량을 초과하지 않도록 주의하세요.'],
    ['아세트아미노펜을 복용 후 어지러움을 느끼면 어떻게 해야 하나요?', '증상이 지속된다면 복용을 중단하고 의사와 상담하세요.'],
    ['이 약을 복용 중인 다른 약이 있으면 괜찮나요?', '복용 중인 다른 약과 상호작용이 있을 수 있으니 의사와 상의하세요.'],
    ['아세트아미노펜 복용 후 금해야 할 음식이 있나요?', '특정한 음식과의 상호작용은 없지만, 알코올 섭취는 피하는 것이 좋습니다.'],
    ['임신 중에 아세트아미노펜을 복용해도 괜찮나요?', '임신 중 복용에 대해 반드시 의사와 상의하는 것이 좋습니다.'],
    ['아세트아미노펜 복용 후 졸음이 올 수 있나요?', '졸음은 일반적인 부작용은 아니지만, 피로감을 느낄 수 있습니다.'],
    ['아세트아미노펜을 몇 시간 간격으로 복용해야 하나요?', '보통 4-6시간 간격으로 복용할 수 있습니다.'],
    ['아세트아미노펜을 복용하면 안 되는 사람은 누구인가요?', '간 질환이 있거나 알레르기가 있는 사람은 복용을 피해야 합니다.'],
    ['아세트아미노펜과 다른 진통제를 함께 복용해도 되나요?', '다른 진통제와 함께 복용 시 중복 복용에 주의해야 합니다.'],
    ['아세트아미노펜을 먹고도 통증이 가시지 않으면 어떻게 해야 하나요?', '효과가 없을 경우 의사와 상담하는 것이 좋습니다.'],
    ['아세트아미노펜을 장기간 복용해도 안전한가요?', '장기간 복용은 간에 무리를 줄 수 있으므로 주의해야 합니다.'],
    ['아세트아미노펜을 먹을 때 복용량을 초과하면 안 되나요?', '복용량을 초과하면 간 손상의 위험이 높아지므로 주의해야 합니다.'],
    ['아세트아미노펜을 소아에게도 복용시킬 수 있나요?', '소아의 경우 적절한 용량을 준수해야 하며, 의사의 지침을 따르는 것이 좋습니다.'],
    ['아세트아미노펜 복용 후 얼마나 빨리 효과가 나타나나요?', '보통 복용 후 30분에서 1시간 내에 효과가 나타납니다.'],
    ['아세트아미노펜이 다른 약에 비해 부작용이 적은가요?', '부작용이 적은 편이지만, 개인의 상태에 따라 다를 수 있습니다.'],
    ['아세트아미노펜 복용 중 운동을 해도 괜찮나요?', '가벼운 운동은 괜찮지만, 심한 운동은 피하는 것이 좋습니다.']
]

# BM25 초기화
bm25 = BM25Okapi([pair[0] for pair in pairs])

@app.post("/rerank")
def retrieve_and_rerank(query_request: QueryRequest):
    question = query_request.question
    top_k = query_request.top_k
    
    bm25_scores = bm25.get_scores(question)
    top_k_indices = np.argsort(bm25_scores)[-top_k*2:][::-1]
    bm25_top_pairs = [pairs[i] for i in top_k_indices]
    similar_pairs_ko = get_top_k_similar_pairs(question, bm25_top_pairs, model_ko, tokenizer_ko, k=top_k)
    
    similar_pairs_bge = get_top_k_similar_pairs(question, bm25_top_pairs, model_bge, tokenizer_bge, k=top_k)
    
    return {
        "ko_results": similar_pairs_ko,
        "bge_results": similar_pairs_bge
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)