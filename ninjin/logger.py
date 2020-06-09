import logging

FORMAT = '%(asctime)-15s %(module)s %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('ninjin')
logger.setLevel(logging.DEBUG)
