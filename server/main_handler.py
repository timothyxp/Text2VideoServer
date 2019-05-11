from server.app import app


@app.route('/')
def main():
    return "Hello"
