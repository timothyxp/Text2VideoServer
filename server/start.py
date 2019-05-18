from server.app import app


def main():
    app.run(debug=True, host='0.0.0.0', ssl_context="adhoc")

if __name__ == '__main__':
    main()
