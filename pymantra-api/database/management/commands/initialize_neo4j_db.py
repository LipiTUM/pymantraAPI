import glob
import shutil

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from pymantra.database import NetworkGenerator
from pymantra.statics import NODE_FILES, EDGE_FILES


class Command(BaseCommand):
    help = 'Set up the neo4j database required for pymantra.'

    def handle(self, *args, **kwargs):
        try:
            url = settings.NEO4J_DB.get('protocol') + "://" + settings.NEO4J_DB.get('host') + ":" + settings.NEO4J_DB.get('port')
            auth = (settings.NEO4J_DB.get('user'), settings.NEO4J_DB.get('password'))


            nodes, edges = 0, 0
            print('Checking the neo4j database...')
            with NetworkGenerator(url, auth) as network_generator:
                n_nodes = network_generator.n_nodes
                n_edges = network_generator.n_edges
                print(f"The neo4j database contains {nodes} nodes and {edges} edges.")
            print('Checked the neo4j database.')

            if nodes == 0 and edges == 0:
                print('neo4j database setup failed!')

        except Exception as e:
            traceback = e.__traceback__
            while traceback:
                print("{}: {}".format(traceback.tb_frame.f_code.co_filename,traceback.tb_lineno))
                traceback = traceback.tb_next
            raise CommandError(
                'Initalization failed for the neo4j database.',
                e
            )
