#!/usr/bin/env python3.7
import os
import sys
cwd = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.normpath(os.path.join(cwd, '../../'))
sys.path.insert(0, parent_dir)
from util import pxc_startup
from util import db_connection
from util import sysbench_run
from util import utility
from util import createsql
import configparser

# Reading initial configuration
config = configparser.ConfigParser()
config.read(parent_dir + '/config.ini')
workdir = config['config']['workdir']
basedir = config['config']['basedir']
user = config['config']['user']
node = config['config']['node']
node1_socket = config['config']['node1_socket']
node2_socket = config['config']['node2_socket']
pt_basedir = config['config']['pt_basedir']
sysbench_user = config['sysbench']['sysbench_user']
sysbench_pass = config['sysbench']['sysbench_pass']
sysbench_db = config['sysbench']['sysbench_db']
sysbench_threads = 10
sysbench_table_size = 1000
sysbench_run_time = 10
utility_cmd = utility.Utility()


class SSLCheck:
    def __init__(self, basedir, workdir, user, socket, node):
        self.workdir = workdir
        self.basedir = basedir
        self.user = user
        self.socket = socket
        self.node = node

    def run_query(self, query):
        query_status = os.system(query)
        if int(query_status) != 0:
            return 1
            print("ERROR! Query execution failed: " + query)
            exit(1)
        return 0

    def start_pxc(self):
        # Start PXC cluster for replication test
        dbconnection_check = db_connection.DbConnection(user, self.socket)
        server_startup = pxc_startup.StartCluster(parent_dir, workdir, basedir, int(node))
        result = server_startup.sanity_check()
        utility_cmd.check_testcase(result, "Startup sanity check")
        result = server_startup.create_config('ssl')
        utility_cmd.check_testcase(result, "Configuration file creation")
        result = utility_cmd.create_ssl_certificate(workdir)
        utility_cmd.check_testcase(result, "SSL Configuration")
        result = server_startup.initialize_cluster()
        utility_cmd.check_testcase(result, "Initializing cluster")
        result = server_startup.start_cluster()
        utility_cmd.check_testcase(result, "Cluster startup")
        result = dbconnection_check.connection_check()
        utility_cmd.check_testcase(result, "Database connection")

    def sysbench_run(self, socket, db):
        sysbench = sysbench_run.SysbenchRun(basedir, workdir,
                                            sysbench_user, sysbench_pass,
                                            socket, sysbench_threads,
                                            sysbench_table_size, db,
                                            sysbench_threads, sysbench_run_time)

        result = sysbench.sanity_check()
        utility_cmd.check_testcase(result, "SSL QA sysbench run sanity check")
        result = sysbench.sysbench_load()
        utility_cmd.check_testcase(result, "SSL QA sysbench data load")

    def data_load(self, db, socket ):
        if os.path.isfile(parent_dir + '/util/createsql.py'):
            generate_sql = createsql.GenerateSQL('/tmp/dataload.sql', 1000)
            generate_sql.OutFile()
            generate_sql.CreateTable()
            sys.stdout = sys.__stdout__
            create_db = self.basedir + "/bin/mysql --user=root --socket=" + \
                socket + ' -Bse"drop database if exists ' + db + \
                ';create database ' + db + ';" 2>&1'
            result = os.system(create_db)
            utility_cmd.check_testcase(result, "SSL QA sample DB creation")
            data_load_query = self.basedir + "/bin/mysql --user=root --socket=" + \
                socket + ' ' + db + ' -f <  /tmp/dataload.sql >/dev/null 2>&1'
            result = os.system(data_load_query)
            utility_cmd.check_testcase(result, "SSL QA sample data load")


ssl_run = SSLCheck(basedir, workdir, user, node1_socket, node)
ssl_run.start_pxc()
ssl_run.sysbench_run(node1_socket, 'test')
ssl_run.data_load('pxc_dataload_db', node1_socket)
result = utility_cmd.check_table_count(basedir, 'test', 'sbtest1', node1_socket, node2_socket)
utility_cmd.check_testcase(result, "SSL QA table test.sbtest1 checksum between nodes")
utility_cmd.check_testcase(result, "SSL QA table pxc_dataload_db.t1 checksum between nodes")
