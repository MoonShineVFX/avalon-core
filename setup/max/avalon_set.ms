global lvops

plugin Helper AvalonSet
name: "Avalon Set"
classID:#(0x28ed0e6, 0x62e37c5b)
category:"Avalon"
replaceUI:True
version:1
extends:Point
(
	local count = 1
	parameters pblok1 rollout:avapam_rut
	(
		ava_id type:#string default:"None" ui:edt_id
		family type:#string default:"None" ui:edt_family
		asset type:#string default:"None" ui:edt_asset
		subset type:#string default:"None" ui:edt_subset
		active type:#boolean default:on ui:ckb_active
	)

	parameters pblok2
	(
		avalon_nodes type:#nodeTab tabSize:0 tabSizeVariable:true
	)
	
	rollout avapam_rut "avalonn sets"
	(
		CheckBox ckb_active "Enabled"
		group "avalon sets"
		(
			Label lbl1 "ID" align:#left
			EditText edt_id "" align:#left offset:[-6, 0] enabled:off
			Label lbl2 "Family" align:#left
			EditText edt_family "" align:#left offset:[-6, 0] enabled:off
			Label lbl3 "Asset" align:#left
			EditText edt_asset "" align:#left offset:[-6, 0] enabled:off		
			Label lbl4 "Subset" align:#left
			EditText edt_subset "" align:#left offset:[-6, 0] enabled:off		
		)
	)
	
	rollout obj_lst_rut "object list"
	(
		local owner = if owner != undefined do owner
		local CharMenu --RCMenu
		local inPickMode = false
		checkbutton ckb_add	"Pick"	width:50 height:24	align:#left offset:[-11, 0] across:3
		button		btn_add	"Add..."		width:50 align:#center offset:[0, 0]
		button 		btn_Remove	"Remove"	width:50 align:#right  offset:[11, 0]		
		dotNetControl  nodes_lv "ListView"	width:160 height:620	align:#center offset:[0,0]
		
		fn UpdateUI = 
		(
			ckb_add.state = inPickMode
		)
		
		fn initListView =
		(
			lvops.InitListView nodes_lv pCheckBoxes:true
			lvops.AddLvColumnHeader nodes_lv pCaption: "Avalon Sets" pWidth:(obj_lst_rut.Width - 10)
			lvops.refreshListView nodes_lv
			
			CharMenu = rcmenu CharacterMenu
			(
				menuItem mi_remove "Remove"
				on mi_remove picked do ( obj_lst_rut.executeAction #remove )
			)
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
			UpdateUI()
		)
		
		fn removeSelMembers =  --fixed
		(
			local selectedLVItems = lvops.GetLvSelection nodes_lv
			undo "remove_objects" on
			(
				for li in selectedLVItems where li.selected do
				(	
					local obj = undefined
					if (li.tag != undefined and li.tag.value != undefined) do
					(
						obj = li.tag.value
						idx = findItem avalon_nodes obj
						if idx !=0 do deleteItem avalon_nodes idx
					)
				)
				updateList()
			)
		)		
		
		fn pickFilter obj = 
		(
			local pickable = (obj.baseObject != this) and ((findItem avalon_nodes obj) == 0) and ((classof obj) != AvalonSetHelper)
		)
		
		function PickMultiple = --no fix needed
		(
			while ((obj = (pickObject message:"Please Select Object" count:1 filter:pickFilter forceListenerFocus:false)); isValidNode obj) do
			(
				undo "select object" on
				(
					append avalon_nodes obj
				)
				updateList()
			)
		)
		
		on ckb_add changed stat do --no fix needed
		(
			if (true == stat ) then 
			(
				inPickMode = true
				
				PickMultiple()
				
				inPickMode = false
				ckb_add.checked = false
			)
			else 
			(
				-- When the user clicks on the Add button to turn it off,
				-- terminate the current pickObejct mode
				toolmode.CommandMode = #select
			)
		)
		
		on btn_Add pressed do
		(
			title_s = ("Select " + subset + " Objects")
			objs = selectByName title:title_s filter:pickFilter
			if objs != undefined do
			(
				for obj in objs do append avalon_nodes obj
			)
			updateList()
		)
		
		on btn_Remove pressed do
		(
			removeSelMembers()
		)
		
		on obj_lst_rut open do --no change needed
		(	
			initListView()
			updateList()
		)
	)
		
	on create do
	(
		obj_lst_rut.owner = this
	)
)
