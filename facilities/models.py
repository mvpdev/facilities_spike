from django.db import models

class LGA(models.Model):
    name = models.CharField(max_length=20)
    slug = models.SlugField()
    
    def facilities_by_type(self):
        oput = []
        for ftype in FacilityType.objects.all():
            facilities = list(Facility.objects.filter(ftype=ftype, lga=self).all())
            averages = []
            totals = []
            for variable in ftype.ordered_variables:
                averages.append(variable.calculate_average_for_lga(self))
                totals.append(variable.calculate_total_for_lga(self))
            oput.append(
                (ftype, facilities, averages, totals)
            )
        return oput

class Facility(models.Model):
    name = models.CharField(max_length=20)
    ftype = models.ForeignKey('FacilityType', related_name="facilities")
    lga = models.ForeignKey(LGA, related_name="facilities", null=True)
    
    def set_value_for_variable_and_date(self, variable, date, value):
        d, created = DataRecord.objects.get_or_create(variable=variable, facility=self, date_value=date)
        d.value=value
        d.save()
    
    def get_latest_value_for_variable(self, variable):
        try:
            variable = DataRecord.objects.filter(facility=self, variable=variable).order_by('-date_value')[0]
        except IndexError:
            variable = None
        return variable
    
    def values_in_order(self):
        return [self.get_latest_value_for_variable(v) for v in self.ftype.ordered_variables]

class Variable(models.Model):
    name = models.CharField(max_length=20)
    data_type = models.CharField(max_length=20)
    
    def calculate_total_for_lga(self, lga):
        if self.data_type == "string":
            return None
        else:
            records = DataRecord.objects.filter(variable=self, facility__lga=lga)
            tot = 0
            for record in records:
                tot += record.value
            return tot
    
    def calculate_average_for_lga(self, lga):
        if self.data_type == "string":
            return None
        else:
            records = DataRecord.objects.filter(variable=self, facility__lga=lga)
            count = records.count()
            if count == 0:
                return 0
            tot = 0
            for record in records:
                tot += record.value
            return tot / count

class DataRecord(models.Model):
    """
    Not sure if we want to use different columns for data types or do
    some django Meta:abstract=True stuff to have different subclasses of DataRecord
    behave differently. For now, this works and is pretty clean.
    """
    float_value = models.FloatField(null=True)
    text_value = models.CharField(null=True, max_length=20)
    variable = models.ForeignKey(Variable, related_name="data_records")
    facility = models.ForeignKey(Facility, related_name="data_records")
    date_value = models.DateField(null=True)

    _data_type = None
    def get_data_type(self):
        #caches the data_type in the python object.
        if self._data_type is None:
            self._data_type = self.variable.data_type
        return self._data_type
    data_type = property(get_data_type)
    
    def get_value(self):
        if self.data_type == "string":
            return self.text_value
        else:
            return self.float_value
    
    def date_string(self):
        if self.date_value is None:
            return "No date"
        else:
            return self.date_value.strftime("%D")
    
    def set_value(self, val):
        if self.variable.data_type == "string":
            self.text_value = val
        else:
            self.float_value = val
    
    value = property(get_value, set_value)


class FacilityType(models.Model):
    """
    A model to hold data specific to the FacilityType (...in MVIS this was the Sector)
    """
    name = models.CharField(max_length=20)
    slug = models.SlugField()
    variables = models.ManyToManyField(Variable, related_name="facility_types")
    variable_order_json = models.TextField(null=True)
    
    _ordered_variables = None
    def get_ordered_variables(self):
        """
        Order of variables is something that came up *a lot* in MVIS.
        
        The (fugly) code below uses self.variables (m2m field) but orders
        the results based on the JSON list of ids in "variable_order_json".
        """
        if self._ordered_variables is not None:
            return self._ordered_variables
        #I think it makes sense to pull all the variables into memory.
        variables = list(self.variables.all())
        if self.variable_order_json is None:
            ordered_ids = []
        else:
            import json
            ordered_ids = json.loads(self.variable_order_json)
        #aack... fugly code below
        n_ordered_variables = []
        for vid in ordered_ids:
            try:
                found_variable = [z for z in variables if z.id==vid][0]
                variables.pop(variables.index(found_variable))
                n_ordered_variables.append(found_variable)
            except IndexError:
                pass
        self._ordered_variables = n_ordered_variables + variables
        return self._ordered_variables
    ordered_variables = property(get_ordered_variables)
    
    def set_variable_order(self, variable_list, autosave=True):
        if len(variable_list)==0:
            return
        if isinstance(variable_list[0], int):
            variable_id_list = variable_list
        else:
            variable_id_list = [v.id for v in variable_list]
        import json
        self.variable_order_json = json.dumps(variable_id_list)
        self._ordered_variables = None
        if autosave:
            self.save()