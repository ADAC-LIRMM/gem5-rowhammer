import os
import sys


def gem5_repository():

        path_gem5 = os.getcwd()
        while(os.path.basename(path_gem5) != "gem5"):
                path_gem5 = os.path.abspath(os.path.join(path_gem5, os.pardir))
                if path_gem5 == '/':
                        print(" Error: gem5 parent directory cannot be found \
                                with the path_init.py script.")
                        sys.exit()

        if(os.path.isdir(path_gem5)):
                return path_gem5

        else:
                print("Error: " + path_gem5 + " is not a directory.")


def gem5_ARM_binary():

        path_gem5_binary  = gem5_repository()
        path_gem5_binary += "/build/ARM/gem5.opt"

        if(os.path.isfile(path_gem5_binary)):
                return path_gem5_binary

        else:
                print("Error: " + path_gem5_binary + " is not found. Check if \
                        gem5 has been built correctly for ARM architecture.")
                sys.exit()


def gem5_output(path_folder):

        path_gem5_folder  = gem5_repository()
        path_gem5_folder += "/" + path_folder
        os.system("mkdir -p " + path_gem5_folder)

        if(os.path.isdir(path_gem5_folder)):
                return path_gem5_folder

        else:
                print("Error: The output folder " + path_gem5_folder + " is \
                        not found or cannot be created")
                sys.exit()



def gem5_file(path_file):

        path_gem5_file  = gem5_repository()
        path_gem5_file += "/" + path_file

        if(os.path.isfile(path_gem5_file)):
                return path_gem5_file

        else:
                print("Error: The file " + path_gem5_file + " is not found.")
                sys.exit()

def gem5_folder(path_folder):

        path_gem5_folder  = gem5_repository()
        path_gem5_folder += "/" + path_folder

        if(os.path.isdir(path_gem5_folder)):
                return path_gem5_folder

        else:
                print("Error: The folder " + path_gem5_folder \
                        + " is not found.")
                sys.exit()
