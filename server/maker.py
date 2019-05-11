from server.app import app


@app.route('/make')
def make():
    return 'make'
