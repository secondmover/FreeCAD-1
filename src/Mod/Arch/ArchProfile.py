import FreeCAD, Draft, Part, os
from FreeCAD import Vector
import csv

if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore, QtGui
    from DraftTools import translate
else:
    def translate(ctxt,txt):
        return txt

__title__="FreeCAD Profile"
__author__ = "XX"
__url__ = "XX"

# Presets in the form: Class, Name, Profile type, [profile data]
# Loaded from Mod/Arch/Data/beams.csv
profilefiles = [os.path.join(FreeCAD.getResourceDir(),"Mod","Arch","Presets","profiles.csv")]

def readPresets():
    Presets=[None]
    for profilefile in profilefiles:
        try:
            with open(profilefile, 'rb') as csvfile:
                beamreader = csv.reader(csvfile)
                bid=1 #Unique index
                for row in beamreader:
                    if row[0].startswith("#"):
                        continue
                    try:
                        r=[bid, row[0], row[1], row[2]]
                        for i in range(3,len(row)):
                            r=r+[float(row[i])]
                        if not r in Presets:
                            Presets.append(r)
                        bid=bid+1
                    except ValueError:
                        print "Skipping bad line: "+str(row)
        except IOError:
            print "Could not open ",profilefile
    return Presets

def makeProfile(profile=[0,'REC','REC100x100','R',100,100]):
    '''makeProfile(profile): returns a shape  with the face defined by the profile data'''
    obj = FreeCAD.ActiveDocument.addObject("Part::Part2DObjectPython",profile[2])
    obj.Label = translate("Arch",profile[2])
    if profile[3]=="C":
        _ProfileC(obj, profile)
    elif profile[3]=="H":
        _ProfileH(obj, profile)
    elif profile[3]=="R":
        _ProfileR(obj, profile)
    elif profile[3]=="RH":
        _ProfileRH(obj, profile)
    elif profile[3]=="U":
        _ProfileU(obj, profile)
    else :
        print "Profile not supported"
    if FreeCAD.GuiUp:
        Draft._ViewProviderDraft(obj.ViewObject)
    return obj

class _Profile(Draft._DraftObject):
    '''Superclass for Profile classes'''

    def __init__(self,obj, profile):
        self.Profile=profile
        Draft._DraftObject.__init__(self,obj,"Profile")
        
            
class _ProfileC(_Profile):
    '''A parametric circular tubeprofile. Profile data: [Outside diameter, Inside diameter]'''

    def __init__(self,obj, profile):
        obj.addProperty("App::PropertyLength","OutDiameter","Draft","Outside Diameter").OutDiameter = profile[4]
        obj.addProperty("App::PropertyLength","Thickness","Draft","Wall thickness").Thickness = profile[5]
        _Profile.__init__(self,obj,profile)

    def execute(self,obj):
        pl = obj.Placement
        c1=Part.Circle()
        c1.Radius=obj.OutDiameter.Value
        c2=Part.Circle()
        c2.Radius=obj.OutDiameter.Value-2*obj.Thickness.Value
        cs1=c1.toShape()
        cs2=c2.toShape()
        p=Part.makeRuledSurface(cs2,cs1)
        obj.Shape = p
        obj.Placement = pl
        
class _ProfileH(_Profile):
    '''A parametric H or I beam profile. Profile data: [width, height, web thickness, flange thickness] (see http://en.wikipedia.org/wiki/I-beam for reference)'''

    def __init__(self,obj, profile):
        obj.addProperty("App::PropertyLength","Width","Draft","Width of the beam").Width = profile[4]
        obj.addProperty("App::PropertyLength","Height","Draft","Height of the beam").Height = profile[5]
        obj.addProperty("App::PropertyLength","WebThickness","Draft","Thickness of the web").WebThickness = profile[6]
        obj.addProperty("App::PropertyLength","FlangeThickness","Draft","Thickness of the flanges").FlangeThickness = profile[7]
        _Profile.__init__(self,obj,profile)

    def execute(self,obj):
        pl = obj.Placement
        p1 = Vector(-obj.Width.Value/2,-obj.Height.Value/2,0)
        p2 = Vector(obj.Width.Value/2,-obj.Height.Value/2,0)
        p3 = Vector(obj.Width.Value/2,(-obj.Height.Value/2)+obj.FlangeThickness.Value,0)
        p4 = Vector(obj.WebThickness.Value/2,(-obj.Height.Value/2)+obj.FlangeThickness.Value,0)
        p5 = Vector(obj.WebThickness.Value/2,obj.Height.Value/2-obj.FlangeThickness.Value,0)
        p6 = Vector(obj.Width.Value/2,obj.Height.Value/2-obj.FlangeThickness.Value,0)
        p7 = Vector(obj.Width.Value/2,obj.Height.Value/2,0)
        p8 = Vector(-obj.Width.Value/2,obj.Height.Value/2,0)
        p9 = Vector(-obj.Width.Value/2,obj.Height.Value/2-obj.FlangeThickness.Value,0)
        p10 = Vector(-obj.WebThickness.Value/2,obj.Height.Value/2-obj.FlangeThickness.Value,0)
        p11 = Vector(-obj.WebThickness.Value/2,(-obj.Height.Value/2)+obj.FlangeThickness.Value,0)
        p12 = Vector(-obj.Width.Value/2,(-obj.Height.Value/2)+obj.FlangeThickness.Value,0)
        p = Part.makePolygon([p1,p2,p3,p4,p5,p6,p7,p8,p9,p10,p11,p12,p1])
        p = Part.Face(p)
        p.reverse()
        obj.Shape = p
        obj.Placement = pl

