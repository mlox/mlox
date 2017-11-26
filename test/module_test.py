#! /usr/bin/python3

# A test script to make sure all the modules work

import sys
import os
import subprocess
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
        self.assertTrue(a is None)
        self.assertTrue(b is None)
        self.assertEqual(c, os.path.abspath('..'))

        #TODO:  Actually test these two (seperately)
        #print(fileFinder.filter_dup_files(dir_list.filelist()))

#Config Handler
class configHandler_test(unittest.TestCase):
    import modules.configHandler as configHandler
    zinx_txt = ['Better Heads Bloodmoon addon.esm', 'Better Heads Tribunal addon.esm', 'Better Heads.esm',
                'Bloodmoon.esm', 'MCA.esm', 'Morrowind.esm', 'Tribunal.esm', 'ACE_Subtitles.esp',
                'Balmora Expansion - LITE 1.0.esp', 'Balmora Expansion v1.4.esp', 'BAR_DarkshroudKeep_v1.2.esp',
                'Beasts of Burden Necromancer.esp', 'Better Bodies.esp', 'Better Clothes_v1.0_nac.esp',
                'BE_dh_furn_stores .esp', 'BE_Personal_Fix.esp', 'Blasphemous Revenants.esp', 'BR Dead Heros.esp',
                'Dark_Stone_Fortress.esp', 'Flee AI Tweaks.esp', 'IceNioLivRobeReplacerALL.esp',
                'Illuminated Order v1.0 - Bloodmoon Compatibility Extras.esp', 'Illuminated Order v1.0.esp',
                'indybank.esp', 'Level List Merger.esp', 'MCA - Guards Patch.esp', 'MCA - Personal Fix.esp',
                'MCA - Vampire Realism Patch.esp', 'MTT Vol III.esp', 'MWE_Base.esp', 'MWE_Combat.esp',
                'MWE_Writing.esp', 'Necro Armor v1_0.esp', 'Propylon Fix.esp', 'Quest Fix.esp', 'Scripted_Spells.esp',
                'Slave Trade.esp', "Slof's BB neck fix.esp", "Slof's Better Beasts b.esp",
                'Vampire Realism II - BM Add-On.esp', 'Vampire Realism II - TB Add-On.esp',
                'Vampire Realism II - VE Patch.esp', 'Vampire Realism II.esp', 'Vampire_Embrace.esp',
                'Vampire_Werewolf.esp', "Wakim's Game Improvement 9.esp", 'werewolfrealism-moononly.esp',
                'Werewolf_Evolution.esp']

    # Get  list of plugins (in order from the correct directory)
    test1_plugins_raw = subprocess.check_output('cd test1.data; ( ls -rt *.esm ; ls -rt *.esp ) | col', shell=True)
    test1_plugins= test1_plugins_raw.decode().split('\n')[:-1]

    modified_plugins = list(test1_plugins)
    modified_plugins[-2] = test1_plugins[-1]
    modified_plugins[-1] = test1_plugins[-2]
    morrowind_ini = ['Morrowind.esm', 'Tribunal.esm', 'BLOODMOON.esm', 'GIANTS.esm', 'TR_Data.esm', 'TR_Map1.esm',
                     'TR_Map2.esm', 'Better Heads.esm', 'Better Heads Tribunal addon.esm',
                     'Better Heads Bloodmoon addon.esm', 'BT_Whitewolf_2_0.esm', 'The Wilderness Mod 2.0.esm',
                     'The Wilderness Mod 2.0 T & B.esm', 'Morrowind Comes Alive.esm', 'Morrowind Patch v1.6.5-BETA.esm',
                     'fem_body.esp', 'Zed.esp', 'RealSignposts.esp', 'Passive_Healthy_Wildlife.esp', 'entertainers.esp',
                     'AreaEffectArrows.esp', 'bcsounds.esp', 'LeFemmArmor.esp', 'adamantiumarmor.esp',
                     'EBQ_Artifact.esp', 'Siege at Firemoth.esp', 'A good place to stay, Teleport Addon.esp',
                     'A good place to stay, Ver 1,8.esp', 'No-Glo_0709.esp', 'Clean Water Nymph race.esp',
                     'female_cuirasses_2.0.esp', 'Weapon Wielding Mannequins.esp', 'Nerevarine Greeting tweaks.esp',
                     'Aduls_Artifact_Replace_(Trueflame).esp', 'GIANTS Ultimate Control file.esp', 'Blood and Gore.esp',
                     'Better Bodies.esp', 'Meteor.esp', 'HelioS - Giants Fix.esp',
                     'Silt_Striders_Are_In_Vvardenfell.esp', "Taddeus'BalancedArmors.esp",
                     'CET_Meteoric_Steel_Mail.esp', 'Vivec Signposts.esp', 'Amazon War Boots 1.0.esp',
                     'Annastia V3.3.esp', 'indybankWC.esp', 'MTT IV Master.esp', "Taddeus'BalancedObjects.esp",
                     'Amazon Platemail Greaves 2.0.esp', 'GIANTS_Ultimate_Official_Fixes.esp',
                     'Sexy Daedric Armor v1.1.esp', 'Morrowind Comes Alive Guards Patch.esp',
                     'MCAnames4.1lorecorrect.esp', 'Clean BB_Tshirt_and_Skirt.esp', 'Sexy Ordinator Armor 2.esp',
                     'Sexy Glass Armor v1.1.esp', 'Sexy Ice Armor v1.1.esp', 'Amazon Tops.esp', "Bob's Armory.esp",
                     'Clean Better Daedric.esp', 'Better Solsthiem Creatures.esp', 'Sexy Ebony Armor.esp',
                     "Unofficial_Expansion_for_Louis'_BeautyShop.esp", 'BT_Whitewolf_2_0.esp', 'EarthlyDelights.esp',
                     'Better Clothes Beta_1.4.esp', 'ARJAN_A_Lords_Men_v2.0.esp', 'Louis_BeautyShop_v1.5.esp',
                     'StripForMe.esp', 'KeyNamer.esp', 'ModMan_windowlights_full_2.esp',
                     'Lockpick__Probe_Weight_Fix.esp', 'Wolfen Castle.esp', 'Tribun_Laura_3_0.esp', 'master_index.esp',
                     'Merged_Objects.esp', 'Merged_Dialogs.esp', 'Merged_Leveled_Lists.esp']

    def test_No_File(self):
        """Test reading a file that does not exist"""
        with self.assertLogs('mlox.configHandler',level='ERROR') as l:
            handleri = self.configHandler.configHandler("No File")
            self.assertEqual(handleri.read(),[])
            self.assertEqual(l.output, ['ERROR:mlox.configHandler:Unable to open configuration file: No File'])

    def test_Morrowind_only(self):
        """Test reading a file that only contains morrowind game entries"""
        self.assertEqual(self.configHandler.configHandler("./userfiles/zinx.txt","Morrowind").read(),self.zinx_txt)

    def test_Morrowind_ini_reading(self):
        """Test reading an actual morrowind.ini"""
        self.assertEqual(self.configHandler.configHandler("./testM/Morrowind.ini","Morrowind").read(),self.morrowind_ini)

    def test_Invalid(self):
        with self.assertLogs('mlox.configHandler',level='WARNING') as l:
            self.assertEqual(self.configHandler.configHandler("./userfiles/zinx.txt","Invalid").read(),self.zinx_txt)
            self.assertEqual(l.output, ['WARNING:mlox.configHandler:"Invalid" is not a recognized file type!'])

    def test_Default(self):
        self.assertEqual(self.configHandler.configHandler("./userfiles/zinx.txt").read(),self.zinx_txt)

    def test_Oblivion(self):
        #TODO: Actually test this one (Using an oblivion file)
        #print(self.configHandler.configHandler("./userfiles/zinx.txt","Oblivion").read())
        pass

    def test_dirHandler(self):
        """read, check, modify, check modifications, then restore to original"""
        dirHandler = self.configHandler.dataDirHandler("./test1.data/")
        self.assertEqual(dirHandler.read(),self.test1_plugins)
        dirHandler.write(self.modified_plugins)
        self.assertEqual(dirHandler.read(),self.modified_plugins)
        dirHandler.write(self.test1_plugins)

    def test_morrowind_ini_clearing_writing(self):
        """
        Test both clearing and writing to a morrowind.ini file at the same time
        (if read tests failed earlier, this will also fail)
        """
        import shutil
        shutil.copyfile("./testM/Morrowind.ini",".tmp")
        handlerM = self.configHandler.configHandler(".tmp","Morrowind")
        handlerM.clear()
        self.assertEqual(handlerM.read(),[])
        handlerM.write(self.morrowind_ini)
        self.assertEqual(handlerM.read(),self.morrowind_ini)
        os.remove(".tmp")

