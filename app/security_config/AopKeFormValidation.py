from wtforms import StringField
from flask_wtf import FlaskForm
from wtforms.validators import Length
from bleach import clean


class AopKeFormValidation(FlaskForm):
    searchFieldAOP = StringField('searchFieldAOP', validators=[Length(max=1024)])
    searchFieldKE = StringField('searchFieldKE', validators=[Length(max=1024)])
    stressorDropdown = StringField('stressorDropdown', validators=[Length(max=128)])
    organDropdown = StringField('organDropdown', validators=[Length(max=1024)])
    lifeStageDropdown = StringField('lifeStageDropdown', validators=[Length(max=1024)])
    sexDropdown = StringField('sexDropdown', validators=[Length(max=1024)])
    cellValue = StringField('cellValue', validators=[Length(max=1024)])
    taxValue = StringField('taxValue', validators=[Length(max=128)])


def sanitize_form(form):
    if form.searchFieldAOP.data:
        form.searchFieldAOP.data = clean(form.searchFieldAOP.data)

    if form.searchFieldKE.data:
        form.searchFieldKE.data = clean(form.searchFieldKE.data)
