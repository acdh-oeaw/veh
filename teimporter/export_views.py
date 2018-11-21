# import lxml.etree as ET
# from django.http import HttpResponse
# from django.utils.decorators import method_decorator
# from django.contrib.auth.decorators import login_required
# from apis_core.apis_metainfo.models import Uri
# from apis_core.apis_entities.views import GenericListView
# from apis_core.apis_entities.models import Place
# from apis_core.apis_entities.tables import PlaceTable
# from apis_core.apis_entities.filters import PlaceListFilter
# from apis_core.apis_entities.forms import GenericFilterFormHelper
# from teimporter.teimodule import tei
#
#
# class ExportTeiListPlace(GenericListView):
#
#     """ serializes the filtered entites as TEI-doc (tei:listPlace)"""
#
#     model = Place
#     table_class = PlaceTable
#     filter_class = PlaceListFilter
#     formhelper_class = GenericFilterFormHelper
#
#     def get(self, request):
#         teiprocessor = tei.TeiPlaceList(tei.tei_document)
#         queryset = self.get_queryset()
#         places = []
#         for x in queryset:
#             uris = Uri.objects.filter(entity=x.id)
#             legacy_uris = []
#             normdata_uris = []
#             for temp_uri in uris:
#                 if not temp_uri.uri.startswith(
#                         'http://sws.geonames.org') or temp_uri.uri.startswith('http://d-nb'):
#                     legacy_uris.append(temp_uri)
#                 else:
#                     normdata_uris.append(temp_uri)
#             legacy_uris = [
#                 x.uri for x in uris if not x.uri.startswith('http://sws.geonames.org')
#                 or x.uri.startswith('http://d-nb')]
#             try:
#                 xmlid = legacy_uris[0]
#             except IndexError:
#                 xmlid = uris[0].uri
#             idno = [x.uri for x in uris]
#             places.append(teiprocessor.create_place(
#                 xmlid, x.name, x.lat, x.lng, idno)
#             )
#         placelist = teiprocessor.create_place_index_from_place_elements(places)
#         output = ET.tostring(placelist, encoding="utf-8")
#         response = HttpResponse(output, content_type='application/xhtml+xml')
#         return response
