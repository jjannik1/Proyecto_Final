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
    
    session.clear()

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
    pedidos = [pedidos for pedidos in app.db.pedidos.find({})]
    

    total_stock = sum(producto["stock"] for producto in productos)
    clientes_activos = sum(1 for cliente in clientes if cliente["activo"])

    cliente_pedido = clientes[0] if clientes else None
    for cliente in clientes:
        if cliente["pedidos"] > cliente_pedido["pedidos"]:
            cliente_pedido = cliente
    total=0
    for pedido in pedidos:
        total += pedido["total"]

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

        nuevo_producto = {
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
    
    categoria_filtro = request.args.get("categoria")
    diccionario = {}
    if categoria_filtro:
        diccionario["categoria"] = categoria_filtro


    categorias = app.db.productos.distinct("categoria")

    productos_cursor = app.db.productos.find(diccionario)
    productos = []
    for producto in productos_cursor:
        productos.append(producto)
    return render_template("lista_productos.html", productos=productos, fecha=fecha, categoria_filtro=categoria_filtro, categorias=categorias)


@app.route("/productos/<id_producto>")
def detalle_producto(id_producto):
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    producto = app.db.productos.find_one({"_id": ObjectId(id_producto)})
    if producto:
        return render_template("detalle_producto.html", producto=producto, fecha=fecha)
    else:
        return render_template("404.html", fecha=fecha), 404
    
@app.route("/cambiar/<producto_id>" ,  methods=['POST'])
def cambiar(producto_id):

    nuevo_precio = 0.00
    nuevo_stock = 0

    if request.form["precio"]:
        nuevo_precio = float(request.form["precio"])
    if request.form["stock"]:
        nuevo_stock = int(request.form["stock"])

    if nuevo_precio != 0.00 and nuevo_stock != 0:

        app.db.productos.update_one(
            {"_id": ObjectId(producto_id)},
            {"$set": {"stock": nuevo_stock}}
        )

        app.db.productos.update_one(
            {"_id": ObjectId(producto_id)},
            {"$set": {"precio": nuevo_precio}}
        )
    elif nuevo_precio != 0.00 :

        app.db.productos.update_one(
            {"_id": ObjectId(producto_id)},
            {"$set": {"precio": nuevo_precio}}
        )
    
    elif nuevo_stock != 0:
        app.db.productos.update_one(
            {"_id": ObjectId(producto_id)},
            {"$set": {"stock": nuevo_stock}}
        )
    else:
        pass

    return redirect(url_for("ver_productos"))

@app.route("/eliminar-producto/<producto_id>" , methods=['POST'])
def eliminar_producto(producto_id):
    app.db.producto.delete_one({"_id": ObjectId(producto_id)})
    return redirect(url_for("ver_productos"))

@app.route("/registro-usuario", methods=["GET", "POST"])
def registro_usuario():
    mensaje = ""

    if request.method == "POST":
        nombre = request.form["nombre"]
        email = request.form["email"]
        contraseña = request.form["contraseña"]
        activ = True
        pedidos = 0

        
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

@app.route("/activar/<usuario_id>" , methods=['POST'])
def activar(usuario_id):
    app.db.clientes.update_one(
        {"_id": ObjectId(usuario_id)},
        {"$set": {"activo": True}}
    )
    return redirect(url_for("lista_usuarios"))

@app.route("/desactivar/<usuario_id>" , methods=['POST'])
def desactivar(usuario_id):
    app.db.clientes.update_one(
        {"_id": ObjectId(usuario_id)},
        {"$set": {"activo": False}}
    )
    return redirect(url_for("lista_usuarios"))

@app.route("/carrito")
def ver_carrito():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario_id = ObjectId(session["usuario_id"])
    carrito = app.db.carritos.find_one({"usuario_id": usuario_id})    
    productos = carrito.get("productos", []) if carrito else []
    total = sum(item["precio"] * item["cantidad"] for item in productos)
    
    app.db.carritos.update_one(
            {"usuario_id": usuario_id},
            {"$set": {"total": total}},
        )


    return render_template("carrito.html", carrito=productos, usuario_id=usuario_id, total=total, fecha=fecha)


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

        
        app.db.carritos.update_one(
            {"usuario_id": usuario_id},
            {"$set": {"productos": productos}},
        )
    
    flash("Producto agregado al carrito.")
    return redirect(url_for("ver_productos", id_producto=id_producto))


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

@app.route("/pedidos")
def ver_pedidos():
    if len(session) > 0 :
        if session["rol"] == "admin":
                pedidos = [pedidos for pedidos in app.db.pedidos.find({})]

                return render_template("lista_pedidos_admin.html", pedidos=pedidos,fecha=fecha)
        else:
                pedidos_usuario = []
                pedidos = [pedidos for pedidos in app.db.pedidos.find({})]
                sesion = ObjectId(session["usuario_id"])
                for pedido in pedidos:
                    usuario_id = ObjectId(pedido["usuario_id"])
                    if ObjectId(usuario_id) == ObjectId(sesion):
                        pedidos_usuario.append(pedido)
                return render_template("lista_pedidos_clientes.html", pedidos_usuario=pedidos_usuario , fecha=fecha)

@app.route("/comprar/<usuario_id>" , methods=["POST"])
def comprar(usuario_id):
    carrito = app.db.carritos.find_one({"usuario_id": ObjectId(usuario_id)})
    productos = carrito.get("productos", []) if carrito else []
    id_usuario = ObjectId(session["usuario_id"])
    nombre = session["nombre"]
    estado = "Preparacion"
    fecha = datetime.now()

    pedido = {
        "Nombre" : nombre,
        "usuario_id": ObjectId(id_usuario) ,
        "productos":productos,
        "total": float(carrito["total"]) ,
        "estado" :estado,
        "fecha" : fecha
    }
    app.db.pedidos.insert_one(pedido)
    app.db.carritos.update_one(
        {"usuario_id": ObjectId(usuario_id)},
        {"$set": {"productos": []}}
    )
    clientes = app.db.clientes.find_one({"_id": ObjectId(usuario_id)})
    app.db.clientes.update_one(
        {"_id": ObjectId(usuario_id)},
        {"$set": {"pedidos": clientes["pedidos"] + 1}}
    )

    productos2 = [producto for producto in app.db.productos.find({})]

    diccionario_stock = {}

    for producto2 in productos2:

        diccionario_stock[ObjectId(producto2["_id"])] = producto2["stock"]

    print(diccionario_stock)
    for producto in productos:

       
        stock = int(diccionario_stock[ObjectId(producto["producto_id"])])

        app.db.productos.update_one(
            {"_id": ObjectId(producto["producto_id"])},
            {"$set": {"stock": stock - int(producto["cantidad"])}}
        )
    return redirect(url_for("ver_carrito"))

@app.route("/cancelar/<pedido_id>" , methods=["POST"])
def cancelar(pedido_id):
    pedidos = app.db.pedidos.find_one({"_id": ObjectId(pedido_id) })
    clientes = app.db.clientes.find_one({"_id": ObjectId(pedidos["usuario_id"])})
    for productos in pedidos["productos"]:
        producto = app.db.productos.find_one({"_id": ObjectId(productos["producto_id"])})
        app.db.productos.update_one(
            {"_id": ObjectId(productos["producto_id"])},
            {"$set":{"stock" : producto["stock"] + productos["cantidad"]}}
        ) 
    app.db.clientes.update_one(
        {"_id": ObjectId(pedidos["usuario_id"])},
        {"$set": {"pedidos": clientes["pedidos"] - 1}}
    )
    app.db.pedidos.delete_one({"_id": ObjectId(pedido_id)})
    return redirect(url_for("ver_pedidos"))

@app.route("/cambiar_estado/<pedido_id>" , methods=["POST"])
def cambiar_estado(pedido_id):
    app.db.pedidos.update_one(
        {"usuario_id": ObjectId(pedido_id)},
        {"$set": {"estado": "Listo"}}
    )
    return redirect("ver_pedidos")

@app.errorhandler(404)
def pagina_no_encontrada(e):
    return render_template("404.html", fecha=fecha)


@app.errorhandler(500)
def pagina_error_interno(e):
    return render_template("404.html", fecha=fecha)


if __name__ == '__main__':
    app.run(debug=True)
