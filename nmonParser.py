#!/usr/bin/env python

class nmonParser:
	fname = ""
	outdir = ""
	rawdata = []
	outData = {}
	dataPtr=0
	sysInfo=[]
	
	def __init__(self, fname="./nmon",outdir=""):
		self.fname = fname
		self.outdir = outdir
	
	def parseSysInfo(self):
		for l in self.rawdata:
			if "AAA," in l:
				self.dataPtr+=1
				# TODO: Strip row heading
				self.sysInfo.append(l.strip())
			else:
				#if we have finished reading AAA break out 
				break
			
	def parseCols(self):
		for l in self.rawdata[self.dataPtr:]:
			if "BBBP," in l:
				#if we have finished reading headers break
				break
			else:
				self.dataPtr+=1
				bits = l.strip().split(",")
				tmp={}
				for b in bits[2:]:
					tmp[b]=[]
				self.outData[bits[0]]=tmp
				
	def parseBBBP(self):
		for l in self.rawdata[self.dataPtr:]:
			if "BBBP," in l:
				self.dataPtr+=1
				self.sysInfo.append(l.strip())
			else:
				#if we have finished reading BBBP break out
				break
			
	def parseSnapshots(self):
		for l in self.rawdata[self.dataPtr:]:
			if "ZZZZ," in l:
				#extract time
				bits = l.strip().split(',')
				print bits[3],bits[2],"\t",l
			else:
				# split into bits and append
				bits = l.strip().split(',')
				# TODO: better Checking for T#### 
				if bits[1].find("T")==0:
					tmp = self.outData[bits[0]]
					if len(tmp)!=len(bits[2:]):
						print "\n"
						print bits
						print len(tmp),len(bits[2:])
						print tmp
						print bits[2:]
				else:
					# i think we have a new field lets add it
					for b in bits[2:]:
						tmp[b]=[]
					self.outData[bits[0]]=tmp
			
	def parse(self):
		# TODO: check fname
		f = open(self.fname,"r")
		self.rawdata = f.readlines()
		self.parseSysInfo()
		self.parseCols()
		self.parseBBBP()
		print self.outData
		self.parseSnapshots()
		

