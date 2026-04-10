# Banned keywords list (You can add more)
BAD_WORDS = [
    "xxx", "porn", "nude", "sex", "onlyfans", "leak", 
    "bhabi", "desi", "mms", "nsfw", "brazzers", "ullu", 
    "kullu", "hot", "naked", "chudai"
]

def is_nsfw(filename):
    if not filename:
        return False
        
    text = filename.lower()
    
    # Check for bad words in filename
    for word in BAD_WORDS:
        if word in text:
            return True
            
    return False
