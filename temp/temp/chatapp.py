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
