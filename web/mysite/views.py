from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
from .NLP import generate_promotion

def index(request):
    username = "Guest"  # 예시로 사용할 유저명
    return render(request, 'index.html', {'username': username})


@csrf_exempt
def get_info(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            query = data.get('query', '')

            response_data = generate_promotion(query)


            return JsonResponse(response_data)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    return JsonResponse({"error": "Invalid method"}, status=405)