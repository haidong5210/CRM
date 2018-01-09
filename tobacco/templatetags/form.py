from tobacco.server.sites import site
from django.urls import reverse
from django.template import Library
register = Library()


@register.inclusion_tag("form.html")
def popup(config,form):
    result = []
    for _field in form:
        data_dict = {"popup": None, "filed": _field}
        from django.forms.boundfield import BoundField
        from django.forms.models import ModelChoiceField
        from django.db.models.query import QuerySet
        from django.forms.models import ModelMultipleChoiceField
        if isinstance(_field.field, ModelChoiceField):
            model_cls_name = _field.field.queryset.model
            if model_cls_name in site._registry:
                app_model_name = model_cls_name._meta.app_label, model_cls_name._meta.model_name
                name = "tobacco:%s_%s_add" % app_model_name
                current_url = reverse(name)
                # FK，One,M2M： 当前字段所在的类名和related_name
                model_name = config.model_class._meta.model_name
                related_name = config.model_class._meta.get_field(_field.name).rel.related_name
                popurl = "%s?_popbackid=%s&model_name=%s&related_name=%s" % (current_url,
                                                                             _field.auto_id,model_name,related_name)
                data_dict["popup"] = True
                data_dict["popurl"] = popurl
        result.append(data_dict)
    return {"form":result}