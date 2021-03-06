#!/usr/bin/env python
'''
Copyright (c) 2012-2013 Matthias Lee

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import os
import sys
from shutil import rmtree 
import argparse
import logging as log

import pyNmonParser
import pyNmonPlotter
import pyNmonReport

class pyNmonAnalyzer:
	# Holds final 2D arrays of each stat
	processedData = {}
	nmonParser = None
	
	# Holds System Info gathered by nmon
	sysInfo = []
	bbbInfo = []
	args = []
	
	stdReport = [('CPU_ALL', ['user', 'sys', 'wait'], 'stackedGraph: true, fillGraph: true'), ('DISKBUSY', ['sda1', 'sdb1'], ''), ('MEM', ['memtotal', 'active'], ''), ('NET', ['eth0'], '')]
	
	def __init__(self, args):
		self.args = args
		if self.args.defaultConf:
			# write out default report and exit
			log.warn("Note: writing default report config file to " + self.args.confFname)
			self.saveReportConfig(self.stdReport)
			exit()
		
		if self.args.buildReport:
			# check whether specified report config exists
			if os.path.exists("report.config") == False:
				log.warn("looks like the specified config file(\""+self.args.confFname+"\") does not exist.")
				ans = raw_input("\t Would you like us to write the default file out for you? [y/n]:")
				
				if ans.strip().lower() == "y":
					self.saveReportConfig(self.stdReport)
					log.warn("Wrote default config to report.config.")
					log.warn("Please adjust report.config to ensure the correct devices will be graphed.")
				else:
					log.warn("\nNOTE: you could try using the default config file with: -r report.config")
				exit()
		
		# check ouput dir, if not create
		if os.path.exists(self.args.outdir) and args.overwrite:
			try:
				rmtree(self.args.outdir)
			except:
				log.error("Removing old dir:",self.args.outdir)
				exit()
				
		elif os.path.exists(self.args.outdir):
			log.error("Results directory already exists, please remove or use '-x' to overwrite")
			exit()
			
		# Create results path if not existing
		try:
			os.makedirs(self.args.outdir)
		except:
			log.error("Creating results dir:", self.args.outdir)
			exit()
		
		# This is where the magic begins
		self.nmonParser = pyNmonParser.pyNmonParser(args.input_file, args.outdir, args.overwrite)
		self.processedData = self.nmonParser.parse()
		
		if self.args.outputCSV or self.args.buildInteractiveReport:
			log.info("Preparing CSV files..")
			self.outputData("csv")
		if self.args.buildReport:
			log.info("Preparing graphs..")
			self.buildReport()
		if self.args.buildInteractiveReport:
			log.info("Preparing interactive Report..")
			self.buildInteractiveReport(self.processedData, args.dygraphLoc)
		
		log.info("All done, exiting.")
	
	def saveReportConfig(self, reportConf, configFname="report.config"):
		# TODO: add some error checking
		f = open(configFname,"w")
		header = '''
# Plotting configuration file.
# =====
# please edit this file carefully, generally the CPU and MEM options are left blank
# 	since there is under the hood calculations going on to plot used vs total mem and 
#	CPU plots usr/sys/wait for all CPUs on the system
# Do adjust DISKBUSY and NET to plot the desired data
#
# Defaults:
# CPU_ALL=user,sys,wait{stackedGraph: true, fillGraph: true}
# DISKBUSY=sda1,sdb1{}
# MEM=memtotal,active{}
# NET=eth0{}

