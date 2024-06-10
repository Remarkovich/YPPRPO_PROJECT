import cv2
import numpy as np
import tensorflow as tf
import os
import zipfile

# Определение структуры признаков в TFRecord файле
feature_description = {
    'image': tf.io.FixedLenFeature([], tf.string, default_value=''),
    'image_name': tf.io.FixedLenFeature([], tf.string, default_value=''),
    'target': tf.io.FixedLenFeature([], tf.int64, default_value=0),
}


# Функция для разбора данных из TFRecord файла
def _parse_image_function(example_proto):
    return tf.io.parse_single_example(example_proto, feature_description)


# Функция для декодирования изображения
def preprocess_image(image):
    image = tf.io.decode_image(image, channels=3)
    return image


BASE_DIR = "/home/mikhail/YPPRPO/converter/"
tfrec_dir = "./uploads"
output_zip = "./results/data.zip"


# Функция для проверки корректности TFRecord файла
def is_valid_tfrecord(file_path):
    try:
        for record in tf.data.TFRecordDataset(file_path):
            pass
        return True
    except tf.errors.DataLossError:
        return False


def resize_image(image, target_size=(608, 608)):
    return cv2.resize(image, target_size)


# Функция для распаковки TFRecord файла и создания zip-архива для изображений в формате JPEG
def unpack_and_create_zip_resized(tfrecord_path, output_zip, target_size=(608, 608)):
    with zipfile.ZipFile(output_zip, 'a') as zipf:
        if is_valid_tfrecord(tfrecord_path):
            train_image_dataset = tf.data.TFRecordDataset(tfrecord_path)
            train_images = train_image_dataset.map(_parse_image_function)

            # Обработка данных из TFRecord файла
            counter = 0
            folder_created = False  # Переменная для отслеживания создания подпапки
            for image_features in train_images:
                try:
                    image_raw = preprocess_image(image_features['image'])
                    image_resized = resize_image(image_raw.numpy(), target_size=target_size)  # Изменение размера изображения
                    image_name = f"image_{counter}.jpg"  # Имя файла с индексом
                    counter += 1

                    # Преобразование изображения в формат JPEG
                    image_jpeg = cv2.imencode('.jpg', image_resized)[1].tostring()

                    # Добавление изображения в подпапку в архиве
                    if not folder_created:
                        # Создание подпапки в архиве только при первом обнаружении изображения
                        file_name = os.path.splitext(os.path.basename(tfrecord_path))[0]
                        zip_subfolder_path = file_name  # Имя подпапки совпадает с именем TFRecord файла
                        folder_created = True

                    zipf.writestr(os.path.join(zip_subfolder_path, image_name), image_jpeg)
                except Exception as e:
                    print(f"Ошибка при обработке изображения {image_name}: {e}")
        else:
            print(f"Файл {tfrecord_path} поврежден и будет пропущен.")


# Цикл обработки TFRecord файлов
for tfName in os.listdir(os.path.join(BASE_DIR, tfrec_dir)):
    tfrecord_path = os.path.join(BASE_DIR, tfrec_dir, tfName)
    unpack_and_create_zip_resized(tfrecord_path, output_zip, target_size=(608, 608))


print("Создан zip-архив для распакованных изображений в формате JPEG с измененным размером:", output_zip)