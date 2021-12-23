from flask import Flask, render_template
import os, random
from flask_socketio import SocketIO, emit
import logging, base64
import eventlet, eventlet.wsgi

eventlet.monkey_patch()

logging.basicConfig(datefmt = '%Y-%m-%d %H:%M:%S', filename = 'app.log', format = '[%(asctime)s][%(levelname)s] %(message)s', level = logging.DEBUG)

app = Flask(__name__)
socketio = SocketIO( app )
app.config['SECRET_KEY'] = 'sopra la panca la capra campa'

code = ""

@app.route("/", methods=["GET", "POST"])
def upload():
    return render_template( 'upload.html' )

def generateCodeAndFolder( filename ):
    global code
    code = str(random.randint(000000, 999999))
    while os.path.exists(os.path.join(os.getcwd(), f'uploads/{code}')):
        code = str(random.randint(000000, 999999))
    os.makedirs(str(os.path.join(os.getcwd(), f'uploads/{code}')))
    logging.debug(f'path generate: {os.path.join(os.getcwd(), f"uploads/{code}/{filename}")}')
    return os.path.join(os.getcwd(), f'uploads/{code}/{filename}')

@socketio.on( 'take' )
def taked( json ):
    logging.debug(f'response taked: {str(json)}')
    if json['first']:
        with open(generateCodeAndFolder(((str(json['hash']).replace("/", "$")) + "." + json['ext'])), 'wb') as f:
            f.write(base64.b64decode(json['value']))
    if json['last']:
        global code
        pathfile = "".join(f'{os.getcwd()}/uploads/{code}/{x}' for x in os.listdir(f'{os.getcwd()}/uploads/{code}'))
        with open(str(pathfile), 'wb') as f:
            f.write(base64.b64decode(json['value']))
        emit('code', (pathfile.split("/"))[7])
    else:
        pathfile = "".join(f'{os.getcwd()}/uploads/{code}/{x}' for x in os.listdir(f'{os.getcwd()}/uploads/{code}'))
        with open(str(pathfile), 'wb') as f:
            f.write(base64.b64decode(json['value']))

@app.route("/download", methods=["GET", "POST"])
def download():
    return render_template( 'download.html' )

@socketio.on( 'request' )
def check( json ):
    logging.debug(f'response check: {str(json)}')
    pathfile = "".join(f'{os.getcwd()}/uploads/{json["code"]}/{x}' for x in os.listdir(f'{os.getcwd()}/uploads/{json["code"]}'))
    percorso = f"{os.getcwd()}/uploads/{json['code']}/{(str(json['hash']).replace('/', '$'))}.{pathfile.split('.')[-1]}"
    if os.path.exists(pathfile) and pathfile == percorso:
        logging.debug(f"size: {os.path.getsize(percorso)} ext: {pathfile.split('.')[-1]}")
        emit('info', {'size': os.path.getsize(percorso), 'ext': pathfile.split('.')[-1]})
        with open(percorso, "rb") as f:
            while (byte := f.read(1000)):
                emit('download', str(base64.b64encode(byte).decode('ascii')))
    logging.debug("finito")

if __name__ == '__main__':
    socketio.run( app, debug = True )
