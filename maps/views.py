#-*- coding: utf-8-*-

from django.shortcuts import render, get_object_or_404
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.http import HttpResponse
from .forms import *
from .models import Place
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import get_template
from django.template import Context
import json, urllib
from datetime import datetime, timedelta

# Create your views here.
def index(request):
    return all_place_list_return(request)

def load_gmaps(request):
    places = Place.objects.all()
    markers = []
    for place in places:
        markers.append({"name": place.place_name, "lat": place.lat, "lng": place.lng})
    #markers = [{"name":"123", "lat":41.2, "lng": 12.3}]
    return render(request, 'maps/gmaps.html', {'markerTs': markers})

@csrf_exempt
def ajax_add(request):
    if request.method == "POST" and request.is_ajax():
        print 'Raw Data: "%s"' % request.body
        form = PlaceForm(request.POST)
        if form.is_valid():
            new_place = form.save(commit=False)
            new_place.capital = True
            capital_places = Place.objects.filter(capital=True)
            for place in capital_places:
                dest_coord = str(place.lat) + "," + str(place.lng)
                orig_coord = request.POST.get("lat", "") + "," + request.POST.get("lng", "")
                transit_time = calc_time_logic(orig_coord, dest_coord)
                if transit_time < 3600:
                    new_place.group_name = place.group_name
                    new_place.capital = False
                    break
            new_place.save()

    pls = get_template('maps/place_list.html')
    ctx = Context({ 'places': Place.objects.all() })
    return HttpResponse(pls.render(ctx))

def calc_time_logic(orig_coord, dest_coord):
    url = "https://maps.googleapis.com/maps/api/distancematrix/json?origins=" + orig_coord + "&destinations=" + dest_coord + "&mode=trasit&language=ko-KR&key=AIzaSyAIqZxhPY5au_XncU-ZM5hpD8Ty_UkAoWg"
    result= json.load(urllib.urlopen(url))
    transit_time = result['rows'][0]['elements'][0]['duration']['value']
    return transit_time

def capital_update_check(update):
    if update == "on":
        return True
    else:
        return False

def GetTime(sec):
    sec = timedelta(seconds=sec)
    d = datetime(1,1,1) + sec

    #print("DAYS:HOURS:MIN:SEC")
    #print("%d:%d:%d:%d" % (d.day-1, d.hour, d.minute, d.second))
    return str(d.hour) + ":" + str(d.minute)

@csrf_exempt
def ajax_delete(request):
    if request.method == "POST" and request.is_ajax():
        print 'Raw Delete Data: "%s"' % request.POST.get("pk", "")
        pk = request.POST.get("pk", "")
        deletePlace = get_object_or_404(Place, pk=pk)
        if deletePlace.capital:
            group_places = Place.objects.filter(group_name=deletePlace.group_name)
            min_time = 999999
            for place in group_places:
                if place.id == deletePlace.id:
                    continue
                dest_coord = str(place.lat) + "," + str(place.lng)
                orig_coord = str(deletePlace.lat) + "," + str(deletePlace.lng)
                transit_time = calc_time_logic(orig_coord, dest_coord)
                print transit_time
                if transit_time < min_time:
                    candPlace = place
                    min_time = transit_time

            candPlace.update(capital=True)
        deletePlace.delete()
        #form.delete()

    pls = get_template('maps/place_list.html')
    ctx = Context({ 'places': Place.objects.all() })
    return HttpResponse(pls.render(ctx))

@csrf_exempt
def ajax_capital(request):
    if request.method == "POST" and request.is_ajax():
        print 'Raw Delete Data: "%s"' % request.POST.get("update", "")
        update = request.POST.get("update", "")
        pk = request.POST.get("pk", "")
        update = capital_update_check(update)
        Place.objects.filter(pk=pk).update(capital=update)
        #form.delete()

    pls = get_template('maps/place_list.html')
    ctx = Context({ 'places': Place.objects.all() })
    return HttpResponse(pls.render(ctx))

def place_detail(request, pk):
    if request.method == "POST":
        id = request.POST.get("id", "")
        group_name = request.POST.get("group_name", "")
        capital = request.POST.get("capital", "")
        print 'Raw Delete Data: "%s"' % capital
        capital = capital_update_check(capital)
        #print 'Raw Delete Data: "%s"' % pk.pk
        Place.objects.filter(pk=id).update(group_name=group_name)
        Place.objects.filter(pk=id).update(capital=capital)
        #print form
            #form.save()
        return redirect("index")
    else:
        capitals = []
        place = get_object_or_404(Place, pk=pk)
        capital_places = Place.objects.filter(capital=True)
        for cplace in capital_places:
            if cplace.id == place.id:
                continue
            dest_coord = str(cplace.lat) + "," + str(cplace.lng)
            orig_coord = str(place.lat) + "," + str(place.lng)
            transit_time = calc_time_logic(orig_coord, dest_coord)
            print GetTime(transit_time)
            capitals.append({"id": cplace.id, "group_name": cplace.group_name, "place_name": cplace.place_name, "time": GetTime(transit_time)})
        return render(request, 'maps/place_detail.html', {'place': place, 'capitals': capitals})

def all_place_list_return(request):
    places = Place.objects.all()
    return render(request, 'maps/index.html', {'places': places})
