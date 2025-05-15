from flask import Flask, render_template_string, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import boto3
from decimal import Decimal

app = Flask(__name__)
app.secret_key = 'jm-aromas-secret-key'

# DynamoDB resources
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
tabla_usuarios = dynamodb.Table('usuarios_aromas')
tabla_perfumes = dynamodb.Table('perfumes')

# Estilos para tienda de perfumes
style = """
<style>
    body {
        background: linear-gradient(to right, #f7e7ce, #fff);
        color: #333;
        font-family: 'Georgia', serif;
        margin: 0;
        padding: 0;
    }
    header {
        background-color: #4b2e2e;
        color: white;
        padding: 20px;
        text-align: center;
        font-size: 28px;
        font-weight: bold;
        letter-spacing: 2px;
    }
    .top-bar {
        display: flex;
        justify-content: flex-end;
        gap: 10px;
        padding: 10px 20px;
    }
    .top-bar form {
        margin: 0;
    }
    .container {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 20px;
        margin: 30px auto;
        padding: 10px;
        width: 90%;
    }
    .card {
        background: white;
        border-radius: 15px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        width: 220px;
        text-align: center;
        overflow: hidden;
        transition: transform 0.3s ease;
    }
    .card:hover {
        transform: translateY(-10px);
    }
    .card img {
        width: 100%;
        height: 250px;
        object-fit: cover;
    }
    button {
        background-color: #4b2e2e;
        color: white;
        border: none;
        padding: 10px;
        margin-top: 10px;
        cursor: pointer;
        width: 90%;
        border-radius: 5px;
        font-weight: bold;
    }
    button:hover {
        background-color: #7b4e4e;
    }
    table {
        width: 90%;
        margin: auto;
        border-collapse: collapse;
    }
    th, td {
        border: 1px solid #ddd;
        padding: 10px;
    }
    th {
        background-color: #d9b99b;
    }
    .message {
        text-align: center;
        color: green;
        font-weight: bold;
    }
</style>
"""

# Página principal: Tienda de perfumes
main_page_html = style + """
<!DOCTYPE html>
<html>
<head><title>J & M Aromas</title></head>
<body>
    <header>J & M Aromas</header>
    <div class="top-bar">
        <form action="/admin_login" method="get">
            <button type="submit">Vista Admin</button>
        </form>
    </div>

    {% if mensaje_compra %}
    <div class="message">{{ mensaje_compra }}</div>
    {% endif %}

    <div class="container">
        {% for perfume in perfumes %}
        <div class="card">
            <h3>{{ perfume.nombre }}</h3>
            <img src="{{ perfume.imagen }}">
            <p>Precio: ${{ perfume.precio }}</p>
            <form method="post" action="/agregar_carrito">
                <input type="hidden" name="nombre" value="{{ perfume.nombre }}">
                <input type="hidden" name="precio" value="{{ perfume.precio }}">
                <button type="submit">Agregar al carrito</button>
            </form>
        </div>
        {% endfor %}
    </div>

    <h2 style="text-align: center;">Carrito de compras</h2>
    <table>
        <tr><th>Producto</th><th>Precio</th><th>Cantidad</th><th>Subtotal</th><th>Acciones</th></tr>
        {% for item in carrito %}
        <tr>
            <td>{{ item.nombre }}</td>
            <td>${{ item.precio }}</td>
            <td>{{ item.cantidad }}</td>
            <td>${{ item.precio * item.cantidad }}</td>
            <td>
                <form method="post" action="/eliminar_carrito" style="display:inline;">
                    <input type="hidden" name="nombre" value="{{ item.nombre }}">
                    <button type="submit">Eliminar</button>
                </form>
            </td>
        </tr>
        {% endfor %}
        <tr>
            <td colspan="3" style="text-align: right;"><strong>Total:</strong></td>
            <td colspan="2"><strong>${{ total }}</strong></td>
        </tr>
    </table>
    {% if carrito %}
    <form method="post" action="/comprar" style="text-align: center; margin: 20px;">
        <button type="submit">Comprar ahora</button>
    </form>
    {% endif %}
</body>
</html>
"""

