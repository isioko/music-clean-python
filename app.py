from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/")
def start():
	return "hello world"

@app.route('/<name>')
def hello_name(name):
    return "Hello {}!".format(name)

if __name__ == '__main__':
	app.run()