#! /usr/bin/python

# A test script to make sure all the modules work

#Basic setup for logging
import sys
import os
import logging
import unittest
sys.path.append( os.path.abspath('../mlox/') )
logging.basicConfig(level=logging.INFO)

term_color ={
    'red': '\x1b[0;30;41m',
    'clear': '\x1b[0m'
}

#File Finder
class fileFinder_test(unittest.TestCase):
    def test_file_names(self):
        import modules.fileFinder as fileFinder
        file_names = fileFinder.caseless_filenames()
        #TODO:  Actually test this

    def test_dir_list(self):
        import modules.fileFinder as fileFinder
        dir_list = fileFinder.caseless_dirlist()
        self.assertTrue(isinstance(fileFinder.caseless_dirlist(dir_list),fileFinder.caseless_dirlist))     #Make sure copy constructor works
        self.assertEqual(dir_list.dirpath(),os.path.abspath('.'))
        self.assertEqual(dir_list.find_file("module_TEST.PY"),'module_test.py')
        self.assertEqual(dir_list.find_path("module_TEST.PY"),os.path.abspath('.')+'/module_test.py')
        self.assertEqual(dir_list.find_parent_dir("reaDme.mD").dirpath(),os.path.abspath('..'))

        #Multi-line check here
        (a,b,c) = fileFinder.find_game_dirs()
        self.assertTrue(a == None)
        self.assertTrue(b == None)
        self.assertEqual(c.dirpath(),os.path.abspath('..'))

        #TODO:  Actually test these two (seperately)
        #print fileFinder.filter_dup_files(dir_list.filelist())

