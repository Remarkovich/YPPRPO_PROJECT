import json
import cv2
import os
import base64
import numpy as np
from sklearn.model_selection import train_test_split
import shutil
import yaml
import time

script_dir = os.path.dirname(os.path.abspath(__file__))

input_dir = os.path.join(script_dir, 'uploads')
data_dir = os.path.join(script_dir, 'data')
train_dir = os.path.join(data_dir, 'train')
test_dir = os.path.join(data_dir, 'test')
val_dir = os.path.join(data_dir, 'val')

# Убедитесь, что папка data создана
os.makedirs(data_dir, exist_ok=True)
os.makedirs(train_dir, exist_ok=True)
os.makedirs(test_dir, exist_ok=True)
os.makedirs(val_dir, exist_ok=True)

classes = {}

start_time = time.time()

# Открытие JSON-файла и загрузка данных
for filename in os.listdir(input_dir):
    if filename.endswith('.json'):
        name_json = os.path.join(input_dir, filename)
        with open(name_json) as f:
            data = json.load(f)
        # Получение классов из JSON и добавление их в словарь
        for obj in data['shapes']:
            label = obj['label']
            if label not in classes:
                classes[label] = len(classes)  # Присваиваем уникальный индекс для каждого класса

# Вывод обновленного словаря с классами
print(classes)

for folder in [train_dir, test_dir, val_dir]:
    os.makedirs(os.path.join(folder, 'labels'), exist_ok=True)
    os.makedirs(os.path.join(folder, 'images'), exist_ok=True)

def process_files(filenames, current_dir):
    img_resize = (640, 640)
    for filename in filenames:
        if filename.endswith('.json'):
            name_json = os.path.join(input_dir, filename)
            name_img = os.path.join(current_dir, filename.replace('.json', '.png'))
            name_txt = os.path.join(current_dir, filename.replace('.json', '.txt'))
            ann_file = open(name_txt, 'w')

            # Логирование перед загрузкой JSON
            print(f"Loading JSON file: {name_json}")
            file_start_time = time.time()
            with open(name_json) as f:
                data = json.load(f)
            file_end_time = time.time()
            print(f"Loaded JSON file: {name_json} in {file_end_time - file_start_time} seconds")

            image_bin = base64.b64decode(data['imageData'])
            image_np = cv2.imdecode(np.frombuffer(image_bin, np.uint8), cv2.IMREAD_COLOR)
            height = image_np.shape[0]
            width = image_np.shape[1]
            image_np = cv2.resize(image_np, img_resize)
            cv2.imwrite(name_img, image_np)
            print(f"Processing shapes for {filename}: {data['shapes']}")
            for obj in data['shapes']:
                global_cord = np.array(obj['points'])
                relative_cord = (global_cord / [width, height]).flatten()
                label = obj['label']
                print(f"Processing label: {label}")
                ann_file.write(str(classes[label]) + ' ')
                ann_file.write(' '.join(map(str, relative_cord)) + '\n')
            ann_file.close()
            shutil.move(name_txt, os.path.join(current_dir, 'labels', os.path.basename(name_txt)))
            shutil.move(name_img, os.path.join(current_dir, 'images', os.path.basename(name_img)))

# Получение списка файлов для обработки
filenames = [f for f in os.listdir(input_dir) if f.endswith('.json')]

train_files, test_val_files = train_test_split(filenames, test_size=0.4, random_state=42)
test_files, val_files = train_test_split(test_val_files, test_size=0.5, random_state=42)

process_files(train_files, train_dir)
process_files(test_files, test_dir)
process_files(val_files, val_dir)

yaml_file_path = os.path.join(data_dir, 'data.yaml')
with open(yaml_file_path, 'w') as yaml_file:
    yaml_file.write('train: ' + os.path.join('train', 'images').replace('\\', '/') + '\n')
    yaml_file.write('val: ' + os.path.join('val', 'images').replace('\\', '/') + '\n')
    yaml_file.write('test: ' + os.path.join('test', 'images').replace('\\', '/') + '\n\n')
    yaml_file.write('nc: ' + str(len(classes)) + '\n\n')
    yaml_file.write('names:\n')
    for class_name, index in classes.items():
        yaml_file.write(f'  {index}: {class_name}\n')

# Создание архива с обработанными файлами
zip_file_path = os.path.join(script_dir, 'results', 'data.zip')
with zipfile.ZipFile(zip_file_path, 'w') as zipf:
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            file_path = os.path.join(root, file)
            zipf.write(file_path, os.path.relpath(file_path, data_dir))



end_time = time.time()
print(f"Script execution time: {end_time - start_time} seconds")

