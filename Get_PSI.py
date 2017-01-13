"""
@authors: Juan L. Trincado
@email: juanluis.trincado@upf.edu

Get_PSI.py: calculate the PSI inclusion of the reads of the samples using the clusters
 generated by LeafCutter and returns a file with all the PSI values together, removing those clusters with NA values
 The input of this file should be the path where the LeafCutter files are located, and the readCOunts file
"""

import sys
import pandas as pd
import os
import time
from copy import deepcopy

def main():
    try:

        LeafCutter_path = sys.argv[1]
        readCounts_path = sys.argv[2]

        # LeafCutter_path = "/projects_rg/Bellmunt/STAR/whole_cohort/LeafCutter_output"
        # readCounts_path = "/projects_rg/Bellmunt/STAR/whole_cohort/readCounts.tab"

        print("Starting execution: "+time.strftime('%H:%M:%S')+"\n\n")

        #############################################################################################################
        #1. Load the files generated by LeafCutter with the cluster numbers and return a file with all the PSI values
        #############################################################################################################

        bashCommand = "ls "+LeafCutter_path+"/*sorted.gz"
        # bashCommand = "ls /genomics/users/juanluis/SCLC/data/test_LeafCutter/LeafCutter_cluster_results_prueba/*sorted.gz"
        cluster_files = os.popen(bashCommand, "r")

        for line in cluster_files:

            print("Loading file: " + line.rstrip() + "...\n")
            file = pd.read_table(line.rstrip(), header=None, delimiter=" ", compression='gzip', skiprows=1)
            #For each line, calculate the PSI normalizing across the total number of reads per cluster
            psi_list = []

            for i in range(0, len(file.index)):
                # print(i)
                aux = file.iloc[i,1].split("/")
                #If the denominator is 0, skip this line
                if(float(aux[1])!=0):
                    PSI = float(aux[0])/float(aux[1])
                else:
                    PSI = "NaN"
                psi_list.append(PSI)

            file['PSI'] = psi_list

            #Save the dataframe
            # print("Creating file "+line.rstrip()+"...")
            output_path = LeafCutter_path + "/" + line.rstrip().split("/").pop()
            file.to_csv(output_path[:-3], sep=" ", index=False,  float_format='%.f', header=False)

        ##################################################
        #2. Remove all the Na rows and merge all the files
        ##################################################

        bashCommand = "ls "+LeafCutter_path+"/*sorted"
        # bashCommand = "ls /genomics/users/juanluis/test_LeafCutter/*sorted"
        cluster_files = os.popen(bashCommand, "r")
        counter = 0

        for line in cluster_files:

            #Load each file and remove the Nan values
            file = pd.read_table(line.rstrip(), header=None, delimiter=" ").dropna()
            #Remove the column with the reads
            del file[1]
            sampleId = line.rstrip().split("/").pop().split(".junc")[0]
            file = file.rename(columns={0: "Index", 2: sampleId})
            if(counter!=0):
                #merge both files
                file_merged = file_merged.merge(file,left_on="Index", right_on="Index", how='inner')
            else:
                file_merged = deepcopy(file)
            counter += 1

        #Split the index for having this info in different columns
        index_splitted = file_merged['Index'].apply(lambda x: x.split(":"))
        chr = list(map(lambda x: x[0],index_splitted))
        start = list(map(lambda x: x[1],index_splitted))
        end = list(map(lambda x: x[2],index_splitted))
        cluster = list(map(lambda x: x[3],index_splitted))
        id2 = file_merged['Index'].apply(lambda x: ";".join(x.split(":")[:-1])).tolist()

        #Add this lists to file_merged
        file_merged['start'] = start
        file_merged['end'] = end
        file_merged['chr'] = chr
        file_merged['cluster'] = cluster
        file_merged['id2'] = id2

        print("Nrows of file_merged "+str(len(file_merged.index)))

        #####################################################################
        #3. Enrich the output. Get the Junction type and the associated genes
        #####################################################################

        print("Loading readCounts file...\n")
        readCounts = pd.read_table(readCounts_path, delimiter="\t")

        #Format previously the id. Add 1 to the end (Leafcutter adds 1 to the end cordinates)
        id3 = readCounts['id'].apply(lambda x: ";".join(x.split(";")[0:2])+";"+(str(int(x.split(";")[2])+1))).tolist()
        readCounts['id2'] = id3

        #We are interested just in a few columns
        readCounts = readCounts[['id2', 'Associated_genes', 'Type_junction']]

        #Merge this info with the previous file for getting the Junction type and the associated genes
        file_merged2 = file_merged.merge(readCounts, left_on="id2", right_on="id2", how='inner')

        print("Nrows of file_merged2 "+str(len(file_merged2.index)))



        #Put it in the proper order for the vcf file
        sorted_columns = sorted(file_merged2.columns)

        # Remove the columns at the end and put it at the beginning
        sorted_columns.remove('cluster')
        sorted_columns.remove('chr')
        sorted_columns.remove('end')
        sorted_columns.remove('start')
        sorted_columns.remove('Associated_genes')
        sorted_columns.remove('Type_junction')
        sorted_columns.remove('Index')
        sorted_columns.insert(0, "Associated_genes")
        sorted_columns.insert(0, "Type_junction")
        sorted_columns.insert(0, "cluster")
        sorted_columns.insert(0, "end")
        sorted_columns.insert(0, "start")
        sorted_columns.insert(0, "chr")
        sorted_columns.insert(0, "Index")

        file_merged3 = file_merged2.reindex(columns=sorted_columns)
        del file_merged3["id2"]

        #Sort the file
        file_merged_sorted = file_merged3.sort(['chr', 'cluster', 'start', 'end'])

        #Save the dataframe
        output_path = LeafCutter_path + "/psi_all_samples.tab"
        print("Creating file "+output_path+"...")
        file_merged_sorted.to_csv(output_path, sep="\t", index=False)

        print("Done. Exiting program. "+time.strftime('%H:%M:%S')+"\n\n")

        exit(0)

    except Exception as error:
        print('ERROR: ' + repr(error))
        print("Aborting execution")
        sys.exit(1)


if __name__ == '__main__':
    main()