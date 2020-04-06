from flask import Flask
from flask import request
from flask_cors import CORS
import location_history as lh

app = Flask(__name__)
CORS(app)

@app.route('/')
def hello():
    return "Hello world!"

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        lh.analyse_location_history(f)
        # content = f.read()
        # print(content)
        return '',200
    
if __name__ == "__main__":
    app.run()
