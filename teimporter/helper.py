from django.conf import Settings
from django.core.exceptions import MultipleObjectsReturned

from apis_core.apis_entities.models import *
from apis_core.apis_relations.models import *
from apis_core.apis_labels.models import *
from apis_core.apis_metainfo.models import *


def dict_to_pers(pers_dict, entity=None):
    if entity:
        pass
    else:
        entity = Person()
    if pers_dict['surname']:
        entity.name = pers_dict['surname']
    else:
        entity.name = 'no name provided'
    entity.save()

    if pers_dict['forename']:
        entity.first_name = pers_dict['forename']

    if pers_dict['death_date_written']:
        entity.end_date_written = pers_dict['death_date_written']
    if pers_dict['death_date']:
        entity.end_date = pers_dict['death_date']

    if pers_dict['birth_date_written']:
        entity.start_date_written = pers_dict['birth_date_written']
    if pers_dict['birth_date']:
        entity.start_date = pers_dict['birth_date']

    if pers_dict['sex'] == "f":
        entity.gender = 'female'
    elif pers_dict['sex'] == 'm':
        entity.gender = 'male'

    if pers_dict['rolename']:
        entity.rolename = pers_dict['rolename']

    if pers_dict['namelink']:
        ent_titl, _ = Title.obejcts.get_or_create(
            name=pers_dict['namelink']
        )
        entity.title.add(ent_titl)

    if pers_dict['occupation']:
        for x in pers_dict['occupation']:
            prof, _ = ProfessionType.objects.get_or_create(name=x)
            entity.profession.add(prof)

    if pers_dict['birth_place']:
        try:
            pl, _ = Place.objects.get_or_create(
                name=pers_dict['birth_place']
            )
        except MultipleObjectsReturned:
            pl, _ = Place.objects.get_or_create(
                name="potential_duplicate__{}".format(pers_dict['birth_place'])
            )
        rel_type, _ = PersonPlaceRelation.objects.get_or_create(
            name="born in", name_reverse="place of birth"
        )
        pers_pla, _ = PersonPlace.objects.get_or_create(
            relation_type=rel_type,
            related_person=entity,
            related_place=pl
        )
        if pers_dict['birth_date_written']:
            pers_pla.start_date_written = pers_dict['birth_date_written']
            pers_pla.end_date_written = pers_dict['birth_date_written']
        if pers_dict['birth_date']:
            pers_pla.start_date = pers_dict['birth_date']
            pers_pla.end_date = pers_dict['birth_date']
        pers_pla.save()
    pers_pla = None
    if pers_dict['death_place']:
        try:
            pl, _ = Place.objects.get_or_create(
                name=pers_dict['death_place']
            )
        except MultipleObjectsReturned:
            pl, _ = Place.objects.get_or_create(
                name="potential_duplicate__{}".format(pers_dict['death_place'])
            )
        rel_type, _ = PersonPlaceRelation.objects.get_or_create(
            name="died in", name_reverse="place of death"
        )
        pers_pla, _ = PersonPlace.objects.get_or_create(
            relation_type=rel_type,
            related_person=entity,
            related_place=pl
        )
        if pers_dict['death_date_written']:
            pers_pla.start_date_written = pers_dict['death_date_written']
            pers_pla.end_date_written = pers_dict['death_date_written']
        if pers_dict['death_date']:
            pers_pla.end_date = pers_dict['death_date']
            pers_pla.end_date = pers_dict['death_date']
        pers_pla.save()

    if pers_dict['alt_names']:
        for x in pers_dict['alt_names']:
            la_type, _ = LabelType.objects.get_or_create(
                name=x['type']
            )
            label, _ = Label.objects.get_or_create(
                label=x['label'],
                label_type=la_type,
                temp_entity=entity
            )
    entity.save()
    print(entity.id)
    return entity


def create_uri_strings(pers_dict):
    uris = []
    for x in pers_dict['idnos']:
        try:
            project = settings.PROJECTS[x['domain']]
            uri = {
                'string': "/".join([project['base_url'], x['path']]),
                'domain': x['domain']
                }
            uris.append(uri)
        except KeyError:
            uri = {
                'string': x['path'],
                'domain': x['domain']
                }
            uris.append(uri)
    return uris


def create_pers_from_dicts(pers_dicts):
    entities = {
        'new': [],
        'updated': [],
        'all': []
    }
    for pers_dict in pers_dicts:
        if pers_dict['idnos']:
            uri_strings = create_uri_strings(pers_dict)
            temp_uris = []
            entity = None
            for uri_string in uri_strings:
                temp_uri, created = Uri.objects.get_or_create(uri=uri_string['string'])
                temp_uri.domain = uri_string['domain']
                temp_uri.save()
                temp_uris.append(temp_uri)
            for uri in temp_uris:
                if uri.entity:
                    entity = uri.entity
            if entity:
                print(ascii(entity.name))
                for uri in temp_uris:
                    uri.entity = entity
                    uri.save()
                entities['updated'].append(entity)
                entities['all'].append(entity)
            else:
                print('no entity yet exists, create one')

                entity = dict_to_pers(pers_dict)
                for uri in temp_uris:
                    uri.entity = entity
                    uri.save()
                entities['new'].append(entity)
                entities['all'].append(entity)
    return entities


def create_upload_md(user, some_form, ent_type='person'):
    current_user = user
    cd = some_form.cleaned_data
    super_collection, _ = Collection.objects.get_or_create(name='teihencer-all')
    current_group, _ = Group.objects.get_or_create(name=current_user.username)
    current_group.user_set.add(current_user)
    file = cd['file'].read()
    src, _ = Source.objects.get_or_create(orig_filename=cd['file'].name, author=current_user)
    # kind, _ = TextType.objects.get_or_create(
    #     name='process tei:list{}'.format(ent_type), entity=ent_type
    # )
    # text, _ = Text.objects.get_or_create(text=file, source=src, kind=kind)
    parent_collection, _ = Collection.objects.get_or_create(
        name=cd['collection'],
        parent_class=super_collection
    )
    parent_collection.groups_allowed.add(current_group)
    parent_collection.save()
    return {'col': parent_collection, 'src': src, 'text': None, 'file': file, 'user': current_user}


def create_metatdata(user, some_form):
    current_user = user
    cd = some_form.cleaned_data
    super_collection, _ = Collection.objects.get_or_create(name='teihencer-all')
    current_group, _ = Group.objects.get_or_create(name=current_user.username)
    current_group.user_set.add(current_user)
    file = cd['file'].read()
    print(file)
    src, _ = Source.objects.get_or_create(orig_filename=cd['file'].name, author=current_user)
    kind, _ = TextType.objects.get_or_create(name='process tei:listPlace', entity='place')
    text, _ = Text.objects.get_or_create(text=file, source=src, kind=kind)
    if cd['new_sub_collection'] == "":
        col, _ = Collection.objects.get_or_create(
            name="{}".format(cd['collection'])
        )
        if col.parent_class is None:
            col.parent_class = super_collection
            col.save()
        else:
            pass
    else:
        parent_collection, _ = Collection.objects.get_or_create(
            name=cd['collection'],
            parent_class=super_collection
        )
        parent_collection.groups_allowed.add(current_group)
        parent_collection.save()
        col, _ = Collection.objects.get_or_create(
            name=cd['new_sub_collection'],
            parent_class=parent_collection,
        )
    col.groups_allowed.add(current_group)
    col.save()
    return {'col': col, 'src': src, 'text': text, 'file': file}
