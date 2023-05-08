from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError

from libdatasources.DataSource import DataSource
from libdatasources.PatentView import PatentView
from libdatasources.SemanticScholar import SemanticScholar
lookup_classes: list[DataSource] = [SemanticScholar, PatentView]

class NameSearchForm(FlaskForm):
    search_query = StringField('Search', validators=[DataRequired(), Length(min=1, max=30)])
    search_query_two = StringField('Search Second Name (Optional)')
    submitname = SubmitField('Search Name', render_kw={'id': 'nameformsubmit'})
    def validate_search_query(form, field):
        name = field.data.strip()
        has_data = [x.check_name(name) for x in lookup_classes]
        #print(has_data)
        if not all(has_data):
            raise ValidationError("1st Field: Invalid name - no matches in any database")
    def validate_search_query_two(form, field):
        name = field.data.strip()
        if len(name) > 1:
            has_data = [x.check_name(name) for x in lookup_classes]
            #print(has_data)
            if not all(has_data):
                raise ValidationError("2nd Field: Invalid name - no matches in any database")

class IDSearchForm(FlaskForm):
    datasources = [lookup_class.source for lookup_class in lookup_classes]
    idsource = SelectField(u'Database Select', choices = datasources)
    iddata = StringField('ID', validators=[DataRequired(), Length(min=5, max=30)])
    idsource_two = SelectField(u'Database Select', choices = datasources)
    iddata_two = StringField('ID #2 (Optional)')

    submitid = SubmitField('Search ID', render_kw={'id': 'idformsubmit'})

    def validate_iddata(form, field):
        for i, lookup_class in enumerate(lookup_classes):
            match_source = (form.idsource.data == lookup_class.source)
            if match_source and not lookup_class.check_id(field.data):
                raise ValidationError(f"1st field: Invalid ID for {lookup_class.source}")
        #raise ValidationError(f"Invalid datasource of {form.idsource.data}")

    def validate_iddata_two(form, field):
        input_id = field.data.strip()
        if len(input_id) == 0:
            return
        for i, lookup_class in enumerate(lookup_classes):
            match_source = (form.idsource.data == lookup_class.source)
            if match_source and not lookup_class.check_id(field.data):
                raise ValidationError(f"2nd field: Invalid ID for {lookup_class.source}")
        #raise ValidationError(f"Invalid datasource of {form.idsource.data}")
