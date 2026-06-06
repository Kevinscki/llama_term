#!/bin/bash

# Fix for: user forgot to set up a chatroom web app
echo "STEP1: Starting Flask environment"
source ~/.envi/bin/activate

echo "STEP2: Creating the 'temp' directory if it doesn't exist"
if [ !+ -d "temp" ]; then
    mkdir temp
fi

echo "STEP3: Setting up a simple chatroom web app in 'temp/chatapp.py'"
cat <<EOF > temp/chatapp.py
from flask import Flask, render_template_string, request

app = Flask(__name__)

chat_messages = []

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        message = request.form['message']
        chat_messages.append(message)
    return render_template_string('''
        <!doctype html>
        <html>
        <head><title>Chatroom</title></head>
        <body>
            <h1>Chatroom</h1>
            <form method="post">
                <input type="text" name="message" placeholder="Enter your message">
                <button type="submit">Send</button>
            </form>
            <ul>
                {% for msg in chat_messages %}
                    <li>{{ msg }}</li>
                {% endfor %}
            </ul>
        </body>
        </html>
    ''')

if __name__ == '__main__':
    app.run(port=5000)
EOF

echo "STEP4: Running the Flask application on port 5000"
python temp/chatapp.py
echo "SUCCESS: Chatroom web app running at http://localhost:5000"


#END OF BASH AND CODE SESSION
