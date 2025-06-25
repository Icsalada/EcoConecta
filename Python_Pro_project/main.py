from flask import Flask, render_template, request, redirect, url_for, session, g
import sqlite3
import os
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.secret_key = "eco_secreto_2025"
DATABASE = "users.db"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///productos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(300), nullable=False)
    imagen_url = db.Column(db.String(300), nullable=True)

# --- Conexión a la base de datos ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
def reset_acciones():
    db = sqlite3.connect('users.db')
    c = db.cursor()
    c.execute("DELETE FROM acciones")
    db.commit()
    db.close()
# --- Inicializar base de datos ---
def init_db():
    if not os.path.exists(DATABASE):
        with app.app_context():
            db = get_db()
            c = db.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )
            ''')
            c.execute('''
                CREATE TABLE IF NOT EXISTS iniciativas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo TEXT NOT NULL,
                    descripcion TEXT NOT NULL,
                    lat REAL NOT NULL,
                    lng REAL NOT NULL,
                    usuario_id INTEGER,
                    FOREIGN KEY(usuario_id) REFERENCES users(id)
                )
            ''')
            c.execute('''
                CREATE TABLE IF NOT EXISTS acciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    contenido TEXT,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')
            db.commit()

# --- Página principal ---
@app.route('/')
def home():
    return render_template('index.html')

# --- Rutas principales ---
@app.route('/noticias')
def noticias():
    return render_template('noticias.html')

@app.route('/actua')
def actua():
    return render_template('actua.html')

@app.route('/comunidad')
def comunidad():
    if 'user_id' in session:
        return render_template('comunidad.html')
    return redirect(url_for('login'))

# --- Registro ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        c = db.cursor()
        try:
            c.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, password))
            db.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Este correo ya está registrado"
    return render_template('register.html')

# --- Login ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        c = db.cursor()
        c.execute('SELECT id FROM users WHERE email = ? AND password = ?', (email, password))
        user = c.fetchone()
        if user:
            session['user_id'] = user['id']
            return redirect(url_for('home'))
        else:
            return "Credenciales incorrectas"
    return render_template('login.html')

# --- Logout ---
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))


# --- Muro de acciones verdes ---
@app.route('/acciones', methods=['GET', 'POST'])
def acciones():
    db = get_db()
    c = db.cursor()

    if request.method == 'POST':
        if 'user_id' in session:
            contenido = request.form['contenido']
            user_id = session['user_id']
            c.execute("INSERT INTO acciones (user_id, contenido) VALUES (?, ?)", (user_id, contenido))
            db.commit()
        return redirect(url_for('acciones'))

    c.execute('''
        SELECT acciones.contenido, acciones.fecha, users.email
        FROM acciones
        JOIN users ON acciones.user_id = users.id
        ORDER BY acciones.fecha DESC
    ''')
    acciones = c.fetchall()
    return render_template('acciones.html', acciones=acciones)

# --- intercambio ---
@app.route('/intercambio')
def intercambio():
    productos = Producto.query.all()
    return render_template('intercambio.html', productos=productos)

@app.route('/intercambio/<int:id>')
def intercambio_detalle(id):
    producto = Producto.query.get_or_404(id)
    return render_template('intercambio_detalle.html', producto=producto)

@app.route('/intercambio/agregar', methods=['GET', 'POST'])
def intercambio_agregar():
    if request.method == 'POST':
        nuevo = Producto(
            titulo=request.form['titulo'],
            descripcion=request.form['descripcion'],
            imagen_url=request.form['imagen_url'],
        )
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for('intercambio'))
    return render_template('intercambio_agregar.html')

# --- Ejecutar ---
if __name__ == '__main__':
    init_db()   
           # Esto crea las tablas si no existen
    reset_acciones()   # Esto vacía la tabla 'acciones'
    app.run(debug=True)