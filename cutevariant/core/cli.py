
import argparse
import os 
import progressbar
import pprint
import sys
import logging 

from columnar import columnar

from cutevariant.core.importer import import_file, async_import_file
from cutevariant.core import sql
from cutevariant.core import vql


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    parser = argparse.ArgumentParser(description="""
    Cutevariant cli mode helps your to run actions directly from command-line
    """)
    sub_parser = parser.add_subparsers(dest='subparser')
    
    #createdb parser 
    createdb_parser = sub_parser.add_parser("createdb", help="Build a sqlite database from a vcf file")
    createdb_parser.add_argument("-i", "--input", help="VCF file path", required=True)
    createdb_parser.add_argument("-o", "--output", help="cutevariant sqlite database path")

    #show parser 
    show_parser = sub_parser.add_parser("show", help="Display table content")
    show_parser.add_argument("table", choices=["fields","selections","samples"], help="Name of tables")
    show_parser.add_argument("--db", help="sqlite database. By default, $CUTEVARIANT_DB is used")

    #exec parser 
    select_parser = sub_parser.add_parser("exec", help="Execute VQL statement")
    select_parser.add_argument("vql", help="A vql statement")
    select_parser.add_argument("--db", help="sqlite database. By default, $CUTEVARIANT_DB is used")
    select_parser.add_argument("--limit", help="limit output to line number", type=int, default=100)

    # #Set parser
    # set_parser = sub_parser.add_parser("set", help="Set variable")
    # set_parser.add_argument("--db", help="Set $CUTEVARIANT_DB env variable ",type=str)




    args = parser.parse_args()

    if len(sys.argv)==1:
        parser.print_help(sys.stderr)
        sys.exit(1)
 
    if "CUTEVARIANT_DB" in os.environ and args.subparser != "createdb":
        args.db = os.environ['CUTEVARIANT_DB']
        conn = sql.get_sql_connexion(args.db)


    # ====== CREATEDB ============================
    if args.subparser == "createdb":
        if args.output == None:

            args.output = args.input + ".db"

            if os.path.exists(args.output):
                os.remove(args.output)

        conn = sql.get_sql_connexion(args.output)

        if conn:
            #TODO: bug ... max is not 100...
            for i, message in progressbar.progressbar(async_import_file(conn, args.input), redirect_stdout=True):
                print(message)

    # ====== SHOW ============================
    if args.subparser == "show":
        if args.table == "fields":
            print(columnar([i.values() for i in sql.get_fields(conn)], headers=["id","Name","table","type", "description"],  no_borders=True))

        if args.table == "samples":
            print(columnar([i.values() for i in sql.get_samples(conn)], headers=["id","Name"],  no_borders=True))        
        
        if args.table == "selections":
            print(columnar([i.values() for i in sql.get_selections(conn)], headers=["id","Name"],  no_borders=True))


    # ====== EXEC VQL ============================
    if args.subparser == "exec":
        query = "".join(args.vql)


        try:
            cmd = next(vql.execute_vql(query))   

        except vql.textx.TextXSyntaxError as e:
            # Available attributes: e.message, e.line, e.col
            print("==================================== ERRORS ====================================")
            print("TextXSyntaxError: %s, col: %d" % (e.message, e.col))
            print(" ")
            print(query)
            print("_" * (e.col - 1) + "^\n")
            exit(0)

        except vql.VQLSyntaxError as e:
            # Available attributes: e.message, e.line, e.col
            print("==================================== ERRORS ====================================")
            print("TextXSyntaxError: %s, col: %d" % (e.message, e.col))
            print(" ")
            print(query)
            print("_" * (e.col - 1) + "^ \n")
            exit(0)


        if cmd["cmd"] == "select_cmd":
            selector = sql.QueryBuilder(conn)

            print(cmd.get("filter"))
            
            selector.columns = cmd.get("columns")
            selector.filters = cmd.get("filter")
            #selector.group_by = ["chr","pos","ref","alt"]
            
            # remove ids 
            
            #print(columnar(items, headers =selector.headers(), no_borders=True))
            
            tree = []
            for v in selector.trees(grouped = True,limit = args.limit):
                
                #line = [len(v)] + v[0]
                #tree.append(line)

                print(v)
                #line.append(variant_group[0])

                #tree.append(line)

            for v in selector.children(3):
                print(v)

            #print(tree)
            #print(selector.headers)
            #print(columnar(tree, headers = ["child"] + list(selector.headers()), no_borders=True))

          
