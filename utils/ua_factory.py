import ua_generator

def get_ua():
    # Generates a random, valid browser user-agent
    ua = ua_generator.generate()
    return str(ua)