# Login y registro para admin
admin_login_html = style + """
<!DOCTYPE html>
<html>
<head><title>Admin Login - J & M Aromas</title></head>
<body>
    <header>J & M Aromas - Admin</header>
    <div class="top-bar">
        <form action="/" method="get">
            <button type="submit">Volver a tienda</button>
        </form>
    </div>
    <div class="container" style="flex-direction: column; align-items: center;">
        <div class="card" style="width: 300px;">
            <h2>Iniciar Sesión</h2>
            <form method="post" action="/admin_login">
                <input type="text" name="username" placeholder="Usuario" required><br><br>
                <input type="password" name="password" placeholder="Contraseña" required><br><br>
                <button type="submit">Entrar</button>
            </form>
        </div>
        <div class="card" style="width: 300px;">
            <h2>Registrar</h2>
            <form method="post" action="/register">
                <input type="text" name="username" placeholder="Usuario" required><br><br>
                <input type="password" name="password" placeholder="Contraseña" required><br><br>
                <button type="submit">Registrar</button>
            </form>
        </div>
        {% if mensaje %}
        <div class="message">{{ mensaje }}</div>
        {% endif %}
    </div>
</body>
</html>
"""

# Vista admin para editar perfumes
admin_html = style + """
<!DOCTYPE html>
<html>
<head><title>Admin - J & M Aromas</title></head>
<body>
    <header>J & M Aromas - Administrador</header>
    <div class="top-bar">
        <form action="/" method="get">
            <button type="submit">Volver a tienda</button>
        </form>
    </div>

    <div class="container">
        {% for perfume in perfumes %}
        <div class="card">
            <h3>{{ perfume.nombre }}</h3>
            <img src="{{ perfume.imagen }}">
            <p>Precio: ${{ perfume.precio }}</p>
            <form method="post" action="/editar_perfume/{{ perfume.nombre }}">
                <input type="number" name="stock" value="{{ perfume.stock }}" min="0" max="100"><br><br>
                <input type="text" name="precio" value="{{ perfume.precio }}"><br><br>
                <button type="submit">Actualizar</button>
            </form>
        </div>
        {% endfor %}
    </div>

    <div class="card" style="width: 300px; margin: auto; margin-top: 30px;">
        <h2>Agregar Perfume</h2>
        <form method="post" action="/agregar_perfume">
            <input type="text" name="nombre" placeholder="Nombre" required><br><br>
            <input type="text" name="precio" placeholder="Precio" required><br><br>
            <input type="text" name="imagen" placeholder="URL Imagen" required><br><br>
            <input type="number" name="stock" placeholder="Stock" min="0" max="100" required><br><br>
            <button type="submit">Agregar</button>
        </form>
    </div>
</body>
</html>
"""
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect('/admin_login')
        return f(*args, **kwargs)
    return decorated_function

# ---------- Rutas ----------
@app.route('/')
def index():
    perfumes = tabla_perfumes.scan().get('Items', [])
    for perfume in perfumes:
        perfume['precio'] = float(perfume['precio'])
        perfume['stock'] = int(perfume['stock'])

    carrito = session.get('carrito', [])
    total = sum(item['precio'] * item['cantidad'] for item in carrito)
    mensaje_compra = session.pop('mensaje_compra', None)

    return render_template_string(main_page_html, perfumes=perfumes, carrito=carrito, total=total, mensaje_compra=mensaje_compra)

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    mensaje = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            response = tabla_usuarios.get_item(Key={'username': username})
            user = response.get('Item')
            if user and check_password_hash(user['password'], password):
                session['username'] = username
                return redirect('/admin')
            else:
                mensaje = "Credenciales incorrectas"
        except Exception as e:
            mensaje = f"Error: {str(e)}"

    return render_template_string(admin_login_html, mensaje=mensaje)

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    hashed_password = generate_password_hash(password)

    try:
        tabla_usuarios.put_item(Item={'username': username, 'password': hashed_password})
        mensaje = "Usuario registrado correctamente"
    except Exception as e:
        mensaje = f"Error: {str(e)}"

    return render_template_string(admin_login_html, mensaje=mensaje)

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def vista_admin():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        precio = request.form.get('precio', '').strip()
        imagen = request.form.get('imagen', '').strip()
        stock = request.form.get('stock', '').strip()

        if not nombre or not precio or not stock:
            return "Datos incompletos", 400

        try:
            precio = Decimal(precio)
            stock = int(stock)
        except ValueError:
            return "Precio o stock no válidos", 400

        tabla_perfumes.put_item(Item={
            'nombre': nombre,
            'precio': precio,
            'imagen': imagen,
            'stock': stock
        })

    perfumes = tabla_perfumes.scan().get('Items', [])
    for perfume in perfumes:
        perfume['precio'] = float(perfume['precio'])
        perfume['stock'] = int(perfume['stock'])

    return render_template_string(admin_html, perfumes=perfumes)

