import time
import lxml.etree as ET
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import render
from django.views.generic.edit import FormView
from teimporter.teimodule.tei import TeiReader, TeiPlaceList
from teimporter.teimodule.tei import TeiPersonList
from .forms import UploadFileForm, UploadPlaceListForm, UploadListPersonForm
from .helper import *
from apis_core.apis_entities.models import *
from apis_core.apis_metainfo.models import *
from apis_core.apis_vocabularies.models import TextType
from apis_core.helper_functions.RDFparsers import GenericRDFParser
from apis_core.helper_functions.stanbolQueries import find_loc


@method_decorator(login_required, name="dispatch")
class ImportListPerson(FormView):
    template_name = 'teimporter/import_personlist.html'
    form_class = UploadListPersonForm
    success_url = '.'

    def get_form_kwargs(self):
        kwargs = super(ImportListPerson, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form, **kwargs):
        context = super(ImportListPerson, self).get_context_data(**kwargs)
        current_user = self.request.user
        metadata = create_upload_md(current_user, form)
        context['metadata'] = metadata
        parsed = TeiPersonList(metadata['file'])
        cd = form.cleaned_data
        if cd['gnd_only']:
            personnodes = parsed.parse_listperson(gnd=True)
        else:
            personnodes = parsed.parse_listperson()
        try:
            context['counter'] = personnodes['amount']
        except KeyError:
            context['counter'] = None
        try:
            context['personnodes'] = personnodes['persons']
        except KeyError:
            context['personnodes'] = None
        context['person_dicts'] = []
        if context['personnodes']:
            pers_dicts = []
            for x in context['personnodes']:
                pers_dicts.append(parsed.person2dict(x))
            created = create_pers_from_dicts(pers_dicts)
            for x in created['all']:
                # x.text.add(*[metadata['text']])
                x.collection.add(*[metadata['col']])
                x.source = metadata['src']
            context['created'] = created

        return render(self.request, self.template_name, context)


@method_decorator(login_required, name="dispatch")
class ImportPlaceListTEI(FormView):
    template_name = 'teimporter/import_placelist.html'
    form_class = UploadPlaceListForm
    success_url = '.'

    def get_form_kwargs(self):
        kwargs = super(ImportPlaceListTEI, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form, **kwargs):
        context = super(ImportPlaceListTEI, self).get_context_data(**kwargs)
        current_user = self.request.user
        metadata = create_metatdata(current_user, form)
        context['metadata'] = metadata
        teifile = TeiPlaceList(metadata['file'])
        places = teifile.parse_placelist()
        before = len(Place.objects.all())
        fails = []
        cd = form.cleaned_data
        print(places['amount'])
        if cd['xpath'] == "":
            print('start looking for IDs')
            for y in places['places']:
                place = teifile.place2dict(y)
                xmlid = place['xml:id'][0]
                try:
                    print(place['placeNames'][0]['text'])
                except:
                    print('somethign')
                try:
                    placename = place['placeNames'][0]['text']
                except:
                    placename = place['placeNames']['text']
                res = find_loc([placename], geonames_chains=False, dec_diff=25)
                if res:
                    if res[0]:
                        try:
                            try:
                                plc_fin = GenericRDFParser(res[1]['id'], 'Place').get_or_create()
                            except:
                                plc_fin = GenericRDFParser(res[1][0]['id'], 'Place').get_or_create()
                        except:
                            plc_fin = Place.objects.create(name=placename, status='no match')
                    else:
                        if res[1]:
                            plc_fin = Place.objects.create(name=placename, status='ambigue')
                            for x in res[1]:
                                UriCandidate.objects.create(uri=x['id'], entity=plc_fin)
                        else:
                            plc_fin = Place.objects.create(name=placename, status='no match')
                # link new created place object to text-object
                if plc_fin:
                    plc_fin.text.set([metadata['text']], clear=True)
                    plc_fin.collection.set([metadata['col']], clear=True)
                    plc_fin.source = metadata['src']
                    try:
                        resolver_uri = "{}{}".format(metadata['col'].name, xmlid)
                        legacy_uri, _ = Uri.objects.get_or_create(
                            uri=resolver_uri, domain=metadata['col'].name, entity=plc_fin
                        )
                    except:
                        pass
                    plc_fin.save()
                    try:
                        print('saved: {}'.format(plc_fin))
                    except UnicodeEncodeError:
                        print('saved a place with difficult chars')
        else:
            xpath = cd['xpath']
            for y in places['places']:
                url = teifile.fetch_ID(y, xpath, 'geonames')['fetched_id']
                if url:
                    url = url.strip()
                    print('Normdata uris provided, start fetching data for {}'.format(url))
                    try:
                        plc_fin = GenericRDFParser(url, 'Place').get_or_create()
                        plc_fin = plc_fin
                    except:
                        print('ERROR with ID: {}'.format(url))
                        fails.append(url)
                        plc_fine = None
                else:
                    plc_fine = None
                if plc_fin:
                    plc_fin.text.set([metadata['text']], clear=True)
                    plc_fin.collection.set([metadata['col']], clear=True)
                    plc_fin.source = metadata['src']
                    try:
                        resolver_uri = "{}{}".format(metadata['col'].name, xmlid)
                        legacy_uri, _ = Uri.objects.get_or_create(
                            uri=resolver_uri, domain=metadata['col'].name, entity=plc_fin
                        )
                    except:
                        pass
                    plc_fin.save()

        after = len(Place.objects.all())
        context['counter'] = [before, after]
        context['fails'] = fails
        return render(self.request, self.template_name, context)


