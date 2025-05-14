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
@app.route('/')
def index():
    return render_template_string(login_html, mensaje=None)

@app.route('/usuario')
def usuario():
    if 'username' not in session:
        return redirect('/')
    username = session['username']
    celulares = tabla_celulares.scan().get('Items', [])
    # Convertir Decimal a float
    for celular in celulares:
        celular['precio'] = float(celular['precio'])
        celular['stock'] = int(celular['stock'])

    carrito = session.get('carrito', [])
    total = sum(float(item['precio']) * int(item['cantidad']) for item in carrito)
    mensaje_stock = session.pop('mensaje_stock', None)
    mensaje_compra = session.pop('mensaje_compra', None)
    return render_template_string(main_page_html, username=username, celulares=celulares, carrito=carrito, total=total, mensaje_compra=mensaje_compra, mensaje_stock=mensaje_stock)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    if not username or not password:
        return render_template_string(login_html, mensaje="Por favor completa todos los campos")

    try:
        response = tabla_usuarios.get_item(Key={'username': username})
        user = response.get('Item')
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            session['carrito'] = []
            celulares = tabla_celulares.scan().get('Items', [])
            for celular in celulares:
                celular['precio'] = float(celular['precio'])
                celular['stock'] = int(celular['stock'])
            return render_template_string(main_page_html, username=username, celulares=celulares, carrito=session['carrito'], total=0, mensaje_compra=None, mensaje_stock=None)
        else:
            return render_template_string(login_html, mensaje="Credenciales incorrectas")
    except Exception as e:
        return render_template_string(login_html, mensaje=f"Error: {str(e)}")

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']

    if not username or not password:
        return render_template_string(login_html, mensaje="Por favor completa todos los campos")

    try:
        existing = tabla_usuarios.get_item(Key={'username': username}).get('Item')
        if existing:
            return render_template_string(login_html, mensaje="El usuario ya existe")

        hashed_password = generate_password_hash(password)
        tabla_usuarios.put_item(Item={'username': username, 'password': hashed_password})
        return render_template_string(login_html, mensaje="Usuario registrado correctamente")
    except Exception as e:
        return render_template_string(login_html, mensaje=f"Error: {str(e)}")

@app.route('/agregar_carrito', methods=['POST'])
def agregar_carrito():
    if 'carrito' not in session:
        session['carrito'] = []

    try:
        nombre = request.form.get('nombre')
        precio_str = request.form.get('precio')

        if not nombre or not precio_str:
            raise ValueError("Nombre o precio no proporcionado")

        precio = float(precio_str)

        response = tabla_celulares.get_item(Key={'nombre': nombre})
        celular = response.get('Item')

        if not celular:
            mensaje = "Producto no encontrado"
        else:
            stock = int(celular.get('stock', 0))
            carrito = session['carrito']

            for item in carrito:
                if item['nombre'] == nombre:
                    if item['cantidad'] < stock:
                        item['cantidad'] += 1
                        mensaje = None
                    else:
                        mensaje = "No hay más stock disponible"
                    break
            else:
                if stock > 0:
                    carrito.append({'nombre': nombre, 'precio': precio, 'cantidad': 1})
                    mensaje = None
                else:
                    mensaje = "Producto agotado"

            session['carrito'] = carrito

        celulares = tabla_celulares.scan().get('Items', [])
        for celular in celulares:
            celular['precio'] = float(celular['precio'])
            celular['stock'] = int(celular['stock'])

        total = sum(item['precio'] * item['cantidad'] for item in session['carrito'])

        return render_template_string(
            main_page_html,
            username=session.get('username', 'Invitado'),
            celulares=celulares,
            carrito=session['carrito'],
            total=total,
            mensaje_stock=mensaje,
            mensaje_compra=None
        )

    except Exception as e:
        mensaje = f"Error al procesar la solicitud: {str(e)}"
        celulares = tabla_celulares.scan().get('Items', [])
        for celular in celulares:
            celular['precio'] = float(celular['precio'])
            celular['stock'] = int(celular['stock'])

        total = sum(item['precio'] * item['cantidad'] for item in session.get('carrito', []))

        return render_template_string(
            main_page_html,
            username=session.get('username', 'Invitado'),
            celulares=celulares,
            carrito=session.get('carrito', []),
            total=total,
            mensaje_stock=mensaje,
            mensaje_compra=None
        )

