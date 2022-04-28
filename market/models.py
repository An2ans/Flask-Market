from market import db, bcrypt, login_manager
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


#After calling SQLalchemy, you can create "classes" called models

class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), nullable=False, unique=True, primary_key=True)
    username = db.Column(db.String(length=30), nullable=False, unique=True)
    email = db.Column(db.String(length=50), nullable=False, unique=True)
    hash = db.Column(db.String(length=60), nullable=False)
    cash = db.Column(db.Integer(), nullable=False, default=1000)
    items = db.relationship("Item", backref="owned_user", lazy=True)  

    @property 
    def cash_format(self):
        if len(str(self.cash)) >= 4:
            return f"{str(self.cash)[:-3]},{str(self.cash)[-3:]}$"
        else:
            return f"{self.cash}$"


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
            



class Item(db.Model):
    id = db.Column(db.Integer(), primary_key=True, )
    name = db.Column(db.String(length=30), nullable=False, unique=True)  #type of data, ;imit to 30, not null, unique
    price = db.Column(db.Integer(),nullable=False)
    barcode = db.Column(db.String(length=12), nullable=False, unique=True)
    description = db.Column(db.String(length=1024), nullable=False, unique=True)
    owner = db.Column(db.Integer(), db.ForeignKey("user.id"))

    def __repr__(self):
        return f"Item {self.name}"

    def buy(self, user):
        self.owner = user.id
        user.cash -= self.price
        db.session.commit()

    def sell(self, user):
        self.owner = None
        user.cash += self.price
        db.session.commit()