@app.route('/editar_perfume/<nombre>', methods=['POST'])
@login_required
def editar_perfume(nombre):
    stock = request.form.get('stock', '').strip()
    precio = request.form.get('precio', '').strip()

    if not precio or not stock:
        return "Datos incompletos", 400

    try:
        stock = int(stock)
        precio = Decimal(precio)
    except ValueError:
        return "Precio o stock no válidos", 400

    tabla_perfumes.update_item(
        Key={'nombre': nombre},
        UpdateExpression="set stock = :s, precio = :p",
        ExpressionAttributeValues={':s': stock, ':p': precio}
    )

    return redirect('/admin')

@app.route('/agregar_perfume', methods=['POST'])
@login_required
def agregar_perfume():
    nombre = request.form.get('nombre', '').strip()
    precio = request.form.get('precio', '').strip()
    imagen = request.form.get('imagen', '').strip()
    stock = request.form.get('stock', '').strip()

    if not nombre or not precio or not stock:
        return "Datos incompletos", 400

    try:
        precio = Decimal(precio)
        stock = int(stock)
    except ValueError:
        return "Precio o stock no válidos", 400

    tabla_perfumes.put_item(Item={
        'nombre': nombre,
        'precio': precio,
        'imagen': imagen,
        'stock': stock
    })

    return redirect('/admin')

@app.route('/agregar_carrito', methods=['POST'])
def agregar_carrito():
    if 'carrito' not in session:
        session['carrito'] = []

    nombre = request.form['nombre']
    precio = float(request.form['precio'])

    response = tabla_perfumes.get_item(Key={'nombre': nombre})
    perfume = response.get('Item')

    if perfume and int(perfume['stock']) > 0:
        carrito = session['carrito']
        for item in carrito:
            if item['nombre'] == nombre:
                item['cantidad'] += 1
                break
        else:
            carrito.append({'nombre': nombre, 'precio': precio, 'cantidad': 1})

        session['carrito'] = carrito
        session.modified = True

    return redirect('/')

@app.route('/eliminar_carrito', methods=['POST'])
def eliminar_carrito():
    nombre = request.form['nombre']
    carrito = session.get('carrito', [])
    carrito = [item for item in carrito if item['nombre'] != nombre]
    session['carrito'] = carrito
    session.modified = True
    return redirect('/')

@app.route('/comprar', methods=['POST'])
def comprar():
    carrito = session.get('carrito', [])

    for item in carrito:
        nombre = item['nombre']
        cantidad = item['cantidad']

        response = tabla_perfumes.get_item(Key={'nombre': nombre})
        perfume = response.get('Item')

        if perfume:
            nuevo_stock = int(perfume['stock']) - cantidad
            if nuevo_stock < 0:
                session['mensaje_compra'] = f"Stock insuficiente para {nombre}"
                return redirect('/')

            tabla_perfumes.update_item(
                Key={'nombre': nombre},
                UpdateExpression="set stock = :s",
                ExpressionAttributeValues={':s': nuevo_stock}
            )

    session['carrito'] = []
    session['mensaje_compra'] = "¡Gracias por tu compra!"
    session.modified = True
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)