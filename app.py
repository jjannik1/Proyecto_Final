from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from datetime import date, datetime
from bson.objectid import ObjectId
from passlib.hash import pbkdf2_sha256

class Usuario:
    def __init__(self, nombre, email, contraseña, fecha_registro, activo, pedidos, rol="Cliente"):
        self.nombre = nombre
        self.email = email
        self.contraseña = contraseña
        self.fecha_registro = fecha_registro
        self.activo = activo
        self.pedidos = pedidos
        self.rol = rol

    def diccionario(self):
        return {
            "nombre": self.nombre,
            "email": self.email,
            "contraseña": self.contraseña,
            "fecha_registro": self.fecha_registro,
            "activo": self.activo,
            "pedidos": self.pedidos,
            "rol": self.rol
        }


app = Flask(__name__)
app.secret_key = "clave_super_secreta"

online = MongoClient("mongodb+srv://jjen527:35OpRHzih8l1N14m@jjannik.aliwych.mongodb.net/")

app.db = online.tecno

nombre_admin = "Jannik"
tienda = "TecnoMarket"
fecha = date.today()


#####################################################################################
##################### TiendaOnlineMejorado ##########################################
#####################################################################################




@app.route("/", methods=["GET", "POST"])
def login():

    if len(session) > 0 :
        if session["rol"] == "admin":
                return redirect(url_for("dashboard"))
        else:
                return redirect(url_for("ver_productos"))
    
    if request.method == "POST":
        email = request.form["email"]
        contraseña = request.form["contraseña"]

        # Buscar usuario por email en la base de datos
        user = app.db.clientes.find_one({"email": email})

        # Verificar si el usuario existe y la contraseña es correcta
        if user and pbkdf2_sha256.verify(contraseña, user["contraseña"]):
            session["usuario_id"] = str(user["_id"])
            session["rol"] = user["rol"]
            session["nombre"] = user["nombre"]

            # Redirigir según el rol del usuario
            if user["rol"] == "admin":
                return redirect(url_for("dashboard"))
            else:
                return redirect(url_for("ver_productos"))
        else:
            flash("Correo o contraseña incorrectos.")

    return render_template("login.html",fecha=fecha)


@app.route("/inicia_admin")
def inicia_admin():
    return redirect(url_for("dashboard"))