'''
		f.write(header)
		for stat, fields, plotOpts in reportConf:
			line = stat + "="
			if len(fields) > 0:
				line += ",".join(fields)
			line += "{%s}\n" % plotOpts
			f.write(line)
		f.close()
	
	def loadReportConfig(self, configFname="report.config"):
		# TODO: add some error checking
		f = open(configFname, "r")
		reportConfig = []
		
		# loop over all lines
		for l in f:
			l = l.strip()
			stat=""
			fields = []
			# ignore lines beginning with #
			if l[0:1] != "#":
				bits = l.split("=")
				
				# check whether we have the right number of elements
				if len(bits) == 2:
					# interactive/dygraph report options
					optStart=-1
					optEnd=-1
					if ("{" in bits[1]) != ("}" in bits[1]):
						log.error("Failed to parse, {..} mismatch")
					elif "{" in bits[1] and "}" in bits[1]:
						optStart=bits[1].find("{")+1
						optEnd=bits[1].rfind("}")
						plotOpts=bits[1][optStart:optEnd].strip()
					else:
						plotOpts = ""
						
					stat = bits[0]
					if bits[1] != "":
						if optStart != -1:
							fields = bits[1][:optStart-1].split(",")
						else:
							fields = bits[1].split(",")
						
					if self.args.debug:
						log.debug("%s %s" % (stat, fields))
						
					# add to config
					reportConfig.append((stat,fields,plotOpts))
					
		f.close()
		return reportConfig
	
	def buildReport(self):
		nmonPlotter = pyNmonPlotter.pyNmonPlotter(self.processedData, args.outdir, debug=self.args.debug)
				
		# Note: CPU and MEM both have different logic currently, so they are just handed empty arrays []
		#       For DISKBUSY and NET please do adjust the collumns you'd like to plot
		
		if os.path.exists(self.args.confFname):
			reportConfig = self.loadReportConfig(configFname=self.args.confFname)
		else:
			log.error("something went wrong.. looks like %s is missing. run --defaultConfig to generate a template" % (self.args.confFname))
			exit()			
		
		# TODO implement plotting options
		outFiles = nmonPlotter.plotStats(reportConfig)
		
		# Build HTML report
		pyNmonReport.createReport(outFiles, self.args.outdir)
	
	def buildInteractiveReport(self, data, dygraphLoc):
		# Note: CPU and MEM both have different logic currently, so they are just handed empty arrays []
		#       For DISKBUSY and NET please do adjust the collumns you'd like to plot
		
		if os.path.exists(self.args.confFname):
			reportConfig = self.loadReportConfig(configFname=self.args.confFname)
		else:
			log.error("something went wrong.. looks like %s is missing. run --defaultConfig to generate a template" % (self.args.confFname))
			exit()			

		# Build interactive HTML report using dygraphs
		pyNmonReport.createInteractiveReport(reportConfig, self.args.outdir, data=data, dygraphLoc=dygraphLoc)
			
		
	def outputData(self, outputFormat):
		self.nmonParser.output(outputFormat)
		
if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="nmonParser converts NMON monitor files into time-sorted CSV/Spreadsheets for easier analysis, without the use of the MS Excel Macro. Also included is an option to build an HTML report with graphs, which is configured through report.config.")
	parser.add_argument("-x","--overwrite", action="store_true", dest="overwrite", help="overwrite existing results (Default: False)")
	parser.add_argument("-d","--debug", action="store_true", dest="debug", help="debug? (Default: False)")
	parser.add_argument("-i","--inputfile",dest="input_file", default="test.nmon", help="Input NMON file")
	parser.add_argument("-o","--output", dest="outdir", default="./report/", help="Output dir for CSV (Default: ./report/)")
	parser.add_argument("-c","--csv", action="store_true", dest="outputCSV", help="CSV output? (Default: False)")
	parser.add_argument("-b","--buildReport", action="store_true", dest="buildReport", help="report output? (Default: False)")
	parser.add_argument("--buildInteractiveReport", action="store_true", dest="buildInteractiveReport", help="Compile interactive report? (Default: False)")
	parser.add_argument("-r","--reportConfig", dest="confFname", default="./report.config", help="Report config file, if none exists: we will write the default config file out (Default: ./report.config)")
	parser.add_argument("--dygraphLocation", dest="dygraphLoc", default="http://dygraphs.com/dygraph-dev.js", help="Specify local or remote location of dygraphs library. This only applies to the interactive report. (Default: http://dygraphs.com/dygraph-dev.js)")
	parser.add_argument("--defaultConfig", action="store_true", dest="defaultConf", help="Write out a default config file")
	parser.add_argument("-l","--log",dest="logLevel", default="INFO", help="Logging verbosity, use DEBUG for more output and showing graphs (Default: INFO)")
	args = parser.parse_args()
	
	if len(sys.argv) == 1:
		# no arguments specified
		parser.print_help()
		exit()
	
	logLevel = getattr(log, args.logLevel.upper())
	if logLevel is None:
		print "ERROR: Invalid logLevel:", args.loglevel
		exit()
	if args.debug:
		log.basicConfig(level=logLevel, format='%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s')
	else:
		log.basicConfig(level=logLevel, format='%(levelname)s - %(message)s')
	nmonAnalyzer = pyNmonAnalyzer(args)
	