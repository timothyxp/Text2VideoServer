from server.app import app


@app.route('/search')
def make():
    return 'search'
