from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import Length, EqualTo, Email, DataRequired, ValidationError
from market.models import User

class RegisterForm(FlaskForm):
  def validate_username(self, username_to_check):
    user = User.query.filter_by(username=username_to_check.data).first()
    if user: 
      raise ValidationError("Username already exist. Please try a different one")

  def validate_email(self, email_to_check):
    email = User.query.filter_by(email=email_to_check.data).first()
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

class BuyItemForm(FlaskForm):
  submit = SubmitField(label="Buy Item")

class SellItemForm(FlaskForm):
  submit = SubmitField(label="Sell Item")

