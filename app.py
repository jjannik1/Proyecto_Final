from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from datetime import date, datetime
from bson.objectid import ObjectId

class Usuario:
    def __init__(self, nombre, email, contraseña, fecha_registro, activo, pedidos):
        self.nombre = nombre
        self.email = email
        self.contraseña = contraseña
        self.fecha_registro = fecha_registro
        self.activo = activo
        self.pedidos = pedidos

    def diccionario(self):
        return {
            "nombre": self.nombre,
            "email": self.email,
            "contraseña": self.contraseña,
            "fecha_registro": self.fecha_registro,
            "activo": self.activo,
            "pedidos": self.pedidos
        }



app = Flask(__name__)

online = MongoClient("mongodb+srv://jjen527:35OpRHzih8l1N14m@jjannik.aliwych.mongodb.net/")

app.db = online.tecno

nombre_admin = "Jannik"
tienda = "TecnoMarket"
fecha = date.today()


#####################################################################################
#####################TiendaOnlineMejorado############################################
#####################################################################################
@app.route("/dashboard")
def dashboard():    

    productos = [producto for producto in app.db.productos.find({})]
    clientes = [cliente for cliente in app.db.clientes.find({})]
    pedidos = [
        {"cliente": "Ana Torres", "total": 120.00, "fecha": "2025-05-01"},
        {"cliente": "Marta López", "total": 340.50, "fecha": "2025-05-03"},
        {"cliente": "Luis Rivas", "total": 75.00, "fecha": "2025-05-04"}
    ]

    total_stock = 0
    for producto in productos:
        total_stock += producto["stock"]

    clientes_activos = 0
    for cliente in clientes:
        if cliente["activo"]:
            clientes_activos += 1

    

    cliente_pedido = clientes[0]
    for cliente in clientes:
        if cliente["pedidos"] > cliente_pedido["pedidos"]:
            cliente_pedido = cliente


    total = 0
    for pedido in pedidos:
        total += pedido["total"]

    return render_template("dashboard.html",nombre_admin=nombre_admin,tienda=tienda,fecha=fecha,productos=productos,clientes=clientes,pedidos=pedidos,total=total,cliente_pedido=cliente_pedido,clientes_activos=clientes_activos,total_stock=total_stock)





@app.route("/añadir-producto", methods=["GET", "POST"])
def anadir_producto():
    mensaje = None
    if request.method == "POST":
        productos = [producto for producto in app.db.productos.find({})]

        #Creamos una variable para guardar el id más alto
        id_mas_alto = 0

        #Recorremos cada producto y revisamos su id
        for producto in productos:
            if "id" in producto and producto["id"] > id_mas_alto:
                id_mas_alto = producto["id"]

        #El nuevo id será uno más
        nuevo_id = id_mas_alto + 1

        #Crear y guardar el producto
        nuevo_producto = {
            "id": nuevo_id,
            "nombre": request.form["nombre"],
            "precio": float(request.form["precio"]),
            "stock": int(request.form["stock"]),
            "categoria": request.form["categoria"]
        }

        app.db.productos.insert_one(nuevo_producto)
        mensaje = "Producto añadido correctamente."

    return render_template("anadir_producto.html", mensaje=mensaje, fecha=fecha)



@app.route("/productos")
def ver_productos():
    productos_cursor = app.db.productos.find()
    productos = []
    for producto in productos_cursor:
        producto["_id"] = str(producto["_id"])
        productos.append(producto)
    return render_template("lista_productos.html", productos=productos,fecha=fecha)



@app.route("/productos/<id_producto>")
def detalle_producto(id_producto):
    product_found = None
    producto = app.db.productos.find_one({"_id": ObjectId(id_producto)})
    if producto:
        return render_template("detalle_producto.html", producto=producto,fecha=fecha)
    else:
        return render_template("404.html",fecha=fecha), 404
    

@app.route("/registro-usuario", methods=["GET", "POST"])
def registro_usuario():
    mensaje = ""
    if request.method == "POST":
        nombre = request.form["nombre"]
        email = request.form["email"]
        contraseña = request.form["contraseña"]
        activ = request.form["actividad"] == "True"
        pedidos = int(request.form["pedidos"])
        nuevo_usuario = Usuario(nombre, email, contraseña, datetime.now(), activ, pedidos)
        app.db.clientes.insert_one(nuevo_usuario.diccionario())
        mensaje = "Usuario registrado con éxito."
    return render_template("registro_usuario.html", mensaje=mensaje, fecha=fecha)

@app.route("/usuarios")
def lista_usuarios():
    clientes = [cliente for cliente in app.db.clientes.find({})]
    return render_template("lista_usuarios.html", clientes=clientes, fecha=fecha)

@app.errorhandler(404)
def pagina_no_encontrada(e):
    return render_template("404.html", fecha=fecha)

@app.errorhandler(500)
def pagina_no_encontrada(e):
    return render_template("404.html", fecha=fecha)


if __name__ == '__main__':
    app.run()
