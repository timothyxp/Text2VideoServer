from server.app import app, socketio


def main():
    socketio.run(app, debug=True, host='0.0.0.0', port=80)


if __name__ == '__main__':
    main()