#Parser, and pluggraph
class parser_pluggraph_test(unittest.TestCase):
    import modules.ruleParser as ruleParser
    import modules.pluggraph as pluggraph
    import modules.fileFinder as fileFinder
    file_names = fileFinder.caseless_filenames()
    test1_graph = ['morrowind.esm', 'tribunal.esm', 'bloodmoon.esm', 'morrowind patch v1.6.4 (wip).esm',
                   'rf - furniture shop.esm', 'metalqueenboutique.esm', 'book rotate.esm', 'gdr_masterfile.esm',
                   'bt_whitewolf_2_0.esm', 'tr_data.esm', 'tr_map1.esm', 'the undead.esm',
                   'text patch for morrowind with tribunal & bloodmoon.esp', 'lgnpc_sn.esp', 'realsignposts.esp',
                   'dagonfel_well.esp', 'myth and murder ver 2.0.esp', "wakim's game improvement 9.esp", 'chessv4.esp',
                   'lgnpc_nolore_v0_83.esp', 'officialmods_v5.esp', "zyndaar's bows.esp", 'dwemerclock.esp',
                   'uumpp bloated morrowind patch v1.6.4.esp', 'tlm - light sources (natural water).esp',
                   'tlm - ambient light + fog update.esp', 'tlm - npc light sources.esp', 'dh_furn.esp',
                   'dh_furn_stores.esp', 'dh_thriftshop.esp', 'tlm - light sources (lanterns).esp',
                   'tlm - light sources (clearer lighting).esp', 'p.r.e. v4.0.esp', 'nudity greeting expansion v1.esp',
                   'book rotate - morrowind v1.1.esp', 'rf - bethesda furniture.esp', 'better bodies.esp',
                   'silt_striders_are_in_vvardenfell.esp', 'werewolf_evolution.esp', 'rkwerewolf.esp',
                   'vampire_werewolf.esp', 'windows glow.esp', 'unboarable rieklings.esp', 'bm_s_inn.esp',
                   'smooth moves v1.esp', "slof's vampire faces.esp", 'vampire realism ii.esp',
                   'vampire realism ii - tb add-on.esp', 'vampire realism ii - bm add-on.esp',
                   'vampire realism ii - ve patch.esp', 'vampire realism ii - bl patch.esp',
                   'abotwhereareallbirdsgoing.esp', "ng_new_carnithus'_armamentarium.esp", 'scripted_spells.esp',
                   'nixie.esp', 'book rotate - tribunal v5.3.esp', 'book rotate - bloodmoon v5.3.esp',
                   'clean sexy_black_collar_dress_v.1a.esp', 'keynamer.esp', 'tribun_laura_3_0.esp',
                   'galsiahs character development.esp', 'gcd startscript for trib or bloodmoon.esp',
                   'gcd better balanced birthsigns.esp', 'gcd restore potions fix.esp', 'gcd_ss_patch.esp',
                   'brittlewind fix.esp', 'gcd_we_patch.esp', 'drug realism.esp',
                   "juniper's twin lamps (1.1 tribunal).esp", 'gcd_107x_to_108_patch.esp', 'vampire_embrace.esp',
                   'sslave_companions.esp', 'bt_wwlokpatch1.esp', 'vampiric hunger base.esp',
                   'vampiric hunger extended.esp', 'vampiric hunger - su.esp', 'gcd_vh_patch2.esp',
                   'arjan_a_lords_men_v2.0.esp', 'book jackets - morrowind - bookrotate.esp',
                   'dm_db armor replacer.esp', "slof's goth shop ii.esp", 'bb_clothiers_of_vvardenfell_v1.1.esp',
                   'expanded sounds.esp', 'iceniolivrobereplacerall.esp', 'barons_partners30.esp',
                   "slof's pillow book.esp", 'theubercrystalegghunt.esp',
                   'better clothes_v1.1_nac.esp', 'clean tales of seyda neen.esp', 'lgnpc_indarys_manor_v1_45.esp',
                   'new argonian bodies - mature.esp', 'lgnpc_gnaarmok_v1_10.esp', 'lgnpc_aldvelothi_v1_20.esp',
                   'lgnpc_maargan_v1_10.esp', 'new khajiit bodies - mature.esp', 'lgnpc_secret_masters_v1_21.esp',
                   'gothic attire complete v1-1.esp', "building up uvirith's grave 1.1.esp",
                   'secrets of vvardenfell.esp', 'the_vvardenfell_libraries.esp', 'lgnpc_hlaoad_v1_32.esp',
                   'nede v1.2.esp', 'nede wgi patch.esp', 'rts_faeriesseydaneen.esp', 'rts_healingfaeries.esp',
                   'sris_alchemy_bm.esp', 'sri alchemy bm list patch.esp', 'creatures.esp', 'creaturesx-jms_patch.esp',
                   'dn-gdrv1.esp', 'syc_herbalismforpurists.esp', 'syc_herbalismforpurists_bm.esp',
                   'syc_herbalismforpurists_tb.esp', 'syc_herbalism es patch.esp', 'multimark.esp',
                   'multimark_firemothplugin.esp', 'multimark_tribunalplugin.esp', 'multimark_bloodmoonplugin.esp',
                   'multimark-jms_patch.esp', 'all silt strider ports.esp', 'all boat ports.esp',
                   'vampire_embrace-jms_patch.esp', 'dh_thriftshop-jms_patch.esp', 'k_potion_upgrade_1.2.esp',
                   'vampire_embrace-jms_combat_bite_patch.esp', 'syc_herbalismforpurists-jms_patch.esp',
                   'jms-shishi_door_fix.esp', 'moons_soulgems.esp', 'suran_underworld_2.5.esp',
                   'lgnpc_aldruhn_v1_13.esp', 'suran_underworld_2.5-jms_patch.esp', 'bt_whitewolf_2_0-jms_patch.esp',
                   'lgnpc_pelagiad_v1_13.esp', 'lgnpc_telmora_v1_11.esp', 'chargen_revamped_v14.esp',
                   'chargen revamped delay2.esp', 'lgnpc_khuul_v2_01.esp', 'lgnpc_vivecfq_v2_03.esp',
                   'tribunal-jms_patch.esp', 'lgnpc_teluvirith_v1_10.esp', 'lgnpc_vivecredoran_v1_40.esp',
                   'lgnpc_paxredoran_v1_11.esp', 'dx_creatureadditionsv1.0.esp', 'betterclothes_patch.esp',
                   'buug alchemy- bloodmoon.esp', 'buug alchemy- srikandi.esp', 'buug alchemy- tribunal.esp',
                   'pk_tatyshirt.esp', 'clean tales of the bitter coast.esp', 'clean tales of tel branora.esp',
                   'tr_map1-jms_patch.esp', 'chalk30-base.esp', 'dh_furn-jms_patch.esp', 'mtt_iv_master.esp',
                   'jms-springheel_boots.esp', 'morrowind-jms_patch.esp', 'dn-gdrv1-jms_patch.esp',
                   'lgnpc_paxredoran_v1_11-jms_patch.esp', 'vampire_embrace-jms_follow_patch.esp',
                   'jms-ring_of_mojo.esp', 'vampire_embrace-jms_combat_bite_patch-2.esp',
                   'lgnpc_aldruhn_v1_13-jms_patch.esp', 'mashed lists.esp']

    def test_parser_base_version_good(self):
        myParser = self.ruleParser.rule_parser([],"",self.file_names)
        myParser.read_rules("../data/mlox_base.txt")
        self.assertNotEqual(myParser.version,"Unknown")

    def test_parser_base_version_bad(self):
        myParser = self.ruleParser.rule_parser([],"",self.file_names)
        myParser.read_rules("./test1.data/mlox_base.txt")
        self.assertEqual(myParser.version,"Unknown")

    def test_parser_graph(self):
        myParser = self.ruleParser.rule_parser([],"./test1.data/",self.file_names)
        myParser.read_rules("./test1.data/mlox_base.txt")
        graph=myParser.get_graph()
        self.assertEqual(graph.topo_sort(),self.test1_graph)

    #TODO:  d_ver doesn't seem correct
    def test_plugin_version(self):
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
        l1.datadir = "./test1.data/"
        l1.plugin_file = "./userfiles/abot.txt"
        l1.game_type = None
        l1.get_active_plugins()
        l1.update()
        print(l1.listversions())

    def test_Dir(self):
        l2 = self.loadorder()
        l2.datadir = "./test1.data/"
        l2.get_data_files()
        l2.update()

    def test_File(self):
        l3 = self.loadorder()
        l3.read_from_file("./userfiles/abot.txt")
        l3.update()
        print(l3.explain("Morrowind.esm"))
        print(l3.explain("Morrowind.esm", True))

