from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


@app.route("/test", methods=["GET"])
def test():
    return jsonify({"response": "Service 2 Works!"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    app.debug = True
