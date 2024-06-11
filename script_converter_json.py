import json
import cv2
import os
import base64
import numpy as np
from sklearn.model_selection import train_test_split
import shutil
import yaml
import zipfile

input_dir="/home/mikhail/YPPRPO/converter/my_project_2/uploads/"
filenames=os.listdir(input_dir)


train_dir='data/train/'
test_dir='data/test/'
val_dir='data/val/'

yaml_file_path='data/data.yaml'


img_resize=(640,640)

os.makedirs(train_dir,exist_ok=True)
os.makedirs(test_dir,exist_ok=True)
os.makedirs(val_dir,exist_ok=True)



# classes = {'laptop':0,'phone':1}# подумать как менять названия классов
classes = {}

# Открытие JSON-файла и загрузка данных
for filename in filenames:
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




for folder in [train_dir,test_dir,val_dir]:
  os.makedirs(os.path.join(folder, 'labels'), exist_ok=True)
  os.makedirs(os.path.join(folder, 'images'), exist_ok=True)
# filenames=os.listdir(input_dir)# Возвращает список файлов и директорий в указанной директории.
def process_files(filenames,current_dir):
    for filename in filenames:
        if filename.endswith('.json'):
          name_json=os.path.join(input_dir,filename)#Полный путь к исходному JSON-файлу.
          name_img = os.path.join(current_dir, filename.replace('.json', '.png'))
          name_txt = os.path.join(current_dir, filename.replace('.json', '.txt'))
          ann_file=open(name_txt,'w')#запись в файл

          with open(name_json) as f:
              data=json.load(f)#функция считывает данные из файла и декодирует  их в Python-объекты
          image_bin=base64.b64decode(data['imageData'])#декодирует данные изображения в бинарник
          image_np=cv2.imdecode(np.frombuffer(image_bin,np.uint8),cv2.IMREAD_COLOR)
          height = image_np.shape[0]
          width =image_np.shape[1]
          image_np=cv2.resize(image_np,img_resize)
          cv2.imwrite(name_img,image_np)# для сохранения изображения в файл
          print(data['shapes'])
          for obj in data['shapes']:
            global_cord=np.array(obj['points'])#получение координат
            ralative_cord=(global_cord/[width, height]).flatten()#результат сжимается в одномерный массив методом flatten()
            label=obj['label']
            print(label)
            ann_file.write(str(classes[label]) + ' ')
            ann_file.write(' '.join(map(str, ralative_cord)) + '\n')
          ann_file.close()
          shutil.move(name_txt, os.path.join(current_dir, 'labels', os.path.basename(name_txt)))
          shutil.move(name_img, os.path.join(current_dir, 'images', os.path.basename(name_img)))

# Перемещение файлов в папки train, test и val
train_files,test_val_files=train_test_split(filenames,test_size=0.4,random_state=42)
test_files,val_files=train_test_split(test_val_files,test_size=0.5, random_state=42)

process_files(train_files, train_dir)
process_files(test_files, test_dir)
process_files(val_files, val_dir)

with open(yaml_file_path, 'w') as yaml_file:
    yaml_file.write('train: ' + os.path.join('train', 'images').replace('\\', '/') + '\n')
    yaml_file.write('val: ' + os.path.join('val', 'images').replace('\\', '/') + '\n')
    yaml_file.write('test: ' + os.path.join('test', 'images').replace('\\', '/') + '\n\n')
    yaml_file.write('nc: ' + str(len(classes)) + '\n\n')
    yaml_file.write('names:\n')
    for class_name, index in classes.items():
        yaml_file.write(f'  {index}: {class_name}\n')

zip_file_path ='/home/mikhail/YPPRPO/converter/my_project_2/results/data.zip'
with zipfile.ZipFile(zip_file_path,'w') as zipf:
    for root,dirs,files in os.walk('data'):
        for file in files:
            file_path=os.path.join(root,file)
            zipf.write(file_path, os.path.relpath(file_path, 'data'))

shutil.rmtree('data')# Удаление исходных директорий после создания архива