@method_decorator(login_required, name="dispatch")
class ImportTEI(FormView):
    template_name = 'teimporter/import_tei.html'
    form_class = UploadFileForm
    success_url = '.'

    def get_form_kwargs(self):
        kwargs = super(ImportTEI, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form, **kwargs):
        context = super(ImportTEI, self).get_context_data(**kwargs)
        current_user = self.request.user
        metadata = create_metatdata(current_user, form)
        cd = form.cleaned_data
        xpath = cd['xpath']
        teifile = TeiReader(metadata['file'])
        added_ids = teifile.add_ids(xpath)
        place_list = teifile.create_place_index(added_ids[0])
        context['place_list'] = ET.tostring(place_list, pretty_print=True, encoding="UTF-8")
        context['processd_file'] = ET.tostring(
            added_ids[1], pretty_print=True, encoding="UTF-8"
        )
        text, _ = Text.objects.get_or_create(text=context['processd_file'], source=metadata['src'])
        kind, _ = TextType.objects.get_or_create(name='process TEI DOC', entity='place')
        kind.collections.add(metadata['col'])
        kind.save()
        text.kind = kind
        text.save()

        placeindex, _ = Text.objects.get_or_create(
            text=context['place_list'], source=metadata['src']
        )
        kind, _ = TextType.objects.get_or_create(name='generated place list', entity='place')
        kind.collections.add(metadata['col'])
        kind.save()
        placeindex.kind = kind
        placeindex.save()
        if cd['enrich']:
            for x in added_ids[0]:
                placename = x['text']
                legacy_id = x['ref']
                res = find_loc([placename], geonames_chains=False, dec_diff=25)
                if res:
                    if res[0]:
                        try:
                            try:
                                plc_fin = GenericRDFParser(res[1]['id'], 'Place').get_or_create()
                            except:
                                plc_fin = GenericRDFParser(res[1][0]['id'], 'Place').get_or_create()
                        except:
                            plc_fin = Place.objects.create(name=placename, status='no match')
                    else:
                        if res[1]:
                            plc_fin = Place.objects.create(name=placename, status='ambigue')
                            for x in res[1]:
                                UriCandidate.objects.create(uri=x['id'], entity=plc_fin)
                        else:
                            plc_fin = Place.objects.create(name=placename, status='no match')
                if plc_fin:
                    plc_fin.text.set([metadata['text']], clear=True)
                    plc_fin.collection.set([metadata['col']], clear=True)
                    plc_fin.source = metadata['src']
                    try:
                        resolver_uri = "{}{}".format(metadata['col'].name, legacy_id)
                        legacy_uri, _ = Uri.objects.get_or_create(
                            uri=resolver_uri, domain=metadata['col'].name, entity=plc_fin
                        )
                    except:
                        pass
                    plc_fin.save()
                    try:
                        print('saved: {}'.format(legacy_id))
                    except UnicodeEncodeError:
                        print('saved a place with difficult chars')

        else:
            pass
        return render(self.request, self.template_name, context)