@app.route('/eliminar_carrito', methods=['POST'])
def eliminar_carrito():
    nombre = request.form['nombre']
    carrito = session.get('carrito', [])
    for item in carrito:
        if item['nombre'] == nombre:
            item['cantidad'] -= 1
            if item['cantidad'] <= 0:
                carrito.remove(item)
            break
    session['carrito'] = carrito
    celulares = tabla_celulares.scan().get('Items', [])
    for celular in celulares:
        celular['precio'] = float(celular['precio'])
        celular['stock'] = int(celular['stock'])
    total = sum(float(item['precio']) * int(item['cantidad']) for item in carrito)
    return render_template_string(main_page_html, username=session['username'], celulares=celulares, carrito=carrito, total=total, mensaje_stock=None, mensaje_compra=None)

@app.route('/comprar', methods=['POST'])
def comprar():
    carrito = session.get('carrito', [])
    if not carrito:
        session['mensaje_stock'] = "El carrito está vacío"
        return redirect('/usuario')

    try:
        for item in carrito:
            nombre = item['nombre']
            cantidad = item['cantidad']

            response = tabla_celulares.get_item(Key={'nombre': nombre})
            celular = response.get('Item')
            if not celular:
                session['mensaje_stock'] = f"Producto {nombre} no encontrado"
                return redirect('/usuario')
            stock = int(celular.get('stock', 0))

            if stock < cantidad:
                session['mensaje_stock'] = f"Stock insuficiente para {nombre}"
                return redirect('/usuario')

            nuevo_stock = stock - cantidad
            tabla_celulares.update_item(
                Key={'nombre': nombre},
                UpdateExpression='SET stock = :val',
                ExpressionAttributeValues={':val': nuevo_stock}
            )

        session['carrito'] = []
        session['mensaje_compra'] = "¡Compra exitosa! Gracias por tu compra."
        return redirect('/usuario')
    except Exception as e:
        session['mensaje_stock'] = f"Error al procesar la compra: {str(e)}"
        return redirect('/usuario')

@app.route('/admin', methods=['GET', 'POST'])
def vista_admin():
    if 'username' not in session:
        return redirect('/')

    mensaje = None

    if request.method == 'POST':
        try:
            nombre = request.form['nombre']
            precio = Decimal(request.form['precio'])
            imagen = request.form['imagen']
            stock = int(request.form['stock'])

            if not nombre or not imagen:
                mensaje = "Todos los campos son obligatorios"
            else:
                tabla_celulares.put_item(Item={
                    'nombre': nombre,
                    'precio': precio,
                    'imagen': imagen,
                    'stock': stock
                })
                mensaje = "Celular agregado exitosamente"
        except Exception as e:
            mensaje = f"Error: {str(e)}"

    celulares = tabla_celulares.scan().get('Items', [])
    for celular in celulares:
        celular['precio'] = float(celular['precio'])
        celular['stock'] = int(celular['stock'])
    return render_template_string(admin_html, username=session['username'], celulares=celulares, mensaje=mensaje)

@app.route('/editar_celular/<nombre>', methods=['POST'])
def editar_celular(nombre):
    nuevo_stock = int(request.form['stock'])
    nuevo_precio = Decimal(request.form['precio'])

    if nuevo_stock > 100:
        return "<h3 style='color:red;'>El stock no puede ser mayor a 100.</h3><a href='/admin'>Volver</a>"

    try:
        tabla_celulares.update_item(
            Key={'nombre': nombre},
            UpdateExpression="SET precio = :precio, stock = :stock",
            ExpressionAttributeValues={
                ':precio': nuevo_precio,
                ':stock': nuevo_stock
            }
        )
        return redirect('/admin')
    except Exception as e:
        return f"<h3 style='color:red;'>Error al actualizar celular: {str(e)}</h3><a href='/admin'>Volver</a>"

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)