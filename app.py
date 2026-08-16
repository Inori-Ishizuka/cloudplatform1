from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from zoneinfo import ZoneInfo

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///inventory.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# 商品テーブル
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(100))
    stock = db.Column(db.Integer, default=0)

    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(ZoneInfo("Asia/Tokyo")),
        onupdate=lambda: datetime.now(ZoneInfo("Asia/Tokyo"))
    )

# 入出庫履歴テーブル
class StockHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    action = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(ZoneInfo("Asia/Tokyo"))
    )
# ホーム
@app.route("/")
def index():

    low_stock_count = Product.query.filter(Product.stock <= 5).count()

    return render_template(
        "index.html",
        low_stock_count=low_stock_count
    )

# 商品登録
@app.route("/add", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        product = Product(
            name=request.form["name"],
            price=int(request.form["price"]),
            category=request.form["category"],
            stock=int(request.form["stock"])
        )

        db.session.add(product)
        db.session.commit()

        return redirect(url_for("product_list"))

    return render_template("add_product.html")

# 商品一覧
@app.route("/products")
def product_list():
    keyword = request.args.get("keyword")

    if keyword:
        products = Product.query.filter(
            Product.name.contains(keyword)
        ).all()
    else:
        products = Product.query.all()

    return render_template("products.html", products=products)

# 商品編集
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_product(id):
    product = Product.query.get_or_404(id)

    if request.method == "POST":
        product.name = request.form["name"]
        product.price = int(request.form["price"])
        product.category = request.form["category"]
        product.stock = int(request.form["stock"])

        db.session.commit()
        return redirect(url_for("product_list"))

    return render_template("edit_product.html", product=product)

# 商品削除
@app.route("/delete/<int:id>")
def delete_product(id):
    product = Product.query.get_or_404(id)

    db.session.delete(product)
    db.session.commit()

    return redirect(url_for("product_list"))

# 入庫
@app.route("/stock_in/<int:id>", methods=["GET", "POST"])
def stock_in(id):
    product = Product.query.get_or_404(id)

    if request.method == "POST":
        quantity = int(request.form["quantity"])

        product.stock += quantity

        history = StockHistory(
            product_name=product.name,
            action="入庫",
            quantity=quantity
        )

        db.session.add(history)
        db.session.commit()

        return redirect(url_for("product_list"))

    return render_template("stock_in.html", product=product)


# 出庫
@app.route("/stock_out/<int:id>", methods=["GET", "POST"])
def stock_out(id):
    product = Product.query.get_or_404(id)

    if request.method == "POST":
        quantity = int(request.form["quantity"])

        # 在庫不足を防ぐ
        if quantity > product.stock:
            return "在庫が不足しています"

        product.stock -= quantity

        history = StockHistory(
            product_name=product.name,
            action="出庫",
            quantity=quantity
        )

        db.session.add(history)
        db.session.commit()

        return redirect(url_for("product_list"))

    return render_template("stock_out.html", product=product)

#画面履歴
@app.route("/history")
def history():

    histories = StockHistory.query.order_by(
        StockHistory.created_at.desc()
    ).all()

    return render_template(
        "history.html",
        histories=histories
    )

#在庫不足
@app.route("/low_stock")
def low_stock():

    products = Product.query.filter(Product.stock <= 5).all()

    return render_template(
        "low_stock.html",
        products=products
    )

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(host="0.0.0.0", port=5000)