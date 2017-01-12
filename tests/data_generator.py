import os
from badge_hub import get_audio_name, get_proximity_name
from badge_hub import MAX_PENDING_FILE_SIZE

def _create_file(name, size):
    with open(name, "wb") as f:
        f.seek(size)
        f.write("\0")     

def generate_full_pending():
    """
    Generate a pending file >= MAX_PENDING_FILE_SIZE in size
    """
    audio_filename = get_audio_name()
    proximity_filename = get_proximity_name()
    
    _create_file(audio_filename, MAX_PENDING_FILE_SIZE + 100) 
    _create_file(proximity_filename, MAX_PENDING_FILE_SIZE + 100)

    assert os.path.getsize(audio_filename) > MAX_PENDING_FILE_SIZE
    assert os.path.getsize(proximity_filename) > MAX_PENDING_FILE_SIZE
    return (audio_filename, proximity_filename)
def generate_empty_pending():
    """
    Generate an empty pending file
    """
    #TODO
    pass

def generate_half_pending():
    """
    Generate a pending file approx. equal to MAX_PENDING_FILE_SIZE/2 in size
    """
    audio_filename = get_audio_name()
    proximity_filename = get_proximity_name()
    
    _create_file(audio_filename, int(MAX_PENDING_FILE_SIZE / 2))
    _create_file(proximity_filename, int(MAX_PENDING_FILE_SIZE / 2))
    
    return (audio_filename, proximity_filename)
