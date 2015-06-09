import MySQLdb
import MySQLdb.cursors
import csv

### Edit as necessary: user, password,and a workspace folder of your choice
my_wmflab_db_user = ''
my_wmflab_db_pass = ''
workspace = ''
log_file_name = workspace+'scripts/log__wiki__geo_tags.log'
log_file = open(log_file_name,"wt")#,encoding="UTF8")

languages = ["ab","ace","af","ak","als","am","ang","an","ar","arz","ast","as","av","ay","az","bar","bat_smg","ba","bcl","be_x_old","be","bg","bh","bm","bn","bo","bpy","br","bs","bxr","ca","cbk_zam","cdo","ceb","ce","chr","ckb","co","crh","csb","cs","cu","cv","cy","da","de","diq","dsb","dv","el","eml","en","eo","es","et","eu","ext","fa","fiu_vro","fi","fo","frp","frr","fr","fur","fy","gan","ga","gd","glk","gl","gn","got","gu","gv","hak","ha","haw","he","hif","hi","hr","hsb","ht","hu","hy","ia","id","ie","ig","ik","ilo","io","is","it","ja","jv","kaa","kab","ka","kbd","kk","kl","km","kn","koi","ko","krc","ksh","ks","ku","kv","kw","ky","lad","la","lb","lez","lg","lij","li","lmo","ln","lo","lt","lv","map_bms","mdf","mg","mhr","min","mi","mk","ml","mn","mrj","mr","ms","mt","mwl","myv","my","mzn","nah","nap","na","nds_nl","nds","ne","new","nl","nn","nov","no","nrm","nso","nv","oc","om","or","os","pam","pap","pa","pcd","pdc","pl","pms","pnb","pnt","ps","pt","qu","rm","rmy","roa_rup","roa_tara","ro","rue","ru","rw","sah","sa","scn","sco","sc","sd","se","sh","simple","si","sk","sl","sn","so","sq","sr","stq","st","su","sv","sw","szl","ta","tet","te","tg","th","tk","tl","tpi","tr","ts","tt","tyv","ty","udm","ug","uk","ur","uz","vec","vep","vi","vls","vo","war","wa","wo","wuu","xh","yi","yo","zea","zh_classical","zh_min_nan","zh_yue","zh","zu"]
### Testing set ###
#languages = ["ab","it"]


for language in languages:
	print
	print "#-------------------------------------#"
	
	language_db_host = "%swiki.labsdb"%(language)
	language_database = "%swiki_p"%(language)
	print language_db_host
	log_file.write(language_db_host+"\n"+language_database+"\n")
	
	output_file_name = workspace+'wiki_geo_data/wiki_%s__geo_tags__info__edits.tsv'%(language)
	output_file = open(output_file_name,"wt")#,encoding="UTF8")
	print output_file_name
	log_file.write(output_file_name+"\n")
	
	try:
		#cnx = MySQLdb.connect(host=language_db_host, database=language_database, read_default_file='~/replica.my.cnf')
		cnx = MySQLdb.connect(
			host = language_db_host, 
			user = my_wmflab_db_user, 
			passwd = my_wmflab_db_pass, 
			db = language_database,
			#cursorclass = MySQLdb.cursors.DictCursor
			)
		cursor = cnx.cursor()
		
		query = """
		select 
		geo_tags.gt_id as geo_tag_id,
		
		geo_tags.gt_page_id as page_id__geo,
		page_info.page_id as page_id_pag,
		
		
		page_info.page_title,
		page_info.page_namespace,
		page_info.page_len,
		page_info.last_edit_timestamp,
		
		edits_history.edits,
		minor_edits_history.minor_edits,
		
		geo_tags.gt_primary,
		geo_tags.gt_lat,
		geo_tags.gt_lon,
		geo_tags.gt_country,
		geo_tags.gt_region
		
		from geo_tags 
		
		left join (
			select 
			page.page_id,
			page.page_title,
			page.page_len,
			page.page_namespace,
			revision.rev_timestamp as last_edit_timestamp
			from page 
			left join revision 
			on page.page_latest=revision.rev_id
			) as page_info
		on geo_tags.gt_page_id = page_info.page_id
		
		left join (
			select 
			rev_page, 
			count(rev_id) as edits 
			from revision 
			where rev_minor_edit=0
			group by rev_page
			) as edits_history
		on geo_tags.gt_page_id = edits_history.rev_page
		
		left join (
			select 
			rev_page, 
			count(rev_id) as minor_edits
			from revision 
			where rev_minor_edit=1
			group by rev_page
			) as minor_edits_history
		on geo_tags.gt_page_id = minor_edits_history.rev_page
		;
		"""
		log_file.write(query+"\n")
		
		cursor.execute(query)
		
		c = csv.writer(output_file, delimiter="\t", quoting=csv.QUOTE_NONNUMERIC)
		
		rows=cursor.fetchall()
		print "Number of rows:", str(len(rows))
		
		print cursor.description
		
		field_names = []
		page_id_index = None
		for descriptor in cursor.description:
			if descriptor[0] == "page_id__geo":
				page_id_index = cursor.description.index(descriptor)
				print "Index of geo_tag_id is", page_id_index
				log_file.write("Index of geo_tag_id is"+str(page_id_index)+"\n")
			field_names.append(descriptor[0])
		
		field_names.append("first_edit_page_id")
		field_names.append("first_edit_rev_id")
		field_names.append("first_edit_timestamp")
		field_names.append("language")
		
		c.writerow(field_names)
		
		for row in rows:
			
			geo_tag_id = row[page_id_index]
			
			first_edit_query = """
			select 
			revision_history.rev_page as first_edit_page_id,
			revision_history.rev_id as first_edit_rev_id,
			revision_history.rev_timestamp as first_edit_timestamp
			from 
				(
				select 
				min(rev_id) as min_rev_id  
				from revision
				where rev_page=%s
				) as min_rev
			left join 
			revision as revision_history
			on min_rev.min_rev_id=revision_history.rev_id
			"""%(geo_tag_id)
			#log_file.write(first_edit_query+"\n")
			
			cursor.execute(first_edit_query)
			first_edit_row = cursor.fetchone()
			
			if first_edit_row==None:
				row += (None,None,None,)
			else:	
				# 0 revision_history.rev_page as first_edit_page_id,
				# 1 revision_history.rev_id as first_edit_rev_id,
				# 2 revision_history.rev_timestamp as first_edit_timestamp
				row += (first_edit_row[0],)
				row += (first_edit_row[1],)
				row += (first_edit_row[2],)
			
			#print row
			row += (language,)
			c.writerow(row)
			
		output_file.close()
		log_file.write(str(len(rows))+" written.\n\n")
		print ""
		
		cursor.close()
		#cnx.close()
		
	except MySQLdb.Error, e:
		log_file.write("Error %d: %s \n\n" % (e.args[0],e.args[1]))
		print "Error %d: %s" % (e.args[0],e.args[1])
		
	finally:
		if cnx:
			cnx.close()
	
log_file.close()