####   Forms  ####
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm

class SearchForm(FlaskForm):
  q = StringField('Search', [DataRequired()])
  typo = SelectField('Type', choices = [('artist','artist'),('track','track',),('album','album'),('playlist','playlist')])
  submit = SubmitField('Go!')