#Config Handler
class configHandler_test(unittest.TestCase):
    import modules.configHandler as configHandler
    zinx_txt=['Better Heads Bloodmoon addon.esm', 'Better Heads Tribunal addon.esm', 'Better Heads.esm', 'Bloodmoon.esm', 'MCA.esm', 'Morrowind.esm', 'Tribunal.esm', 'ACE_Subtitles.esp', 'Balmora Expansion - LITE 1.0.esp', 'Balmora Expansion v1.4.esp', 'BAR_DarkshroudKeep_v1.2.esp', 'Beasts of Burden Necromancer.esp', 'Better Bodies.esp', 'Better Clothes_v1.0_nac.esp', 'BE_dh_furn_stores .esp', 'BE_Personal_Fix.esp', 'Blasphemous Revenants.esp', 'BR Dead Heros.esp', 'Dark_Stone_Fortress.esp', 'Flee AI Tweaks.esp', 'IceNioLivRobeReplacerALL.esp', 'Illuminated Order v1.0 - Bloodmoon Compatibility Extras.esp', 'Illuminated Order v1.0.esp', 'indybank.esp', 'Level List Merger.esp', 'MCA - Guards Patch.esp', 'MCA - Personal Fix.esp', 'MCA - Vampire Realism Patch.esp', 'MTT Vol III.esp', 'MWE_Base.esp', 'MWE_Combat.esp', 'MWE_Writing.esp', 'Necro Armor v1_0.esp', 'Propylon Fix.esp', 'Quest Fix.esp', 'Scripted_Spells.esp', 'Slave Trade.esp', "Slof's BB neck fix.esp", "Slof's Better Beasts b.esp", 'Vampire Realism II - BM Add-On.esp', 'Vampire Realism II - TB Add-On.esp', 'Vampire Realism II - VE Patch.esp', 'Vampire Realism II.esp', 'Vampire_Embrace.esp', 'Vampire_Werewolf.esp', "Wakim's Game Improvement 9.esp", 'werewolfrealism-moononly.esp', 'Werewolf_Evolution.esp']
    test1_plugins=[
    'Morrowind.esm', 'RF - Furniture shop.esm', 'Book Rotate.esm', 'GDR_MasterFile.esm',
    'MetalQueenBoutique.esm', 'The Undead.esm', 'Morrowind Patch v1.6.4 (WIP).esm',
    'Tribunal.esm', 'Bloodmoon.esm', 'BT_Whitewolf_2_0.esm', 'TR_Data.esm', 'TR_Map1.esm', 'ARJAN_A_Lords_Men_v2.0.esp', 'Adsens_Piercings-jms_patch.esp', 'Adsens_Piercings.esp', 'Better Bodies.esp', 'KeyNamer.esp', 'All Boat Ports.esp', 'RealSignposts.esp', 'All Silt Strider Ports.esp', 'Silt_Striders_Are_In_Vvardenfell.esp', 'Tribun_Laura_3_0.esp', 'BB_Clothiers_of_Vvardenfell_v1.1.esp', 'BM_S_Inn.esp',
    'BT_WWLokpatch1.esp', 'BT_Whitewolf_2_0-jms_patch.esp', 'BUUG Alchemy- Bloodmoon.esp', 'BUUG Alchemy- Srikandi.esp', 'BUUG Alchemy- Tribunal.esp', 'Barons_Partners30.esp', 'Better Clothes_v1.1_nac.esp', 'BetterClothes_Patch.esp', 'Book Jackets - Morrowind - BookRotate.esp', 'Book Rotate - Bloodmoon v5.3.esp', 'Book Rotate - Morrowind v1.1.esp', 'Book Rotate - Tribunal v5.3.esp', 'Brittlewind fix.esp', "Building Up Uvirith's Grave 1.1.esp", 'Chalk30-Base.esp', 'CharGen Revamped delay2.esp', 'CharGen_Revamped_v14.esp',
    'ChessV4.esp', 'Clean Sexy_Black_Collar_Dress_v.1a.esp', 'Clean Tales of Seyda Neen.esp', 'Clean Tales of Tel Branora.esp', 'Clean Tales of the Bitter Coast.esp', 'Creatures.esp', 'CreaturesX-jms_patch.esp', 'DM_DB Armor Replacer.esp', 'DN-GDRv1-jms_patch.esp', 'DN-GDRv1.esp', 'DX_CreatureAdditionsV1.0.esp', 'DagonFel_Well.esp', 'Drug Realism.esp', 'Expanded Sounds.esp',
    'GCD Restore Potions Fix.esp', 'GCD StartScript for Trib or Bloodmoon.esp', 'GCD better balanced birthsigns.esp', 'GCD_107x_to_108_patch.esp', 'GCD_SS_patch.esp', 'GCD_VH_patch2.esp', 'GCD_WE_patch.esp', 'Galsiahs Character Development.esp', 'Gothic Attire Complete v1-1.esp', 'IceNioLivRobeReplacerALL.esp', 'JMS-ring_of_mojo.esp', 'JMS-shishi_door_fix.esp',
    'JMS-springheel_boots.esp', "Juniper's Twin Lamps (1.1 Tribunal).esp", 'K_Potion_Upgrade_1.2.esp', 'LGNPC_AldVelothi_v1_20.esp', 'LGNPC_Aldruhn_v1_13-jms_patch.esp', 'LGNPC_Aldruhn_v1_13.esp', 'LGNPC_GnaarMok_v1_10.esp', 'LGNPC_HlaOad_v1_32.esp', 'LGNPC_Indarys_Manor_v1_45.esp', 'LGNPC_Khuul_v2_01.esp', 'LGNPC_MaarGan_v1_10.esp', 'LGNPC_NoLore_v0_83.esp', 'LGNPC_PaxRedoran_v1_11-jms_patch.esp', 'LGNPC_PaxRedoran_v1_11.esp', 'LGNPC_Pelagiad_v1_13.esp', 'LGNPC_Secret_Masters_v1_21.esp',
    'LGNPC_TelMora_v1_11.esp', 'LGNPC_TelUvirith_v1_10.esp', 'LGNPC_VivecFQ_v2_03.esp', 'LGNPC_VivecRedoran_v1_40.esp', 'Lgnpc_SN.esp', 'MTT_IV_Master.esp', 'Mashed Lists.esp', 'Morrowind-jms_patch.esp', 'MultiMark-jms_patch.esp', 'MultiMark.esp', 'MultiMark_BloodmoonPlugin.esp', 'MultiMark_FiremothPlugin.esp', 'MultiMark_TribunalPlugin.esp',
    'Myth and Murder ver 2.0.esp', 'NEDE WGI patch.esp', 'NEDE v1.2.esp', "NG_New_Carnithus'_Armamentarium.esp", 'New Argonian Bodies - Mature.esp', 'New Khajiit Bodies - Mature.esp', 'Nixie.esp', 'Nudity Greeting Expansion V1.esp', 'OfficialMods_v5.esp', 'P.R.E. v4.0.esp', 'RF - Bethesda Furniture.esp', 'RKWerewolf.esp', 'RTS_FaeriesSeydaNeen.esp', 'RTS_HealingFaeries.esp', 'SSlave_Companions.esp',
    'Scripted_Spells.esp', 'Secrets of Vvardenfell.esp', "Slof's Goth Shop II.esp", "Slof's Pillow Book.esp", "Slof's Vampire Faces.esp", 'Smooth Moves v1.esp', 'Sri Alchemy BM List Patch.esp', 'Sris_Alchemy_BM.esp', 'Suran_Underworld_2.5-jms_patch.esp', 'Suran_Underworld_2.5.esp', 'Syc_Herbalism ES Patch.esp', 'Syc_HerbalismforPurists-jms_patch.esp', 'Syc_HerbalismforPurists.esp', 'Syc_HerbalismforPurists_BM.esp', 'Syc_HerbalismforPurists_TB.esp', 'TLM - Ambient Light + Fog Update.esp', 'TLM - Light Sources (Clearer Lighting).esp', 'TLM - Light Sources (Lanterns).esp', 'TLM - Light Sources (Natural Water).esp', 'TLM - NPC Light Sources.esp', 'TR_Map1-jms_patch.esp', 'Text Patch for Morrowind with Tribunal & Bloodmoon.esp',
    'TheUberCrystalEggHunt.esp', 'The_Vvardenfell_Libraries.esp', 'Tribunal-jms_patch.esp', 'UUMPP Bloated Morrowind Patch v1.6.4.esp', 'Unboarable Rieklings.esp', 'Vampire Realism II - BL Patch.esp', 'Vampire Realism II - BM Add-On.esp', 'Vampire Realism II - TB Add-On.esp', 'Vampire Realism II - VE Patch.esp', 'Vampire Realism II.esp', 'Vampire_Embrace-jms_combat_bite_patch-2.esp', 'Vampire_Embrace-jms_combat_bite_patch.esp', 'Vampire_Embrace-jms_follow_patch.esp', 'Vampire_Embrace-jms_patch.esp',
    'Vampire_Embrace.esp', 'Vampire_Werewolf.esp', 'Vampiric Hunger - SU.esp', 'Vampiric Hunger Base.esp', 'Vampiric Hunger Extended.esp', "Wakim's Game Improvement 9.esp", 'Werewolf_Evolution.esp', 'Windows Glow.esp', "Zyndaar's Bows.esp", 'abotWhereAreAllBirdsGoing.esp', 'dh_furn-jms_patch.esp', 'dh_furn.esp', 'dh_furn_stores.esp', 'dh_thriftshop-jms_patch.esp', 'dh_thriftshop.esp', 'moons_soulgems.esp', 'pk_TatyShirt.esp', 'DwemerClock.esp']
    modified_plugins = test1_plugins
    modified_plugins[163] = 'DwemerClock.esp'
    modified_plugins[164] = 'pk_TatyShirt.esp'

    #Can't use the logging check with python 2.7...
    def test_No_File(self):
        #with self.assertLogs('mlox.configHandler',level='Error') as l:
        handleri = self.configHandler.configHandler("No File")
        self.assertEqual(handleri.read(),[])
        #self.assertEqual(l.output, ['ERROR:mlox.configHandler:Unable to open config file: No File'])

    def test_Morrowind(self):
        self.assertEqual(self.configHandler.configHandler("./userfiles/zinx.txt","Morrowind").read(),self.zinx_txt)

    #Can't use the logging check with python 2.7...
    def test_Invalid(self):
        #with self.assertLogs('mlox.configHandler',level='Error') as l:
        self.assertEqual(self.configHandler.configHandler("./userfiles/zinx.txt","Invalid").read(),self.zinx_txt)
        #self.assertEqual(l.output, ['WARNING:mlox.configHandler:"Invalid" is not a recognized file type!'])

    def test_Default(self):
        self.assertEqual(self.configHandler.configHandler("./userfiles/zinx.txt").read(),self.zinx_txt)

    def test_Oblivion(self):
        #TODO: Actually test this one (Using an oblivion file)
        #print self.configHandler.configHandler("./userfiles/zinx.txt","Oblivion").read()
        pass

    def test_dirHandler(self):
        """read, check, modify, check modifications, then restore to original)"""
        dirHandler = self.configHandler.dataDirHandler("./test1.data/")
        self.assertEqual(dirHandler.read(),self.test1_plugins)
        dirHandler.write(self.modified_plugins)
        self.assertEqual(dirHandler.read(),self.modified_plugins)
        dirHandler.write(self.test1_plugins)

