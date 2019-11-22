from tests import *

if __name__ == "__main__":
    import dotenv
    import unittest
    from django.conf import settings
    
    dotenv.read_dotenv()
    settings.configure()
    unittest.main()


