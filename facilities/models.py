from django.db import models

class Facility(models.Model):
    name = models.CharField(max_length=20)
    ftype = models.ForeignKey('FacilityType', null=True, related_name="facilities")
    
    def set_value_for_variable(self, variable, value):
        d, created = DataRecord.objects.get_or_create(variable=variable, facility=self)
        d.value=value
        d.save()
    
    def get_value_for_variable(self, variable):
        try:
            variable = DataRecord.objects.get(facility=self, variable=variable)
        except DataRecord.DoesNotExist:
            variable = None
        return variable
    
    def values_in_order(self):
        var_list = []
        for v in self.ordered_variables():
            var_list.append(self.get_value_for_variable(v))
        return var_list
    
    def ordered_variables(self):
        return self.ftype.ordered_variables()

class Variable(models.Model):
    name = models.CharField(max_length=20)
    data_type = models.CharField(max_length=20)

class DataRecord(models.Model):
    float_value = models.FloatField(null=True)
    text_value = models.CharField(null=True, max_length=20)
    variable = models.ForeignKey(Variable, related_name="data_records")
    facility = models.ForeignKey(Facility, related_name="data_records")
    
    def get_value(self):
        if self.variable.data_type == "string":
            return self.text_value
        else:
            return self.float_value
    
    def set_value(self, val):
        if self.variable.data_type == "string":
            self.text_value = val
        else:
            self.float_value = val
    
    value = property(get_value, set_value)


class FacilityType(models.Model):
    name = models.CharField(max_length=20)
    slug = models.SlugField()
    
    def ordered_variables(self):
        """
        I don't know the _best_ way to do this, but we want an ordered list of variables.
        """
        return [ftv.variable for ftv in self.expected_variables.order_by('display_order')]

class FacilityTypeVariable(models.Model):
    facility_type = models.ForeignKey(FacilityType, related_name="expected_variables")
    variable = models.ForeignKey(Variable)
    display_order = models.IntegerField()