@app.route("/inicia_cliente")
def inicia_cliente():
    return redirect(url_for("ver_productos"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if "rol" not in session or session["rol"] != "admin":
        return redirect(url_for("login"))

    productos = [producto for producto in app.db.productos.find({})]
    clientes = [cliente for cliente in app.db.clientes.find({})]
    pedidos = [
        {"cliente": "Ana Torres", "total": 120.00, "fecha": "2025-05-01"},
        {"cliente": "Marta López", "total": 340.50, "fecha": "2025-05-03"},
        {"cliente": "Luis Rivas", "total": 75.00, "fecha": "2025-05-04"}
    ]

    total_stock = sum(producto["stock"] for producto in productos)
    clientes_activos = sum(1 for cliente in clientes if cliente["activo"])

    cliente_pedido = clientes[0] if clientes else None
    for cliente in clientes:
        if cliente["pedidos"] > cliente_pedido["pedidos"]:
            cliente_pedido = cliente

    total = sum(pedido["total"] for pedido in pedidos)

    return render_template(
        "dashboard.html",
        nombre_admin=nombre_admin,
        tienda=tienda,
        fecha=fecha,
        productos=productos,
        clientes=clientes,
        pedidos=pedidos,
        total=total,
        cliente_pedido=cliente_pedido,
        clientes_activos=clientes_activos,
        total_stock=total_stock
    )


@app.route("/añadir-producto", methods=["GET", "POST"])
def anadir_producto():
    if "rol" not in session or session["rol"] != "admin":
        return redirect(url_for("login"))

    mensaje = None
    if request.method == "POST":
        productos = [producto for producto in app.db.productos.find({})]

        id_mas_alto = 0
        for producto in productos:
            if "id" in producto and producto["id"] > id_mas_alto:
                id_mas_alto = producto["id"]

        nuevo_id = id_mas_alto + 1

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
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    productos_cursor = app.db.productos.find()
    productos = []
    for producto in productos_cursor:
        producto["_id"] = str(producto["_id"])
        productos.append(producto)
    return render_template("lista_productos.html", productos=productos, fecha=fecha)


@app.route("/productos/<id_producto>")
def detalle_producto(id_producto):
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    producto = app.db.productos.find_one({"_id": ObjectId(id_producto)})
    if producto:
        return render_template("detalle_producto.html", producto=producto, fecha=fecha)
    else:
        return render_template("404.html", fecha=fecha), 404


@app.route("/registro-usuario", methods=["GET", "POST"])
def registro_usuario():
    mensaje = ""

    if request.method == "POST":
        nombre = request.form["nombre"]
        email = request.form["email"]
        contraseña = request.form["contraseña"]
        activ = request.form.get("actividad", "True") == "True"
        pedidos = int(request.form.get("pedidos", 0))

        
        if app.db.clientes.find_one({"email": email}):
            mensaje = "El email ya está registrado."
        else:
            hashed_password = pbkdf2_sha256.hash(contraseña)
            nuevo_usuario = Usuario(
                nombre, email, hashed_password, datetime.now(), activ, pedidos
            )
            app.db.clientes.insert_one(nuevo_usuario.diccionario())
            app.db.carritos.insert_one({"usuario_id": app.db.clientes.find_one({"email": email})["_id"],"productos": [], "total": 0})

            flash("Usuario registrado con éxito.")
            return redirect(url_for("login"))  

    return render_template("registro_usuario.html", mensaje=mensaje, fecha=fecha)



@app.route("/usuarios")
def lista_usuarios():
    if "rol" not in session or session["rol"] != "admin":
        return redirect(url_for("login"))

    clientes = [cliente for cliente in app.db.clientes.find({})]
    return render_template("lista_usuarios.html", clientes=clientes, fecha=fecha)

@app.route("/eliminar-usuario/<usuario_id>" , methods=['POST'])
def eliminar_usuario(usuario_id):
    app.db.clientes.delete_one({"_id": ObjectId(usuario_id)})
    app.db.carritos.delete_one({"usuario_id": ObjectId(usuario_id)})
    return redirect(url_for("lista_usuarios"))

@app.route("/carrito")
def ver_carrito():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario_id = ObjectId(session["usuario_id"])
    carrito = app.db.carritos.find_one({"usuario_id": usuario_id})    
    productos = carrito.get("productos", []) if carrito else []
    total = carrito.get("total")


    return render_template("carrito.html", carrito=productos, total=total, fecha=fecha)


#Agregar producto al carrito

@app.route("/agregar-al-carrito/<id_producto>", methods=['POST'])
def agregar_al_carrito(id_producto):
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    
    #Necesitamos el id del usuario para poder coger su carrito por eso cogemos del usuario que esta en la sesion su id y despues buscamos la id del usuario en la tabla carritos y coger su carrito
    usuario_id = ObjectId(session["usuario_id"])
    carrito = app.db.carritos.find_one({"usuario_id": usuario_id})

    producto = app.db.productos.find_one({"_id": ObjectId(id_producto)})
    if producto:
        productos = carrito["productos"]
        encontrado = False


        for item in productos:
            if item["producto_id"] == producto["_id"]:
                if item["cantidad"] < producto["stock"]:
                    item["cantidad"] += 1
                    flash("Producto actualizado en el carrito.")
                else:
                    flash("No hay suficiente stock disponible.")
                encontrado = True
                break
            
        if not encontrado:
            if producto["stock"] > 0:
                productos.append({
                    "producto_id": producto["_id"],
                    "nombre": producto["nombre"],
                    "precio": producto["precio"],
                    "cantidad": 1
                })
                flash("Producto agregado al carrito.")
            else:
                flash("Producto sin stock disponible.")

        total = sum(item["precio"] * item["cantidad"] for item in productos)
        app.db.carritos.update_one(
            {"usuario_id": usuario_id},
            {"$set": {"productos": productos}},
            {"$set": {"total": total}}
        )
    
    flash("Producto agregado al carrito.")
    return redirect(url_for("detalle_producto", id_producto=id_producto))


#Eliminar producto del carrito

@app.route("/eliminar-del-carrito/<producto_id>", methods=["POST"])
def eliminar_del_carrito(producto_id):
    if "usuario_id" not in session:
        return redirect(url_for("login"))
    
    usuario_id = ObjectId(session["usuario_id"])
    app.db.carritos.update_one(
        {"usuario_id": usuario_id},
        {"$pull": {"productos": {"producto_id": ObjectId(producto_id)}}}
    )
    flash("Producto eliminado del carrito.")
    return redirect(url_for("ver_carrito"))

    
#Quitar cantidad del producto que esta en el carrito
@app.route("/restar-producto/<producto_id>", methods=["POST"])
def restar_producto(producto_id):
    if "usuario_id" not in session:
        return redirect(url_for("login"))
    
    usuario_id = ObjectId(session["usuario_id"])
    carrito = app.db.carritos.find_one({"usuario_id": usuario_id})
    productos = carrito["productos"]
    for item in productos:
        if str(item["producto_id"]) == producto_id:
            item["cantidad"] -= 1
            if item["cantidad"] <= 0:
                productos.remove(item)
            break

    app.db.carritos.update_one(
        {"usuario_id": usuario_id},
        {"$set": {"productos": productos}}
    )

    return redirect(url_for("ver_carrito"))

#Agregar cantidad del producto que esta en el carrito
@app.route("/sumar-producto/<producto_id>", methods=["POST"])
def sumar_producto(producto_id):
    if "usuario_id" not in session:
        return redirect(url_for("login"))
    
    producto = app.db.productos.find_one({"_id": ObjectId(producto_id)})

    usuario_id = ObjectId(session["usuario_id"])
    carrito = app.db.carritos.find_one({"usuario_id": usuario_id})
    productos = carrito["productos"]

    for item in productos:
        if str(item["producto_id"]) == producto_id:
            stock_disponible = producto["stock"]
            cantidad_actual = item["cantidad"]

            if cantidad_actual < stock_disponible:
                item["cantidad"] += 1
            else:
                flash("No hay suficciente stock disponible")
        break

    app.db.carritos.update_one(
        {"usuario_id": usuario_id},
        {"$set": {"productos": productos}}
    )

    return redirect(url_for("ver_carrito"))


#Vaciar el carrito entero
@app.route("/vaciar-carrito", methods=["POST"])
def vaciar_carrito():
    if "usuario_id" not in session:
        return redirect(url_for("login"))
    
    usuario_id = ObjectId(session["usuario_id"])
    app.db.carritos.update_one(
        {"usuario_id": usuario_id},
        {"$set": {"productos": []}}
    )
    flash("Carrito vaciado")
    return redirect(url_for("ver_carrito"))


@app.errorhandler(404)
def pagina_no_encontrada(e):
    return render_template("404.html", fecha=fecha)


@app.errorhandler(500)
def pagina_error_interno(e):
    return render_template("404.html", fecha=fecha)


if __name__ == '__main__':
    app.run(debug=True)