#Version
class version_test(unittest.TestCase):
    import modules.version as version

    def test_internal_version(self):
        self.assertEqual(self.version.Version,'0.62')


############################################################
# update.py


def hash_file(file_path):
    """Get the hash of a file"""
    import hashlib
    with open(file_path, 'rb') as test_file:
        return hashlib.sha256(test_file.read()).hexdigest()


class update_test(unittest.TestCase):
    import modules.update as update
    temp_dir = ""
    file_name = "test100k.db"
    test_url = "http://speedtest.ftp.otenet.gr/files/test100k.db"

    def setUp(self):
        import tempfile
        self.temp_dir = tempfile.mkdtemp()
        self.local_file = os.path.join(self.temp_dir, self.file_name)

    def test_remote_file_changed(self):
        # Make sure the file doesn't exist
        self.assertTrue(self.update.remote_file_changed(self.local_file,self.test_url))
        # Download the file
        subprocess.check_call(['wget', '-O', self.local_file, self.test_url])
        # Make sure the file does exist
        self.assertFalse(self.update.remote_file_changed(self.local_file, self.test_url))
        # Zero the file (so the updater knows it needs updating)
        subprocess.check_call(['truncate', '-s0', self.local_file])
        # Make sure the updater says we need an update
        self.assertTrue(self.update.remote_file_changed(self.local_file,self.test_url))

    def test_extract_file(self):
        # Make a 7z file to test with, and get the hash
        z_file = os.path.join(self.temp_dir, 'module_test.7z')
        subprocess.check_call(['7za', 'a', z_file, 'module_test.py'])
        file_hash = hash_file('module_test.py')

        self.update.extract_file(z_file,self.temp_dir)
        new_file_hash = hash_file(os.path.join(self.temp_dir, 'module_test.py'))
        self.assertTrue(file_hash == new_file_hash)

    def test_extract_file_7za(self):
        # Make a 7z file to test with, and get the hash
        z_file = os.path.join(self.temp_dir, 'module_test.7z')
        subprocess.check_call(['7za', 'a', z_file, 'module_test.py'])
        file_hash = hash_file('module_test.py')

        self.update.extract_via_7za(z_file, self.temp_dir)
        new_file_hash = hash_file(os.path.join(self.temp_dir, 'module_test.py'))
        self.assertTrue(file_hash == new_file_hash)

    def test_extract_file_libarchive(self):
        # Make a 7z file to test with, and get the hash
        z_file = os.path.join(self.temp_dir, 'module_test.7z')
        subprocess.check_call(['7za', 'a', z_file, 'module_test.py'])
        file_hash = hash_file('module_test.py')

        self.update.extract_via_libarchive(z_file, self.temp_dir)
        new_file_hash = hash_file(os.path.join(self.temp_dir, 'module_test.py'))
        self.assertTrue(file_hash == new_file_hash)

    def test_download(self):
        self.update.download_file(self.local_file, self.test_url)
        self.assertTrue(os.path.getsize(self.local_file) == 102400)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)


if __name__ == '__main__':
    unittest.main()
