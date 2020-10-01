from flask_wtf import FlaskForm
from wtforms import Stringfield, PasswordField
from wtforms.validators import DataRequired, Email, Length

class UserAddForm(FlaskForm):
    """Form for adding a user"""

    username= Stringfield('Username', validators=[DataRequired])
    email = Stringfield('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])
    