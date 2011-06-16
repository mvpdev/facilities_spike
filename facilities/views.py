# Create your views here.
from django.shortcuts import render_to_response
from django.template import RequestContext

from facilities.models import *

def home(request):
    context = RequestContext(request)
    ftype = FacilityType.objects.all()[0]
    # context.facilities = Facility.objects.all()
    # context.variables = ftype.ordered_variables()
    context.ftypes = list(FacilityType.objects.all())
    return render_to_response("list.html", context_instance=context)