#Parser, and pluggraph
class parser_pluggraph_test(unittest.TestCase):
    import modules.ruleParser as ruleParser
    import modules.pluggraph as pluggraph
    import modules.fileFinder as fileFinder
    file_names = fileFinder.caseless_filenames()
    test1_graph=['morrowind.esm', 'tribunal.esm', 'bloodmoon.esm', 'morrowind patch v1.6.4 (wip).esm', 'rf - furniture shop.esm', 'metalqueenboutique.esm', 'book rotate.esm', 'gdr_masterfile.esm', 'bt_whitewolf_2_0.esm', 'tr_data.esm', 'tr_map1.esm', 'the undead.esm', 'text patch for morrowind with tribunal & bloodmoon.esp', 'lgnpc_sn.esp', 'realsignposts.esp', 'dagonfel_well.esp', 'myth and murder ver 2.0.esp', "wakim's game improvement 9.esp", 'chessv4.esp', 'lgnpc_nolore_v0_83.esp', 'officialmods_v5.esp', "zyndaar's bows.esp", 'dwemerclock.esp', 'uumpp bloated morrowind patch v1.6.4.esp', 'tlm - light sources (natural water).esp', 'tlm - ambient light + fog update.esp', 'tlm - npc light sources.esp', 'dh_furn.esp', 'dh_furn_stores.esp', 'dh_thriftshop.esp', 'tlm - light sources (lanterns).esp', 'tlm - light sources (clearer lighting).esp', 'p.r.e. v4.0.esp', 'nudity greeting expansion v1.esp', 'book rotate - morrowind v1.1.esp', 'rf - bethesda furniture.esp', 'better bodies.esp', 'silt_striders_are_in_vvardenfell.esp', 'werewolf_evolution.esp', 'rkwerewolf.esp',
    'vampire_werewolf.esp', 'windows glow.esp', 'unboarable rieklings.esp', 'bm_s_inn.esp', 'smooth moves v1.esp', "slof's vampire faces.esp", 'vampire realism ii.esp', 'vampire realism ii - tb add-on.esp', 'vampire realism ii - bm add-on.esp', 'vampire realism ii - ve patch.esp', 'vampire realism ii - bl patch.esp', 'abotwhereareallbirdsgoing.esp', "ng_new_carnithus'_armamentarium.esp", 'scripted_spells.esp', 'nixie.esp', 'book rotate - tribunal v5.3.esp', 'book rotate - bloodmoon v5.3.esp', 'clean sexy_black_collar_dress_v.1a.esp', 'keynamer.esp', 'tribun_laura_3_0.esp', 'galsiahs character development.esp', 'gcd startscript for trib or bloodmoon.esp', 'gcd better balanced birthsigns.esp', 'gcd restore potions fix.esp', 'gcd_ss_patch.esp', 'brittlewind fix.esp', 'gcd_we_patch.esp', 'drug realism.esp', "juniper's twin lamps (1.1 tribunal).esp", 'gcd_107x_to_108_patch.esp', 'vampire_embrace.esp', 'sslave_companions.esp', 'bt_wwlokpatch1.esp', 'vampiric hunger base.esp', 'vampiric hunger extended.esp', 'vampiric hunger - su.esp', 'gcd_vh_patch2.esp', 'arjan_a_lords_men_v2.0.esp', 'book jackets - morrowind - bookrotate.esp', 'dm_db armor replacer.esp', "slof's goth shop ii.esp", 'bb_clothiers_of_vvardenfell_v1.1.esp', 'expanded sounds.esp', 'iceniolivrobereplacerall.esp', 'barons_partners30.esp', "slof's pillow book.esp", 'theubercrystalegghunt.esp',
    'better clothes_v1.1_nac.esp', 'clean tales of seyda neen.esp', 'lgnpc_indarys_manor_v1_45.esp', 'new argonian bodies - mature.esp', 'lgnpc_gnaarmok_v1_10.esp', 'lgnpc_aldvelothi_v1_20.esp', 'lgnpc_maargan_v1_10.esp', 'new khajiit bodies - mature.esp', 'lgnpc_secret_masters_v1_21.esp', 'gothic attire complete v1-1.esp', "building up uvirith's grave 1.1.esp", 'secrets of vvardenfell.esp', 'the_vvardenfell_libraries.esp', 'lgnpc_hlaoad_v1_32.esp', 'nede v1.2.esp', 'nede wgi patch.esp', 'rts_faeriesseydaneen.esp', 'rts_healingfaeries.esp', 'sris_alchemy_bm.esp', 'sri alchemy bm list patch.esp', 'creatures.esp', 'creaturesx-jms_patch.esp', 'dn-gdrv1.esp', 'syc_herbalismforpurists.esp', 'syc_herbalismforpurists_bm.esp', 'syc_herbalismforpurists_tb.esp', 'syc_herbalism es patch.esp', 'multimark.esp', 'multimark_firemothplugin.esp', 'multimark_tribunalplugin.esp', 'multimark_bloodmoonplugin.esp', 'multimark-jms_patch.esp', 'all silt strider ports.esp', 'all boat ports.esp', 'vampire_embrace-jms_patch.esp', 'dh_thriftshop-jms_patch.esp', 'k_potion_upgrade_1.2.esp', 'vampire_embrace-jms_combat_bite_patch.esp', 'syc_herbalismforpurists-jms_patch.esp', 'jms-shishi_door_fix.esp', 'moons_soulgems.esp', 'suran_underworld_2.5.esp', 'lgnpc_aldruhn_v1_13.esp', 'suran_underworld_2.5-jms_patch.esp', 'bt_whitewolf_2_0-jms_patch.esp', 'lgnpc_pelagiad_v1_13.esp', 'lgnpc_telmora_v1_11.esp', 'chargen_revamped_v14.esp', 'chargen revamped delay2.esp', 'lgnpc_khuul_v2_01.esp', 'lgnpc_vivecfq_v2_03.esp', 'tribunal-jms_patch.esp', 'lgnpc_teluvirith_v1_10.esp', 'lgnpc_vivecredoran_v1_40.esp', 'lgnpc_paxredoran_v1_11.esp', 'dx_creatureadditionsv1.0.esp', 'betterclothes_patch.esp', 'buug alchemy- bloodmoon.esp', 'buug alchemy- srikandi.esp', 'buug alchemy- tribunal.esp', 'pk_tatyshirt.esp', 'clean tales of the bitter coast.esp', 'clean tales of tel branora.esp', 'tr_map1-jms_patch.esp', 'chalk30-base.esp', 'dh_furn-jms_patch.esp', 'mtt_iv_master.esp', 'jms-springheel_boots.esp', 'morrowind-jms_patch.esp', 'dn-gdrv1-jms_patch.esp', 'lgnpc_paxredoran_v1_11-jms_patch.esp', 'vampire_embrace-jms_follow_patch.esp', 'jms-ring_of_mojo.esp', 'vampire_embrace-jms_combat_bite_patch-2.esp', 'lgnpc_aldruhn_v1_13-jms_patch.esp', 'mashed lists.esp']

    def test_parser_graph(self):
        graph = self.pluggraph.pluggraph()
        myParser = self.ruleParser.rule_parser([],graph,"./test1.data/",sys.stdout,self.file_names)
        myParser.read_rules("./test1.data/mlox_base.txt")
        self.assertEqual(graph.topo_sort(),self.test1_graph)

    #TODO:  d_ver doesn't seem correct
    def test_version(self):
        #Multi-line check here
        (f_ver,d_ver) = self.ruleParser.get_version("BB_Clothiers_of_Vvardenfell_v1.1.esp","./test1.data/")
        self.assertEqual(f_ver,'00001.00001.00000._')
        self.assertEqual(d_ver,None)