class _ProfileR(_Profile):
    '''A parametric rectangular beam profile based on [Width, Height]'''

    def __init__(self,obj, profile):
        obj.addProperty("App::PropertyLength","Width","Draft","Width of the beam").Width = profile[4]
        obj.addProperty("App::PropertyLength","Height","Draft","Height of the beam").Height = profile[5]
        _Profile.__init__(self,obj,profile)

    def execute(self,obj):
        pl = obj.Placement
        p1 = Vector(-obj.Width.Value/2,-obj.Height.Value/2,0)
        p2 = Vector(obj.Width.Value/2,-obj.Height.Value/2,0)
        p3 = Vector(obj.Width.Value/2,obj.Height.Value/2,0)
        p4 = Vector(-obj.Width.Value/2,obj.Height.Value/2,0)
        p = Part.makePolygon([p1,p2,p3,p4,p1])
        p = Part.Face(p)
        p.reverse()
        obj.Shape = p
        obj.Placement = pl

class _ProfileRH(_Profile):
    '''A parametric Rectangular hollow beam profile. Profile data: [width, height, thickness]'''

    def __init__(self,obj, profile):
        obj.addProperty("App::PropertyLength","Width","Draft","Width of the beam").Width = profile[4]
        obj.addProperty("App::PropertyLength","Height","Draft","Height of the beam").Height = profile[5]
        obj.addProperty("App::PropertyLength","Thickness","Draft","Thickness of the sides").Thickness = profile[6]
        _Profile.__init__(self,obj,profile)

    def execute(self,obj):
        pl = obj.Placement
        p1 = Vector(-obj.Width.Value/2,-obj.Height.Value/2,0)
        p2 = Vector(obj.Width.Value/2,-obj.Height.Value/2,0)
        p3 = Vector(obj.Width.Value/2,obj.Height.Value/2,0)
        p4 = Vector(-obj.Width.Value/2,obj.Height.Value/2,0)
        q1 = Vector(-obj.Width.Value/2+obj.Thickness.Value,-obj.Height.Value/2+obj.Thickness.Value,0)
        q2 = Vector(obj.Width.Value/2-obj.Thickness.Value,-obj.Height.Value/2+obj.Thickness.Value,0)
        q3 = Vector(obj.Width.Value/2-obj.Thickness.Value,obj.Height.Value/2-obj.Thickness.Value,0)
        q4 = Vector(-obj.Width.Value/2+obj.Thickness.Value,obj.Height.Value/2-obj.Thickness.Value,0)
        p = Part.makePolygon([p1,p2,p3,p4,p1])
        q = Part.makePolygon([q1,q2,q3,q4,q1])
        r = Part.Face([p,q])
        r.reverse()
        obj.Shape = r
        obj.Placement = pl
        
class _ProfileU(_Profile):
    '''A parametric H or I beam profile. Profile data: [width, height, web thickness, flange thickness] (see  http://en.wikipedia.org/wiki/I-beam forreference)'''

    def __init__(self,obj, profile):
        obj.addProperty("App::PropertyLength","Width","Draft","Width of the beam").Width = profile[4]
        obj.addProperty("App::PropertyLength","Height","Draft","Height of the beam").Height = profile[5]
        obj.addProperty("App::PropertyLength","WebThickness","Draft","Thickness of the webs").WebThickness = profile[6]
        obj.addProperty("App::PropertyLength","FlangeThickness","Draft","Thickness of the flange").FlangeThickness = profile[7]
        _Profile.__init__(self,obj,profile)

    def execute(self,obj):
        pl = obj.Placement
        p1 = Vector(-obj.Width.Value/2,-obj.Height.Value/2,0)
        p2 = Vector(obj.Width.Value/2,-obj.Height.Value/2,0)
        p3 = Vector(obj.Width.Value/2,obj.Height.Value/2,0)
        p4 = Vector(obj.Width.Value/2-obj.FlangeThickness.Value,obj.Height.Value/2,0)
        p5 = Vector(obj.Width.Value/2-obj.FlangeThickness.Value,obj.WebThickness.Value-obj.Height.Value/2,0)
        p6 = Vector(-obj.Width.Value/2+obj.FlangeThickness.Value,obj.WebThickness.Value-obj.Height.Value/2,0)
        p7 = Vector(-obj.Width.Value/2+obj.FlangeThickness.Value,obj.Height.Value/2,0)
        p8 = Vector(-obj.Width.Value/2,obj.Height.Value/2,0)
        p = Part.makePolygon([p1,p2,p3,p4,p5,p6,p7,p8,p1])
        p = Part.Face(p)
        p.reverse()
        obj.Shape = p
        obj.Placement = pl
        
