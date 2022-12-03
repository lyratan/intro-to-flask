from flask import Flask,redirect
from flask import render_template
from flask import request
from flask import session
from bson.json_util import loads, dumps
from flask import make_response
import database as db
import authentication
import ordermanagement as om
import logging

app = Flask(__name__)

# Set the secret key to some random bytes.
# Keep this really secret!
app.secret_key = b's@g@d@c0ff33!'


logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.INFO)


@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

@app.route('/invalid', methods=['GET', 'POST'])
def invalid():
    return render_template('invalid.html')

@app.route('/auth', methods = ['GET', 'POST'])
def auth():
    username = request.form.get('username')
    password = request.form.get('password')

    is_successful, user = authentication.login(username, password) 
    app.logger.info('%s', is_successful)
    if(is_successful):
        session["user"] = user
        return redirect('/')
    else:
        return redirect('invalid')


@app.route('/logout')
def logout():
    session.pop("user",None)
    session.pop("cart",None)
    return redirect('/')



@app.route('/')
def index():
    return render_template('index.html', page="Index")

@app.route('/products')
def products():
    product_list = db.get_products()
    return render_template('products.html', page="Products", product_list=product_list)

@app.route('/productdetails')
def productdetails():
    code = request.args.get('code', '')
    product = db.get_product(int(code))

    return render_template('productdetails.html', code=code, product=product)

@app.route('/addtocart')
def addtocart():
    code = request.args.get('code', '')
    product = db.get_product(int(code))
    item=dict()
    # A click to add a product translates to a 
    # quantity of 1 for now

    item["qty"] = 1
    item["name"] = product["name"]
    item["subtotal"] = product["price"]*item["qty"]
    item["code"] = code

    if(session.get("cart") is None):
        session["cart"]={}

    cart = session["cart"]
    cart[code]=item
    session["cart"]=cart
    return redirect('/cart')

@app.route('/updatecart', methods=['POST'])
def updatecart():
    code = request.form.getlist("code")
    qty = request.form.getlist("qty")

    for code, qty in zip(code, qty):
        if (qty != ''):
            product = db.get_product(int(code))
            item=dict()

            item["qty"] = int(qty)
            item["name"] = product["name"]
            item["subtotal"] = product["price"]*item["qty"]
            item["code"] = code
        
            cart = session["cart"]
            cart[code] = item
            session["cart"]=cart
    return redirect('/cart')

@app.route('/removeitem', methods=["POST"])
def removeitem():
    cart = session["cart"]
    code = request.form.get('code')
    del cart[code]
    session["cart"]=cart
    return render_template("cart.html")

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/branches')
def branches():
    branches = db.get_branches()

    return render_template('branches.html', page="Branches", branches=branches)

@app.route('/branchdetails')
def branchdetails():
    code = request.args.get('code', '')
    branch = db.get_branch(int(code))

    return render_template('branchdetails.html', branch=branch)

@app.route('/aboutus')
def aboutus():
    return render_template('aboutus.html', page="About Us")

@app.route('/checkout')
def checkout():
    # clear cart in session memory upon checkout
    om.create_order_from_cart()
    session.pop("cart",None)
    return redirect('/ordercomplete')

@app.route('/ordercomplete')
def ordercomplete():
    return render_template('ordercomplete.html')

@app.route('/pastorders')
def pastorders():
    if (session.get("user") is not None):
        orders = db.get_past_orders(session["user"]["username"])

        return render_template('pastorders.html', orders=orders)
    else:
        return redirect('/login')

@app.route('/changepassword')
def changepassword():
    if (session.get("user") is not None):
        return render_template('changepassword.html')
    else:
        return redirect('/login')

@app.route('/updatepassword', methods=['POST'])
def updatepassword():
    response = True
    current_password = request.form.get('currentpassword')
    new_password1 = request.form.get('newpassword1')
    new_password2 = request.form.get('newpassword2')

    user = db.get_user(session["user"]["username"])
    if (current_password != user["password"]):
        response = False
    
    if (new_password1 != new_password2):
        response = False
    
    if (response):
        db.update_password(user["username"], new_password1)

    return render_template('changepassword.html', response=response)

@app.route('/api/products/<int:code>',methods=['GET'])
def api_get_product(code):
    resp = make_response(dumps(db.get_product(code)))
    resp.mimetype = 'application/json'
    return resp

