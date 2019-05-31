from server.app import app
import server.main_handler
import server.maker
import server.search


def main():
    app.run(debug=True, host='0.0.0.0', port=80)


if __name__ == '__main__':
    main()
