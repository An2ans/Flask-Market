from market import db, bcrypt, login_manager
from flask_login import UserMixin
from sqlalchemy.sql import func


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


#After calling SQLalchemy, you can create "classes" called models

class Users(db.Model, UserMixin):
    id = db.Column(db.Integer(), nullable=False, unique=True, primary_key=True, autoincrement=True)
    username = db.Column(db.String(length=30), nullable=False, unique=True)
    email = db.Column(db.String(length=50), nullable=False, unique=True)
    hash = db.Column(db.String(length=60), nullable=False)
    cash = db.Column(db.Integer(), nullable=False, default=1000)


    # To hash the password I'm using Bcrypt. First we set up the property password: plain text from form
    @property
    def password(self):
        return self.password
    # Then, using a setter, bcrypt transforms the plain text into a hash, which is stored in the db
    @password.setter
    def password(self, plaintext_password):
        self.hash = bcrypt.generate_password_hash(plaintext_password).decode("utf-8")

    def check_password(self, password_req):
        return bcrypt.check_password_hash(self.hash, password_req)
            



class Stocks(db.Model):
    symbol = db.Column(db.String(), primary_key=True, nullable=False, unique=True)
    name = db.Column(db.String(length=30), nullable=False, unique=True)  #type of data, ;imit to 30, not null, unique

    def __repr__(self):
        return f"Stock {self.symbol}"

    def buy(self, user, shares, price):
        # Update cash
        user.cash -= price * shares
        # Update / create new wallet entry. Update both number of shares and price per share 
        if db.session.query(Wallet).filter_by(user_id=user.id, stock=self.symbol).first():
            wallet = db.session.query(Wallet).filter_by(user_id=user.id, stock=self.symbol)
            total_shares = int(wallet.first().shares) + shares
            price_paid = (wallet.first().price_paid * wallet.first().shares + shares * price) / total_shares
            wallet.update({"shares": total_shares, "price_paid": price_paid }, synchronize_session="fetch")
        else:
            db.session.add(Wallet(user_id=user.id, stock=self.symbol, price_paid=price, shares=shares ))
        # Add Purchases entry and commit
        db.session.add(Purchases(user_id=user.id, stock=self.symbol, price=price, shares=shares, total_paid=(shares*price) ))
        db.session.commit()

    def sell(self, user, shares, price):
        # Update cash
        user.cash += price * shares
        # Update / delete wallet entry. 
        if db.session.query(Wallet).filter_by(user_id=user.id, stock=self.symbol).first():
            wallet = db.session.query(Wallet).filter_by(user_id=user.id, stock=self.symbol)
            total_shares = int(wallet.first().shares) - shares
            if total_shares == 0:
                wallet.delete()
            else:
                wallet.update({"shares": total_shares}, synchronize_session="fetch")
        # Add Sales entry and commit
        db.session.add(Sales(user_id=user.id, stock=self.symbol, price=price, shares=shares, total_received=(shares*price) ))
        db.session.commit()

class Wallet(db.Model):
  id = db.Column(db.Integer(), nullable=False, unique=True, primary_key=True, autoincrement=True)
  user_id = db.Column(db.Integer(), db.ForeignKey("users.id"))
  stock = db.Column(db.String(), db.ForeignKey("stocks.symbol"))
  price_paid = db.Column(db.Integer(), nullable=False)
  shares = db.Column(db.Integer(), nullable=False)

class Purchases(db.Model):
  id = db.Column(db.Integer(), nullable=False, unique=True, primary_key=True, autoincrement=True)
  user_id = db.Column(db.Integer(), db.ForeignKey("users.id")) 
  stock = db.Column(db.String(), db.ForeignKey("stocks.symbol"))
  shares = db.Column(db.Integer(), nullable=False)
  price = db.Column(db.Integer(), nullable=False)
  total_paid = db.Column(db.Integer(), nullable=False)
  created_on = db.Column(db.DateTime(), nullable=False, server_default=func.now())
  
class Sales(db.Model):
  id = db.Column(db.Integer(), nullable=False, unique=True, primary_key=True, autoincrement=True)
  user_id = db.Column(db.Integer(), db.ForeignKey("users.id")) 
  stock = db.Column(db.String(), db.ForeignKey("stocks.symbol"))
  shares = db.Column(db.Integer(), nullable=False)
  price = db.Column(db.Integer(), nullable=False)
  total_received = db.Column(db.Integer(), nullable=False)
  created_on = db.Column(db.DateTime(), nullable=False, server_default=func.now())

