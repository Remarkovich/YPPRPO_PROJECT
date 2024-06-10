import os
import requests
import subprocess
import time
import signal
import zipfile
import json
import yaml
import shutil

script_dir = os.path.dirname(os.path.abspath(__file__))

def create_file_dict(root_dir, extension='.txt'):
    file_dict = {}
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(extension):
                # Получаем только имя файла без расширения
                file_name = os.path.splitext(file)[0]
                # Получаем части имени файла, разделенные по "_"
                parts = file_name.split('_')
                # Имя файла без префикса и расширения
                name = '_'.join(parts[1:]) if len(parts) > 1 else parts[0]
                # Добавляем в словарь
                file_dict[name] = os.path.join(root, file)
                
    return file_dict

def read_annotations_from_json(json_dir):
    annotation_files = sorted(os.listdir(json_dir))
    annotations = []

    for ann_file in annotation_files:
        ann_path = os.path.join(json_dir, ann_file)
        file_name = os.path.splitext(ann_file)[0]
        
        with open(ann_path, 'r') as f:
            data = json.load(f)
            cord = []
            for annotation in data.get("shapes", []):
                class_label = annotation.get("label")
                height = data.get("imageHeight")
                width = data.get("imageWidth")
                polygon_coords = annotation.get("points", [])
                for cords in polygon_coords:
                    cords[0] = cords[0]/width
                    cords[1] = cords[1]/height
                    cord.append(cords[0])
                    cord.append(cords[1])
                if class_label and polygon_coords:
                    annotation_entry = [file_name, class_label] + [cord] + [width, height]
                    annotations.append(annotation_entry)

    return annotations

def read_and_scale_coordinates(mask_path, class_dict):
    coords = []
    with open(mask_path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) > 2:
                class_index = int(parts[0])
                class_name = class_dict.get(class_index, "Unknown")
                # Считываем координаты и масштабируем их по ширине и высоте
                scaled_coords = [float(parts[i]) for i in range(1, len(parts))]
                coords.append([class_name] + [scaled_coords])
    return coords


def compare(test_coords, coords, test_name_of_class, name_of_class):
    for i in range (len(coords)):
        if test_coords[i] != coords[i] and test_name_of_class != name_of_class:
            return False
    return True

def clear_folder(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

class Server:
    def __init__(self):
        self.stdout_file = open('server_stdout.log', 'w')
        self.stderr_file = open('server_stderr.log', 'w')
        self.process = subprocess.Popen(
            ["python3", "server.py"],
            stdout=self.stdout_file,
            stderr=self.stderr_file
        )
        time.sleep(3)  # Даем серверу время для запуска

    def __del__(self):
        if self.process:
            os.kill(self.process.pid, signal.SIGINT)
            self.process.wait()
            self.stdout_file.close()
            self.stderr_file.close()

# Функция для загрузки архива на сервер
def upload_zip(server_url, zip_file_path):
    with open(zip_file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(server_url + '/upload', files=files)
        print(f"Upload response status: {response.status_code}")
        print(f"Upload response text: {response.text}")
    return response

def process_zip(server_url):
    response = requests.post(server_url + '/process')
    print(f"Process response status: {response.status_code}")
    print(f"Process response text: {response.text}")
    time.sleep(3)  # Увеличиваем время ожидания для завершения обработки
    return response

def download_processed_zip(server_url, output_path):
    response = requests.get(server_url + '/download/data.zip')
    print(f"Download response status: {response.status_code}")
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print("Processed archive downloaded successfully.")
    else:
        print(f"Download response text: {response.text}")
    return response

def check_server_status(server_url):
    try:
        response = requests.get(server_url)
        if response.status_code == 200:
            print("Server is up and running.")
            return True
        else:
            print(f"Failed to reach server: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error checking server status: {e}")
        return False

server = Server()
server_url = 'http://localhost:3001'
test_zip_path = os.path.join(script_dir, 'test', 'test_json.zip')
output_zip_path = os.path.join(script_dir, 'results', 'test_data.zip') 

# Проверяем статус сервера
if check_server_status(server_url):
    # Загружаем на сервер архив с тестовыми данными
    try:
        response = upload_zip(server_url, test_zip_path)
        if response.status_code == 200:
            print("Test archive uploaded successfully.")
        else:
            print("Failed to upload test archive.")
    except Exception as e:
        print("Error occurred while uploading test archive:", e)

    # Запускаем обработку файлов на сервере
    try:
        response = process_zip(server_url)
        if response.status_code == 200:
            print("Files processed successfully.")
            try:
                download_processed_zip(server_url, output_zip_path)
            except Exception as e:
                print("Error occurred while downloading processed archive:", e)
        else:
            print("Failed to process files.")
    except Exception as e:
        print("Error processing files:", e)
else:
    print("Server is not reachable. Check server logs for details.")

del server


json_dir = os.path.join(script_dir, 'test', 'test_json.zip')
test_fir = os.path.join(script_dir, 'results', 'test_data.zip')

# Путь к папке, в которую нужно разархивировать архив
extract_folder = os.path.join(script_dir, 'test', 'extract_folder')
test_folder = os.path.join(script_dir, 'test', 'test_folder')
# Создаем папку, если её нет
os.makedirs(extract_folder, exist_ok=True)
os.makedirs(test_folder, exist_ok=True)

# Разархивируем архив
with zipfile.ZipFile(json_dir, 'r') as zip_ref:
    zip_ref.extractall(extract_folder)

with zipfile.ZipFile(test_fir, 'r') as zip_ref:
    zip_ref.extractall(test_folder)

annotations = read_annotations_from_json(extract_folder)
path_yaml = os.path.join(script_dir, 'test','test_folder', 'data.yaml')

with open(path_yaml, 'r') as yaml_file:
    yaml_content = yaml.safe_load(yaml_file)

# Создание словаря, где ключ - индекс класса, а значение - название класса
classes = {index: name for index, name in yaml_content['names'].items()}
file_dict = create_file_dict(test_folder)
# Сравнение полученных данных с посчитанными
for ann in annotations:
    name = ann[0]
    coords = read_and_scale_coordinates(file_dict[name], classes)
    flag = compare(ann[2], coords[0][1], ann[1], coords[0][0])
    if flag == False:
        raise("Test is failed")


clear_path_extract = os.path.join(script_dir, 'test', 'extract_folder')
clear_path_test = os.path.join(script_dir, 'test', 'test_folder')
clear_path_data = os.path.join(script_dir, 'data')
clear_folder(clear_path_extract)
clear_folder(clear_path_test)
clear_folder(clear_path_data)
