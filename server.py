from flask import Flask, request, send_file, render_template, send_from_directory, after_this_request
from werkzeug.utils import secure_filename
import os
import zipfile
import shutil
import logging

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

uploaded_files = []

@app.route("/")
def hello():
    return render_template('index.html')

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return "No file part", 400
    
    files = request.files.getlist("file")
    if len(files) == 0:
        return "No files selected", 400
    
    for file in files:
        if file.filename == "":
            return "A file has no name", 400
        
        # Берём только имя файла, для сохранения
        filename = secure_filename(file.filename)
        # Сохранить файл
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        uploaded_files.append(file_path)    
    return "Files uploaded successfully", 200

@app.route("/process", methods=["POST"])
def process():
    if not uploaded_files:
        return "No files to process", 400

    try:
        # Удаляем папку с предыдущими результатами, если она существует
        if os.path.exists('data'):
            shutil.rmtree('data')

        # Распаковываем и удаляем загруженные ZIP файлы
        for file_path in uploaded_files:
            file_name, file_extension = os.path.splitext(file_path)
            if file_extension.lower() == '.zip':
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(UPLOAD_FOLDER)
                os.remove(file_path)

        # Очистка списка загруженных файлов, чтобы не обрабатывать их повторно
        uploaded_files.clear()
        
        # Обработка всех извлечённых файлов
        os.system("python3 script_converter_json.py")

        # Создание архива с обработанными файлами
        output_zip_path = os.path.join(app.config['RESULTS_FOLDER'], 'data.zip')
        with zipfile.ZipFile(output_zip_path, 'w') as zipf:
            for root, dirs, files in os.walk('data'):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, os.path.relpath(file_path, 'data'))

        # Очистка загруженных файлов
        shutil.rmtree(UPLOAD_FOLDER)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        return "Files processed successfully", 200

    except Exception as e:
        logging.error(f"Error processing files: {str(e)}")
        return f"Error processing files: {str(e)}", 500

@app.route("/download/<filename>")
def uploaded_file(filename):
    filepath = os.path.join(app.config['RESULTS_FOLDER'], filename)
    
    @after_this_request
    def remove_file(response):
        try:
            os.remove(filepath)
        except Exception as error:
            app.logger.error("Error removing file: %s", error)
        return response
    
    return send_from_directory(app.config['RESULTS_FOLDER'], filename)
    
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3001)
