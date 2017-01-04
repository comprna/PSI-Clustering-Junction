import os, sys, glob, math

# TODO The rpkm.tab generation is actually commented because some error converting to int, fix this

try:
    inFilePattern = sys.argv[1]+"*/SJ.out.geneAnnotated.bed"
    totalMappedReadsFilePath = sys.argv[1]+"totalMappedReads.tab"
    averageLengthFilePath = sys.argv[1]+"averageLength.tab"
    outCountsFilePath = sys.argv[1]+"readCounts.tab"
    outRpkmFilePath = sys.argv[1]+"rpkm_final.tab"

    # inFilePattern = "/projects_rg/Bellmunt/STAR/TEST/*/SJ.out.geneAnnotated.bed"
    # totalMappedReadsFilePath = "/projects_rg/Bellmunt/STAR/TEST/totalMappedReads.tab"
    # averageLengthFilePath = "/projects_rg/Bellmunt/STAR/TEST/averageLength.tab"
    # outCountsFilePath = "/projects_rg/Bellmunt/STAR/TEST/readCounts_final.tab"
    # outRpkmFilePath = "/projects_rg/Bellmunt/STAR/TEST/rpkm_final.tab"

    inFilePaths = glob.glob(inFilePattern)

    print ("Pooling data...")

    metaDict = {}
    countDict = {}
    headerItems = None
    samples = []
    for inFilePath in inFilePaths:
        inFileData = [line.rstrip().split("\t") for line in open(inFilePath)]
        sampleID = os.path.basename(os.path.dirname(inFilePath))

        if inFilePath == inFilePaths[0]:
            headerItems = inFileData.pop(0)
            headerItems = headerItems[:4] + headerItems[5:]
        else:
            inFileData.pop(0)

        #headerItems.append(sampleID)
        samples.append(sampleID)
        for rowItems in inFileData:
            metaItems = rowItems[:4] + rowItems[5:]
            rowID = metaItems[0]
            counts = rowItems[4]

            if not rowID in metaDict:
                metaDict[rowID] = metaItems

            if not rowID in countDict:
                countDict[rowID] = {}

            countDict[rowID][sampleID] = counts

    for item in sorted(samples):
        headerItems.append(item)

    totalMappedReads = {}
    for line in open(totalMappedReadsFilePath):
        lineitems = line.rstrip().split("\t")
        totalMappedReads[lineitems[0]] = lineitems[1]

    averageLength = {}
    for line in open(averageLengthFilePath):
        lineitems = line.rstrip().split("\t")
        averageLength[lineitems[0]] = lineitems[1]

    outCountsFile = open(outCountsFilePath, 'w')
    outCountsFile.write("\t".join(headerItems) + "\n")
    outRpkmFile = open(outRpkmFilePath, 'w')
    outRpkmFile.write("\t".join(headerItems) + "\n")

    print ("There are %d genes to calculate" % len(metaDict))
    print ("")

    i = 1
    for rowID in sorted(metaDict):
        sys.stdout.write("\rCurrently on: %d" % i,)
        sys.stdout.flush()
        outCountsRow = list(metaDict[rowID])
        outRpkmRow = list(metaDict[rowID])
        for sampleID in headerItems[8:]:
            sampleCount = "0"
            rpkm = "0"
            if sampleID in countDict[rowID]:
                sampleCount = countDict[rowID][sampleID]
                tmr = float(totalMappedReads[sampleID])
                al = float(averageLength[sampleID])
                rpkm = "%.9f" % ((math.pow(10,9) * float(sampleCount)) / (tmr * al))
            outCountsRow.append(sampleCount)
            outRpkmRow.append(rpkm)
        outCountsFile.write("\t".join(outCountsRow) + "\n")
        outRpkmFile.write("\t".join(outRpkmRow) + "\n")
        i += 1

    i -= 1
    sys.stdout.write("\rCurrently on: %d\n" % i, )
    outCountsFile.close()
    print("Generated file "+outCountsFilePath)
    outRpkmFile.close()
    print("Generated file " + outRpkmFilePath)

except Exception as error:
    print('\nERROR: ' + repr(error))
    print("Aborting execution")
    sys.exit(1)