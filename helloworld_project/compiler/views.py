from http.client import HTTPException
import importlib
from django.http import FileResponse, HttpResponse
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

import json
import uuid

from dotenv import load_dotenv
from compiler.data_problems import problems_list
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sol_module = importlib.import_module("compiler.solution")
#load_dotenv(os.path.join(BASE_DIR, '.env'))
load_dotenv()


def get_html_file_path(id : int) -> str:
    s = "problem_description_"+str(id)+".html"
    HTML_FILE_PATH = os.path.join(BASE_DIR, "templates", s)
    return HTML_FILE_PATH

def generate_file(language, code, input):
    file_extension = {'cpp': 'cpp', 'java': 'java', 'py': 'py', 'c': 'c'}
    temp_dir = os.getenv('OUTPUT_TEMP_DIR')
    os.makedirs(temp_dir, exist_ok=True)
    filename = os.path.join(temp_dir,f"{str(uuid.uuid4())}.{file_extension[language]}")
    input_filename = os.path.join(temp_dir,f"{str(uuid.uuid4())}.txt")
    with open(filename, 'w') as file:
        file.write(code)
    with open(input_filename, 'w') as file:
        file.write(input)
    return filename, input_filename

def cleanup_files(file_path, input_path):
    files_to_delete = [file_path, input_path]
    
    for file in files_to_delete:
        try:
            os.remove(file)
            print(f"Successfully deleted {file}")
        except OSError as e:
            print(f"Error deleting {file}: {e.strerror}")

def execute_cpp(file_path, input_path):
    file_name = os.path.basename(file_path)
    file_name_without_ext = os.path.splitext(file_name)[0]
    temp_dir = os.getenv('OUTPUT_TEMP_DIR')

    if os.name == 'nt':  # Windows
        compiled_path = os.path.join(temp_dir, f"{file_name_without_ext}.exe")
        compile_command = f"g++ \"{file_path}\" -o \"{compiled_path}\""
        run_command = f"\"{compiled_path}\" < \"{input_path}\""
    else:  # macOS/Linux
        compiled_path = os.path.join(temp_dir, f"{file_name_without_ext}.out")
        compile_command = f"g++ \"{file_path}\" -o \"{compiled_path}\""
        run_command = f"chmod +x \"{compiled_path}\" && \"{compiled_path}\" < \"{input_path}\""

    os.system(compile_command)
    output = os.popen(run_command).read()
    #os.remove(compiled_path)
    cleanup_files(file_path, input_path)
    # Also remove the compiled file if it exists
    if os.path.exists(compiled_path):
        os.remove(compiled_path)
    return {'output': output}

def execute_python(file_path, input_path):
    if os.name == 'nt':
        python_command = "python"
    else:
        python_command = "python3"

    command = f'{python_command} "{file_path}" < "{input_path}"'

    try:
        # Execute the command and capture the output
        output = os.popen(command).read()
        return {'output': output}
    except Exception as e:
        return {'output': f"Execution error: {str(e)}"}
    finally:
        # Clean up the files
        cleanup_files(file_path, input_path)

def get_all_problems(request):
    response = JsonResponse({"problems": problems_list})
    return response

def get_problem_description(request,id):
    #return {"id":id}
    path = get_html_file_path(id)
    # Return the HTML file as a FileResponse
    return FileResponse(open(path, 'rb'), content_type='text/html')

@csrf_exempt
def check_solution(request,id):
        if request.method == 'POST':
            try:
            # Parse the JSON data from the request body
                data = json.loads(request.body)
                inp1 = data.get('inp')
                filtered_list = [d for d in problems_list if d.get('id') == id]
                solution_func_name = filtered_list[0].get('solution_func')
                solution_func = getattr(sol_module, solution_func_name, None)
                result = solution_func(inp1)
                # Return the result as JSON
                return JsonResponse({"input":inp1,"output": result})
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON'}, status=400)
            except KeyError as e:
                return JsonResponse({'error': f'Missing required field: {str(e)}'}, status=400)
        else:
            return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

@csrf_exempt
def run_code(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            if not data.get('code'):
                raise HTTPException(status_code=400, detail="Empty code!")
            file_path, input_path = generate_file(data.get('language'), data.get('code'), data.get('input'))
            result = None

            if data.get('language') == 'cpp':
                result = execute_cpp(file_path, input_path)
            elif data.get('language') == 'py':
                result = execute_python(file_path, input_path)
            elif data.get('language') not in ['cpp', 'py']:
                raise HTTPException(status_code=400, detail="Unsupported language")
            return JsonResponse({"output":result['output']})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except KeyError as e:
            return JsonResponse({'error': f'Missing required field: {str(e)}'}, status=400)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

@csrf_exempt
def submit_solution(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            if not data.get('code'):
                raise HTTPException(status_code=400, detail="Empty code!")
            problem = next((p for p in problems_list if p['id'] == data.get('id')), None)
            if not problem:
                raise HTTPException(status_code=404, detail="Problem not found")

            test_cases = problem.get('test_cases', [])
            if not test_cases:
                raise HTTPException(status_code=400, detail="No test cases found for this problem")

            results = []
            passed_count = 0
            total_count = len(test_cases)

            for test_case in test_cases:
                file_path, input_path = generate_file(data.get('language'), data.get('code'), test_case['input'])
                
                if data.get('language') == 'cpp':
                    result = execute_cpp(file_path, input_path)
                elif data.get('language') == 'py':
                    result = execute_python(file_path, input_path)
                elif data.get('language') not in ['cpp', 'py']:
                    raise HTTPException(status_code=400, detail="Unsupported language")

                actual_output = result['output'].strip()
                expected_output = str(test_case['output']).strip()
                passed = actual_output == expected_output

                if passed:
                    passed_count += 1

                all_passed = passed_count == total_count
            
            return JsonResponse({
                    "success":True,
                    "status":"Success" if all_passed else "Failed",
                    "message":f"Passed {passed_count}/{total_count} test cases",
                    })
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except KeyError as e:
            return JsonResponse({'error': f'Missing required field: {str(e)}'}, status=400)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)



