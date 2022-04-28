from market import app, db
from flask import render_template, redirect, url_for, flash, request
from market.models import Item, User
from market.forms import RegisterForm, LoginForm, BuyItemForm, SellItemForm
from flask_login import login_user, logout_user, login_required, current_user

# Home route
@app.route("/")
@app.route("/home")
def home_page():
    return render_template("home.html")

# Market route
@app.route("/market", methods=['GET', 'POST'])
@login_required
def market_page():
    # This is to filter those items that have not been purchased yet, without it the items will stay on page. Owned items will be displayed on the right.
    items = Item.query.filter_by(owner=None)
    owned_items = Item.query.filter_by(owner=current_user.id)
    buy_form = BuyItemForm()
    sell_form = SellItemForm()
    if request.method == 'POST':
        item_to_buy = Item.query.filter_by(name=request.form.get("item_to_buy")).first()
        item_to_sell = Item.query.filter_by(name=request.form.get("item_to_sell")).first()
        # Buy items from marketplace
        if item_to_buy:
            if current_user.cash >= item_to_buy.price: 
                item_to_buy.buy(current_user)
                flash(f"Your purchase is completed! {item_to_buy.name} for {item_to_buy.price}$", category="success")
                return redirect(url_for("market_page"))
            else:
                flash("There is not enough cash to purchase this item", category="danger")
                return redirect(url_for("market_page"))
        # Sell items to marketplace
        elif item_to_sell and item_to_sell.owner == current_user.id :
            item_to_sell.sell(current_user)
            flash(f"You have successfully sold {item_to_sell.name} for {item_to_sell.price}$", category="success")
            return redirect(url_for("market_page"))
    else:
        return render_template("market.html", items=items, buy_form=buy_form, owned_items=owned_items, sell_form=sell_form)

# Register new users
@app.route("/register", methods=['GET', 'POST'])
def register_page():
    form = RegisterForm()
    if form.validate_on_submit():
        user_to_create = User(username=form.username.data, email=form.email.data, password=form.password.data)
        db.session.add(user_to_create)
        db.session.commit()
        login_user(user_to_create)
        flash(f"Account {user_to_create.username} created successfully!", category="success")
        return redirect(url_for('market_page'))
    if form.errors != {}:
        for err in form.errors.values():
            flash(f"There was an error while creating the account {err}", category="danger")
    return render_template("register.html", form=form)

# Login users
@app.route("/login", methods=["GET", "POST"])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        user_req = User.query.filter_by(username=form.username.data).first()
        password_req = form.password.data
        if user_req and user_req.check_password(password_req):
            login_user(user_req)
            flash(f"Successfully logged in as: {user_req.username}", category="success")
            return redirect(url_for("market_page"))
        else:
            flash("Username and password does not match. Please, try again.", category="danger")

    return render_template("login.html", form=form)

# Logout
@app.route("/logout")
def logout_page():
    logout_user()
    flash("Successfully logged out", category="info")
    return redirect(url_for("home_page"))