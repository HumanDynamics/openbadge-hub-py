import unittest

from badge_hub import get_archive_name, get_proximity_name, get_audio_name
from badge_hub import _create_pending_file_name
from badge_hub import AUDIO, PROXIMITY
from badge_hub import pending_file_prefix

from settings import DATA_DIR

from data_generator import generate_full_pending, generate_half_pending

import glob
import os
class TestFileHandling(unittest.TestCase):
    
    def cleanup(self):
        for filename in glob.glob(DATA_DIR + "*"):
            os.remove(filename)

    def test_name_creation(self):
        self.cleanup()
        audio_name = _create_pending_file_name(AUDIO)
        prox_name = _create_pending_file_name(PROXIMITY)
        
        # the names should be of the format:
        # <pending_file_prefix>_<datetime string>_<audio/proxmity>.txt
        self.assertTrue(AUDIO in audio_name)
        self.assertTrue(PROXIMITY in prox_name)
        self.assertTrue(audio_name.startswith(pending_file_prefix))
        self.assertTrue(prox_name.startswith(pending_file_prefix))
        self.assertTrue(audio_name.endswith(".".join((AUDIO, "txt"))))
        self.assertTrue(prox_name.endswith(".".join((PROXIMITY, "txt"))))

    def test_get_existing(self):
        self.cleanup()
        existing_audio, existing_proximity = generate_half_pending() 
        
        audio_name = get_audio_name()
        proximity_name = get_proximity_name()
    
        self.assertEquals(audio_name, existing_audio)
        self.assertEquals(proximity_name, existing_proximity)

        self.cleanup()

    def test_rollover(self):
        """
          
        """ 
        self.cleanup()
        existing_audio, existing_proximity = generate_full_pending() 
        
        audio_name = get_audio_name()
        proximity_name = get_proximity_name() 
    
        # just for kicks
        self.assertNotEqual(audio_name, proximity_name)
    
        # check to make sure the existing file was not returned
        self.assertNotEqual(audio_name, existing_audio)
        self.assertNotEqual(proximity_name, existing_proximity)

        self.cleanup()
