# -*- coding: utf-8 -*-
# Pass groups from objects script
# Autor: Lucio Gomez (psicofil@gmail.com)
# Creation Date: 28/10/2025
# Version: 28/10/2025

# Import the necessary
import salome
import  SMESH, SALOMEDS
from salome.smesh import smeshBuilder
from qtsalome import QMessageBox
mesh = []

try:
    smesh = smeshBuilder.New()
    # smesh.SetEnablePublish( False )
    selected=salome.sg.getSelected(0)
    selobjID=salome.myStudy.FindObjectID(selected)
    mesh=smesh.Mesh(selobjID.GetObject())
except:
    QMessageBox.critical(None,'Error',"Select a Mesh First",QMessageBox.Abort)


if mesh:
    aCriteria = []
    aCriterion = smesh.GetCriterion(SMESH.NODE,SMESH.FT_FreeNodes,SMESH.FT_Undefined,0)
    aCriteria.append(aCriterion)
    aFilter_1 = smesh.GetFilterFromCriteria(aCriteria)
    aFilter_1.SetMesh(mesh.GetMesh())
    Free_Nodes = mesh.GroupOnFilter( SMESH.NODE, 'Free_Nodes', aFilter_1 )
    a0D_FreeNodes = mesh.Add0DElementsToAllNodes(Free_Nodes, '0D_FreeNodes' )
    mesh.RemoveGroup(Free_Nodes)
    ## Set names of Mesh objects
    smesh.SetName(a0D_FreeNodes, '0D_FreeNodes')
    ## Create Mesh Geometry Groups
    # try:
    #     shape=mesh.GetShape()
    #     import GEOM
    #     from salome.geom import geomBuilder
    #     geompy = geomBuilder.New()
    #     groups_source = geompy.GetGroups(shape)
    #     for group in groups_source:
    #         if str(group.GetMaxShapeType()) == 'VERTEX':
    #             if len(mesh.GetGroupByName(group.GetName())) == 0:
    #                 obj_group = mesh.GroupOnGeom(group,group.GetName(),SMESH.ELEM0D)
    #                 smesh.SetName(obj_group, group.GetName())
    #             else:
    #                 if str(mesh.GetGroupByName(group.GetName())[0].GetType()) != 'ELEM0D':
    #                     obj_group = mesh.GroupOnGeom(group,group.GetName(),SMESH.ELEM0D)
    #                     smesh.SetName(obj_group, group.GetName())
    # except:
    #     None

if salome.sg.hasDesktop():
  salome.sg.updateObjBrowser()