#Load order
#TODO: Actually test anything here
class loadOrder_test(unittest.TestCase):
    from modules.loadOrder import loadorder
    import modules.fileFinder as fileFinder

    def test_File_and_Dir(self):
        l1 = self.loadorder()
        l1.datadir = self.fileFinder.caseless_dirlist("./test1.data/")
        l1.plugin_file = "./userfiles/abot.txt"
        l1.game_type = None
        l1.get_active_plugins()
        l1.update()
        print l1.listversions()

    def test_Dir(self):
        l2 = self.loadorder()
        l2.datadir = self.fileFinder.caseless_dirlist("./test1.data/")
        l2.get_data_files()
        l2.update()

    def test_File(self):
        l3 = self.loadorder()
        l3.read_from_file("./userfiles/abot.txt")
        l3.update()
        print l3.explain("Morrowind.esm")
        print l3.explain("Morrowind.esm",True)

#Version
class version_test(unittest.TestCase):
    import modules.version as version

    def test_internal_version(self):
        self.assertEqual(self.version.Version,'0.61')

    def test_version_string(self):
        self.assertRegexpMatches(self.version.version_info(),' \d*\.\d* \[mlox-base 20\d\d-\d\d-\d\d \d\d:\d\d:\d\d \(UTC\)] \(en_US/UTF-8\)\\nPython Version: \d\.\d\\nwxPython Version: \d\.\d\.\d\.\d\\n')

#Updater
class update_test(unittest.TestCase):
    temp_dir = ""

    def setUp(self):
        import tempfile
        self.temp_dir = tempfile.mkdtemp()

    #Make sure basic updator works
    def testUpdater(self):
        sys.path[0]= self.temp_dir
        import modules.update as update
        update.update_mloxdata()

        self.assertTrue(os.path.isfile(self.temp_dir+'/mlox-data.7z'),term_color['red']+"Unable to download mlox-data.7z"+term_color['clear'])
        self.assertTrue(os.path.isfile(self.temp_dir+'/mlox_base.txt'),term_color['red']+"Unable to extract mlox_base.txt"+term_color['clear'])

        update.update_mloxdata()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

unittest.main()
