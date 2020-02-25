global lvops

plugin Helper AvalonSetHelper
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
	
	rollout avapam_rut "avalonn parameters"
	(
		CheckBox ckb_active "Enabled"
		group "avalon sets"
		(
			Label lbl1 "ID: " across:2 align:#right
			EditText edt_id "" enabled:off
			Label lbl2 "Family: " across:2 align:#right
			EditText edt_family "" enabled:off
			Label lbl3 "Asset: " across:2 align:#right
			EditText edt_asset "" enabled:off		
			Label lbl4 "Subset: " across:2 align:#right
			EditText edt_subset "" enabled:off		
		)
	)
	
	rollout obj_lst_rut "object list"
	(
		local owner = if owner != undefined do owner
		local inPickMode = false
		checkbutton ckb_add	"Add..."	width:50 height:24	align:#left offset:[-11, 0] across:3
		button		btn_add	"Add"		width:50 align:#center offset:[0, 0]
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
		
		function removeSelMembers =  --fixed
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
					)
				)
				updateList()
			)
		)
		
		function pickFilter obj = 
		(
			pickable = obj.baseObject != this
		)
		
		function PickMultiple = --no fix needed
		(
			while ((obj = (pickObject message:"Please Select Object" count:1 filter:pickFilter forceListenerFocus:false)); isValidNode obj) do
			(
				undo "select object" on
				(				
					-- print obj.name
					append avalon_nodes obj
				)
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

		on obj_lst_rut open do --no change needed
		(	
			initListView()
			updateList()
		)
	)
		
	on create do
	(
		print this
		-- print ("on create " + (create as string))
		-- count += 1
		obj_lst_rut.owner = this
		--this[4][1].cross = off
		--this[4][1].centermarker = on
		--this[4][1].axistripod = off
		--this[4][1].box = off
		
	)

)