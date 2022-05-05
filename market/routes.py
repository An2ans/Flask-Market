import os

from market import app, db
from flask import render_template, redirect, url_for, flash, request, session, Flask
from market.models import Stocks, Users, Wallet, Purchases, Sales
from market.forms import RegisterForm, LoginForm, BuyForm, SellForm
from flask_login import login_user, logout_user, login_required, current_user


# from cs50 import SQL
# from flask_session import Session
# from tempfile import mkdtemp
# from werkzeug.security import check_password_hash, generate_password_hash

from market.helpers import lookup, usd

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

quotes_buy = list()
quotes_sell = list()


# Home route
@app.route("/")
@app.route("/home")
def home_page():
    return render_template("home.html")

# Index route
@app.route("/index", methods=['GET', 'POST'])
@login_required
def index_page():
    # This is to filter those items that have not been purchased yet, without it the items will stay on page. Owned items will be displayed on the right.
    stocks = Stocks.query.all()
    stocks_wallet = Wallet.query.filter_by(user_id=current_user.id)
    if request.method == 'POST':
        # item_to_buy = Item.query.filter_by(name=request.form.get("item_to_buy")).first()
        # item_to_sell = Item.query.filter_by(name=request.form.get("item_to_sell")).first()
        # Buy items from marketplace
        if item_to_buy:
            if current_user.cash >= item_to_buy.price: 
                item_to_buy.buy(current_user)
                flash(f"Your purchase is completed! {item_to_buy.name} for {item_to_buy.price}$", category="success")
                return redirect(url_for("index_page"))
            else:
                flash("There is not enough cash to purchase this item", category="danger")
                return redirect(url_for("index_page"))
        # Sell items to marketplace
        elif item_to_sell and item_to_sell.owner == current_user.id :
            item_to_sell.sell(current_user)
            flash(f"You have successfully sold {item_to_sell.name} for {item_to_sell.price}$", category="success")
            return redirect(url_for("index_page"))
    else:
        return render_template("index.html", stocks=stocks, stocks_wallet=stocks_wallet)




# Register new users
@app.route("/register", methods=['GET', 'POST'])
def register_page():
    form = RegisterForm()
    if form.validate_on_submit():
        user_to_create = Users(username=form.username.data, email=form.email.data, password=form.password.data)
        db.session.add(user_to_create)
        db.session.commit()
        login_user(user_to_create)
        flash(f"Account {user_to_create.username} created successfully!", category="success")
        return redirect(url_for('index_page'))
    if form.errors != {}:
        for err in form.errors.values():
            flash(f"There was an error while creating the account {err}", category="danger")
    return render_template("register.html", form=form)

# Login users
@app.route("/login", methods=["GET", "POST"])
def login_page():
    form = LoginForm()
    if request.method == "POST":
        if form.validate_on_submit():
            user_req = Users.query.filter_by(username=form.username.data).first()
            password_req = form.password.data
            if user_req and user_req.check_password(password_req):
                login_user(user_req)
                flash(f"Successfully logged in as: {user_req.username}", category="success")
                return redirect(url_for("index_page"))
            else:
                flash("Username and password does not match. Please, try again.", category="danger")

    return render_template("login.html", form=form)

# Logout
@app.route("/logout")
def logout_page():
    logout_user()
    flash("Successfully logged out", category="info")
    return redirect(url_for("home_page"))


# Buy shares of stock
@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy_page():
    stocks_list = Stocks.query.all()
    form = BuyForm()
    av_cash = float(current_user.cash)
    # Generate def stocks
    if len(stocks_list) <= 4:
        stocks_def = ["FB", "MSFT", "AAPL", "GOOGL", "IBM"]
        for stock in stocks_def:
            try:
                q = lookup(stock)
                db.session.add(Stocks(symbol=q["symbol"], name=q["name"]))
            except:
                pass
        db.session.commit()

    if request.method == "POST":

        # Quote a stock 
        if form.quote.data:
            stock = form.stock.data
            shares = form.shares.data
            quote = lookup(stock)
            if quote == None :
                flash("There has been an issue with this search, please try again", category="danger")
                return redirect(url_for("buy_page"))
            else:
                try:
                    shares_wallet = Wallet.query.filter_by(user_id=current_user.id, stock=quote["symbol"]).first().shares
                    price_paid = Wallet.query.filter_by(user_id=current_user.id, stock=quote["symbol"]).first().price_paid
                except:
                    shares_wallet = 0
                    price_paid = 0

            # This is to add the stock entry in the db if it doesnt exist
            if not Stocks.query.filter_by(symbol=quote["symbol"]).first() :
                db.session.add(Stocks(symbol=quote["symbol"], name=quote["name"]))
                db.session.commit()

            # Then we add the rest of values and append it to the quotes list
            quote["shares"] = shares
            quote["shares_wallet"] = shares_wallet
            quote["price_paid"] = price_paid
            quotes_buy.append(quote)
            if len(quotes_buy) > 10 :
                quotes_buy.pop(0)

            return render_template("buy.html", form=form, stocks_list=stocks_list, av_cash=av_cash, quotes=reversed(quotes_buy))
        
        if form.submit.data:
            stock_to_buy = Stocks.query.filter_by(symbol=request.form.get("stock_to_buy")).first()
            shares_to_buy = int(request.form.get("shares_to_buy"))
            price_to_buy = float(request.form.get("price_to_buy"))
            
            if av_cash < (shares_to_buy * price_to_buy):
                flash("There is no enough cash for this transaction", category="danger")
                return redirect(url_for("buy_page"))
            else:
                stock_to_buy.buy(current_user, shares_to_buy, price_to_buy)
                flash(f"Your purchase is completed! You have acquired {shares_to_buy} shares of {stock_to_buy.name} for a total of  {price_to_buy * shares_to_buy}$. The new shares are now in your wallet.", category="success")
                return redirect(url_for("buy_page"))


    # Get Request:
    else:
        return render_template("buy.html", form=form, stocks_list=stocks_list, av_cash=av_cash, quotes=reversed(quotes_buy))


