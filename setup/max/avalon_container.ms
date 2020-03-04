Global lvops

plugin Helper AvalonContainer
name: "Avalon Constiner"
classID:#(0x7b75cb7b, 0x43caa938)
category:"Avalon"
replaceUI:True
version:1
extends:Point
(
	parameters pblok1 rollout:avaconpam_rut
	(		
		schema type:#string default:"avalon-core:container-2.0" ui:edt_schma
		ava_name type:#string default:"None" ui:edt_name
		loader type:#string default:"None" ui:edt_loader
		object_name type:#string default:"None" ui:edt_objectName
		namespace type:#string default:"None" ui:edt_namespace
		representation type:#string default:"None" ui:edt_representation
		avalon_nodes type:#nodeTab tabSize:0 tabSizeVariable:true
	)
	
	rollout avaconpam_rut "avalon container"
	(
		group "avalon Parameters"
		(
			label lbl1 "Schema" align:#left 
			edittext edt_schma width:140 align:#left offset:[-6,0] enabled:False
			label lbl2 "Loader" align:#left			
			edittext edt_loader width:140 align:#left offset:[-6,0] enabled:False
			label lbl3 "ObjectName" align:#left			
			edittext edt_objectName width:140 align:#left offset:[-6,0] enabled:False
			label lbl4 "Name" align:#left
			edittext edt_name width:140 align:#left offset:[-6,0] enabled:False
			label lbl5 "Namespace" align:#left
			edittext edt_namespace width:140 align:#left offset:[-6,0] enabled:False
			label lbl6 "Representation" align:#left
			edittext edt_representation width:140 align:#left offset:[-6,0] enabled:False
		)
	)
	
	rollout obj_lst_rut "object list"
	(
		dotNetControl  nodes_lv "ListView"	width:160 height:620	align:#center offset:[0,0]
		
		fn initListView =
		(
			lvops.InitListView nodes_lv pCheckBoxes:False
			lvops.AddLvColumnHeader nodes_lv pCaption: "Avalon Container" pWidth:(obj_lst_rut.Width - 10)
			lvops.refreshListView nodes_lv
		)
		
		fn updateList = 
		(
			nodes = #()
			lvops.ClearLvItems nodes_lv
			local LVAdd = lvops.AddLvItem
			for obj in avalon_nodes do
			(
				LVAdd nodes_lv pTextItems: #(obj.name) pTag: (dotNetMXSValue obj)
			)
			lvops.SelectLvItem nodes_lv 0
		)

		on obj_lst_rut open do
		(
			initListView()
			updateList()
		)
	)
)