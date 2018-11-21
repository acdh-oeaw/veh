from django.conf.urls import url
from . import import_views
from . import export_views

app_name = 'teimporter'

urlpatterns = [
    url(r'^import-single-doc/$', import_views.ImportTEI.as_view(), name='import_tei'),
    url(r'^import-placelist/$', import_views.ImportPlaceListTEI.as_view(), name='import_placelist'),
    url(r'^import-listperson/$', import_views.ImportListPerson.as_view(), name='import_listperson'),
    # url(
    #     r'^place/list/export-as-tei$',
    #     export_views.ExportTeiListPlace.as_view(),
    #     name='place_list_as_tei'
    # ),
]