# Sell shares of stock
@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell_page():
    form = SellForm()
    av_cash = float(current_user.cash)


    if request.method == "POST":

        # Quote a stock 
        if form.quote.data:
            stock = form.stock.data.upper()
            wallet = Wallet.query.filter_by(user_id=current_user.id, stock=stock).first()
            quote = lookup(stock)
            if quote == None :
                flash("There has been an issue with this search, please try again", category="danger")
                return redirect(url_for("sell_page"))
            else:
                quote["shares"] = int(form.shares.data)
                try:
                    quote["shares_wallet"] = wallet.shares 
                    quote["price_paid"] = wallet.price_paid
                except:
                    quote["shares_wallet"] = 0
                    quote["price_paid"] = 0
                quotes_sell.append(quote)
            if len(quotes_sell) > 10 :
                quotes_sell.pop(0)

            return render_template("sell.html", form=form, av_cash=av_cash, quotes=reversed(quotes_sell))
        
        if form.submit.data:
            stock_to_sell = Stocks.query.filter_by(symbol=request.form.get("stock_to_sell")).first()
            shares_to_sell = int(request.form.get("shares_to_sell"))
            price_to_sell = float(request.form.get("price_to_sell"))
            wallet = Wallet.query.filter_by(user_id=current_user.id, stock=stock_to_sell.symbol).first()
            shares_wallet = wallet.shares if wallet else 0
            
            if shares_wallet < shares_to_sell:
                flash(f"There are no enough shares of this stock in your wallet to complete this transaction: Your wallet: {shares_wallet} Your order: {shares_to_sell}", category="danger")
                return redirect(url_for("sell_page"))
            else:
                stock_to_sell.sell(current_user, shares_to_sell, price_to_sell)
                flash(f"Your sale is completed! You have sold {shares_to_sell} shares of {stock_to_sell.name} for a total of  {price_to_sell * shares_to_sell}$. The new shares are now in your wallet.", category="success")
                return redirect(url_for("sell_page"))


    # Get Request:
    else:
        return render_template("sell.html", form=form, av_cash=av_cash, quotes=reversed(quotes_sell))


# History of records:

@app.route("/history", methods=["GET", "POST"])
@login_required
def history_page():
    purchases = Purchases.query.filter_by(user_id=current_user.id).all()
    sales = Sales.query.filter_by(user_id=current_user.id).all()
    av_cash = current_user.cash
    

    return render_template("history.html", av_cash=av_cash, purchases=purchases, sales=sales)



# @app.route("/buy", methods=["GET", "POST"])
# @login_required
# def buy():
#     
#     # First check to have all inputs
#     list = db.execute("SELECT stock_symbol from stocks LIMIT 10")
#     if request.method == "POST":
#         if not request.form.get("symbol") or not request.form.get("shares"):
#             return apology("Sorry, there was an issue with your purchase order. Please try again")

#         #I've added a table where to see the symbol and full name of all quoted stocks, to work fine we need to add the stock info to the table
#         symbol = request.form.get("symbol").upper()
#         quote = lookup(symbol)
#         if not quote:
#             return apology("Invalid stock symbol")
#         if not db.execute("SELECT * from stocks WHERE stock_symbol = ?", symbol):
#             db.execute("INSERT INTO stocks VALUES (?, ?)", quote["symbol"], quote["name"] )

#         # Checking the number of shares is correct: first forcing it to be int, then checking it is greater than 0
#         number = request.form.get("shares")
#         try:
#             int(number)
#             number = int(number)
#         except ValueError:
#             return apology("Incorrect amount of shares to buy/sell")

#         if number <= 0:
#             return apology("Incorrect amount of shares to buy/sell")

#         #Then check if user has enough cash, I've calculated the new available cash to use it later, it must be >= 0 to continue
#         price = quote["price"]
#         avCash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"]
#         newAvCash = avCash - price * number
#         if newAvCash < 0:
#             apology("There is not enough cash for this transaction")

#         # If cash is enough, we register the transaction and update cash in users table. I have added a confirmation step so user first have to quote the stock, then confirm the purchase.
#         if request.form.get("confirmation"):
#             db.execute("INSERT INTO purchases (user_id, stock_symbol, stock_amount, total_paid) VALUES (?, ?, ?, ?) ", session["user_id"], symbol, number, price * number)
#             db.execute("UPDATE users SET cash = ? WHERE id = ?", newAvCash, session["user_id"])

#             #I've created wallet table where to store the total amount of shares each user has, to use it in index. Here the table is updated
#             avStocks = db.execute("SELECT stock_amount FROM wallet WHERE user_id = ? AND stock_symbol = ? ", session["user_id"], symbol)
#             if not avStocks:
#                 db.execute("INSERT INTO wallet (user_id, stock_symbol, stock_amount) VALUES (?, ?, ?)", session["user_id"], symbol, number)
#             else:
#                 totalStocks = avStocks[0]["stock_amount"] + number
#                 db.execute("UPDATE wallet SET stock_amount = ?, modified_on = CURRENT_TIMESTAMP WHERE user_id = ? AND stock_symbol = ?", totalStocks, session["user_id"], symbol)
#             return redirect("/")
#         else:
#             return render_template("buy.html", quote=quote, number=number, newAvCash=newAvCash)
#     else:
#         return render_template("buy.html", list=list)






