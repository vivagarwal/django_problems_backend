from django.http import HttpResponse
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

# Create your views here.
def hello_world(request):
    return HttpResponse("Hello, World!")

def hello_id(request, id):
    return HttpResponse(f"You requested ID: {id}")

@csrf_exempt
def calculate(request):
    if request.method == 'POST':
        try:
            # Parse the JSON data from the request body
            data = json.loads(request.body)
            num1 = data.get('num1')
            num2 = data.get('num2')
            operation = data.get('operation')

            # Perform the calculation based on the operation
            if operation == 'add':
                result = num1 + num2
            elif operation == 'subtract':
                result = num1 - num2
            elif operation == 'multiply':
                result = num1 * num2
            elif operation == 'divide':
                if num2 != 0:
                    result = num1 / num2
                else:
                    return JsonResponse({'error': 'Cannot divide by zero'}, status=400)
            else:
                return JsonResponse({'error': 'Invalid operation'}, status=400)

            # Return the result as JSON
            return JsonResponse({'result': result})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except KeyError as e:
            return JsonResponse({'error': f'Missing required field: {str(e)}'}, status=400)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
