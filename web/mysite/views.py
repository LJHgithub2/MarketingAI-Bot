from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
import NLP

def index(request):
    username = "Guest"  # 예시로 사용할 유저명
    return render(request, 'index.html', {'username': username})


@csrf_exempt
def get_info(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            query = data.get('query', '')

            # 여기에 실제 데이터베이스 조회 로직을 추가합니다.
            # 지금은 간단한 예제 데이터를 반환합니다.
            response_data = {
                "section1": [
                    {
                        "Index": 8,
                        "생성시간": f"{query}2024.06.10 06:30:42",
                        "게시글내용": f"{query}생성된 유자C의 브라이트닝 케어🤩...",
                        "해쉬태그": [f"{query}#어글리러블리", "#uglylovely"],
                        "img_path": "./images/7.jpg"
                    },
                    {
                        "Index": 64,
                        "생성시간": "2023.11.29 08:04:25",
                        "게시글내용": "어제보다 밝은 오늘을 꿈꾸며✨...",
                        "해쉬태그": ["#어글리러블리유자마스크", "#어글리러블리", "#uglylovely"],
                        "img_path": "./images/63.jpg"
                    },
                    # 추가 데이터...
                ],
                "section2": "생성된 유자 마스크팩으로 각질 케어와 매끈한 피부결을 경험할 수 있습니다. 고흥산 못난이 유자로 만든 어글리 러블리 유자 마스크는 피부 컨디션 회복에 도움을 줍니다. 외출 전에는 우산을 챙기고, 집에서는 어글리 러블리 마스크 팩을 사용하여 스페셜 케어를 즐기세요."
            }

            return JsonResponse(response_data)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    return JsonResponse({"error": "Invalid method"}, status=405)