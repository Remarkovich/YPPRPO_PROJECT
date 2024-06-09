from flask import Flask, request, send_file, render_template, send_from_directory, Response, render_template
from flask import send_from_directory, current_app as app, after_this_request
from werkzeug.utils import secure_filename
import os
import shutil
import logging

app = Flask(__name__)
UPLOAD_FOLDER_1 = 'uploads'
RESULTS_FOLDER = 'results'
app.config['UPLOAD_FOLDER_1'] = UPLOAD_FOLDER_1
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER

uploaded_files = []

@app.route("/")
def hello():
    return render_template('index.html')

@app.route("/upload", methods=["POST"])
def upload():

    if "file" not in request.files:
        return "No file part"
    
    files = request.files.getlist("file")
    if len(files) == 0:
        return "No files selected"
    
    for file in files:
        if file.filename == "":
            return "A file has no name"
        
        #Берём только имя файла, для сохранения
        filename = secure_filename(file.filename)
        # Сохранить файл
        file_path = os.path.join(app.config['UPLOAD_FOLDER_1'], filename)
        file.save(file_path)
        uploaded_files.append(file_path)    
    return ""

@app.route("/process", methods=["POST"])
def process():
    if not uploaded_files:
        return "No files to process" 
    
    
    file_path = uploaded_files[0]
    file_name,file_extension = os.path.splitext(file_path)
    if file_extension.lower() == '.json':
        os.system(f'python3 script_converter_json.py')
    elif file_extension.lower() == '.tfrec':
        os.system("python3 script_converter_tfrec.py")
    
    # Очистка списка uploaded_files для следующей партии загрузок
    shutil.rmtree(UPLOAD_FOLDER_1)
    os.mkdir('uploads')
    
    return "Files processed successfully"

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
