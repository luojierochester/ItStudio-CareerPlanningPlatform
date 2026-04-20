import requests

res = requests.post('http://localhost:8001/api/recommend', json={
    'resume_text': '我熟悉Python和PyTorch，有推荐系统课程项目经历，曾参加蓝桥杯竞赛，有实习经历，持有英语六级证书',
    'topn': 5
})

data = res.json()
for item in data['data']:
    print(f"{item['title'][:20]:20s}  rank_score={item['rank_score']:.4f}  sim={item['sim']:.4f}")