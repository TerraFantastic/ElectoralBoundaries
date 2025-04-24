from django.shortcuts import render
from django import forms
import geopandas as gpd
import pandas as pd
import requests
import os

class AddressForm(forms.Form):
    address = forms.CharField(max_length=1000, label="", widget=forms.TextInput(attrs={'placeholder':'Start Entering Your Address Here', 'size': '50', "class":"input"}))
    lat = forms.DecimalField(max_digits=25, decimal_places=20, widget=forms.HiddenInput)
    long = forms.DecimalField(max_digits=25, decimal_places=20, widget=forms.HiddenInput)

# Create your views here.
def home(request):
    return render(request, "boundary/home.html", {
        "form":AddressForm()
    })

def BoundaryCheck(request):

    #Grab form data
    filledAddress = AddressForm(request.GET)
    
    #Check form data is valid, if so, grab address and coords
    if filledAddress.is_valid():
        address = filledAddress.cleaned_data["address"]
        lat = filledAddress.cleaned_data["lat"]
        long = filledAddress.cleaned_data["long"]

    #Put address info and coords into a dataframe
    addressdf = pd.DataFrame({"address":[address], "x":long, "y":lat})

    #Convert data frame to points data
    geometry = gpd.points_from_xy(addressdf.x, addressdf.y, crs="EPSG:4326")

    #Read in json files with old and new boundary data
    boundarynewGDF = gpd.read_file(os.path.join(os.path.dirname(__file__), "boundarynew.json"))
    boundaryoldGDF = gpd.read_file(os.path.join(os.path.dirname(__file__), "boundaryold.json"))

    #Set up CRS Info
    boundarynewGDF = boundarynewGDF.set_crs(crs="EPSG:2193")
    boundarynewGDF = boundarynewGDF.to_crs(crs="EPSG:4326")
    boundaryoldGDF = boundaryoldGDF.set_crs(crs="EPSG:2193")
    boundaryoldGDF = boundaryoldGDF.to_crs(crs="EPSG:4326")

    #Run Within Test to determine which old and new boundary the point is in 
    withintableold = boundaryoldGDF.contains(geometry[0], align=True)
    withintablenew = boundarynewGDF.contains(geometry[0], align=True)

    # List of Electorates with Polygons which are Multi-Polygons
    MultiPolys = ["Auckland Central", "Kaipara ki Mahurangi", "Northland", "Rongotai"]
    #List of Electorates with No Changes
    No_change = ["Hamilton East", "Hamilton West", "Tukituki", "New Plymouth", "Coromandel", "Port Waikato", "Waikato", "Taupō"
                 , "Nelson", "West Coast-Tasman", "Kaikōura", "Waimakariri", "Banks Peninsula", "Rangitata", "Waitaki", "Taieri"
                 , "Dunedin"]

    #Use for loop to find index where within operation returned true in current boundaries
    for n, i in enumerate(withintableold):
        if i == True:
            oldboundname = boundaryoldGDF["GED2020_V1_00_NAME"][n]

            #Set Changetrue to True, Change to False if name is within no_change list
            changetrue = True
            for i in No_change:
                if i == oldboundname:
                    changetrue = False

            #If mulitpolgon, pass through two sets of vertices
            if oldboundname in MultiPolys:
                oldgeom1 = list(boundaryoldGDF.explode().loc[n].iloc[0]["geometry"].exterior.coords)
                oldgeomlists = [list(elem) for elem in oldgeom1]
                for elem in oldgeomlists:
                    elem.reverse()

                oldgeom2 = list(boundaryoldGDF.explode().loc[n].iloc[1]["geometry"].exterior.coords)
                AucklandSecondOld = [list(elem) for elem in oldgeom2]
                for elem in AucklandSecondOld:
                    elem.reverse()

            #If single polygon, pass through one set of vertices and placeholder string 
            else:
                oldgeom = list(boundaryoldGDF.explode().loc[n]["geometry"].exterior.coords)
                oldgeomlists = [list(elem) for elem in oldgeom]
                for elem in oldgeomlists:
                    elem.reverse()
                AucklandSecondOld ="Not Applicable"

    #Use for loop to find index where within operation returned true in new boundaries
    for n, i in enumerate(withintablenew):
        if i == True:
            newboundname = boundarynewGDF["Proposed_General_Electorate"][n]

            #If mulitpolgon, pass through two sets of vertices
            if newboundname in MultiPolys:
                newgeom1 = list(boundarynewGDF.explode().loc[n].iloc[0]["geometry"].exterior.coords)
                newgeomlists = [list(elem) for elem in newgeom1]
                for elem in newgeomlists:
                    elem.reverse()

                newgeom2 = list(boundarynewGDF.explode().loc[n].iloc[1]["geometry"].exterior.coords)
                AucklandSecondNew = [list(elem) for elem in newgeom2]
                for elem in AucklandSecondNew:
                    elem.reverse()

            #If single polygon, pass through one set of vertices and placeholder string 
            else:
                newgeom = list(boundarynewGDF.explode().loc[n]["geometry"].exterior.coords)
                newgeomlists = [list(elem) for elem in newgeom]
                AucklandSecondNew = "Not Applicable"
                for elem in newgeomlists:
                    elem.reverse()
                    
    return render(request, "boundary/boundarycheck.html", {
        "address":address,
        "oldbound":oldboundname,
        "newbound":newboundname,
        "lat":lat,
        "long":long,
        "newb":newgeomlists,
        "oldb":oldgeomlists,
        "AucklandSecondOld":AucklandSecondOld,
        "AucklandSecondNew":AucklandSecondNew,
        "changetrue":changetrue
    })
