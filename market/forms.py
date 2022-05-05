from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField
from wtforms.validators import Length, EqualTo, Email, DataRequired, ValidationError, NumberRange
from market.models import Users

class RegisterForm(FlaskForm):
  def validate_username(self, username_to_check):
    user = Users.query.filter_by(username=username_to_check.data).first()
    if user: 
      raise ValidationError("Username already exist. Please try a different one")

  def validate_email(self, email_to_check):
    email = Users.query.filter_by(email=email_to_check.data).first()
    if email:
      raise ValidationError("Email address already exists. Please try a different one")

  username = StringField(label="Username:", validators=[Length(min=2, max=30), DataRequired()])
  email = StringField(label="Email:", validators=[Email(), DataRequired()])
  password = PasswordField(label="Password:", validators=[Length(min=8), DataRequired()])
  passwordConfirm = PasswordField(label="Confirm your Password:", validators=[EqualTo("password"), DataRequired()])
  submit = SubmitField(label="Create Account")

class LoginForm(FlaskForm):
  username = StringField(label="Username:", validators=[Length(min=2, max=30), DataRequired()])
  password = PasswordField(label="Password:", validators=[Length(min=8), DataRequired()])
  submit = SubmitField(label="Log In")

class BuyForm(FlaskForm):
  stock = StringField(label="Stock:", validators=[Length(min=2, max=5), DataRequired()] )
  shares = IntegerField(label="Shares:", validators=[DataRequired(), NumberRange(min=1, message="The minimun number of shares you can buy is 1")] )
  submit = SubmitField(label="Buy")
  quote = SubmitField(label="Quote")


class SellForm(FlaskForm):
  stock = StringField(label="Stock:", validators=[Length(min=2, max=5), DataRequired()] )
  shares = IntegerField(label="Shares:", validators=[DataRequired(), NumberRange(min=1, message="The minimun number of shares you can sell is 1")] )
  submit = SubmitField(label="Sell")
  quote = SubmitField(label="Quote")

