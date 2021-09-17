#!/usr/bin/python
# This file's encoding: UTF-8, so that non-ASCII characters can be used in strings.
#
#		███╗   ███╗ ███╗   ███╗ ██╗    ██╗			-------                                                   -------
#		████╗ ████║ ████╗ ████║ ██║    ██║		 # -=======---------------------------------------------------=======- #
#		██╔████╔██║ ██╔████╔██║ ██║ █╗ ██║		# ~ ~ Written by DRGN of SmashBoards (Daniel R. Cappel);  May, 2020 ~ ~ #
#		██║╚██╔╝██║ ██║╚██╔╝██║ ██║███╗██║		 #            [ Built with Python v2.7.16 and Tkinter 8.5 ]            #
#		██║ ╚═╝ ██║ ██║ ╚═╝ ██║ ╚███╔███╔╝		  # -======---------------------------------------------------======- #
#		╚═╝     ╚═╝ ╚═╝     ╚═╝  ╚══╝╚══╝ 			 ------                                                   ------
#		  -  - Melee Modding Wizard -  -  


# External dependencies
import os
import ttk
import time
import codecs
import psutil
import subprocess
import Tkinter as Tk
from ruamel import yaml
from ScrolledText import ScrolledText

# Internal dependencies
import globalData
from basicFunctions import msg, cmdChannel, printStatus
from guiSubComponents import BasicWindow, cmsg


#class NumberConverter( BasicWindow ):


class ImageDataLengthCalculator( BasicWindow ):

	def __init__( self, root ):
		BasicWindow.__init__( self, root, 'Image Data Length Calculator' )

		# Set up the input elements
		# Width
		ttk.Label( self.window, text='Width:' ).grid( column=0, row=0, padx=5, pady=2, sticky='e' )
		self.widthEntry = ttk.Entry( self.window, width=5, justify='center' )
		self.widthEntry.grid( column=1, row=0, padx=5, pady=2 )
		# Height
		ttk.Label( self.window, text='Height:' ).grid( column=0, row=1, padx=5, pady=2, sticky='e' )
		self.heightEntry = ttk.Entry( self.window, width=5, justify='center' )
		self.heightEntry.grid( column=1, row=1, padx=5, pady=2 )
		# Input Type
		ttk.Label( self.window, text='Image Type:' ).grid( column=0, row=2, padx=5, pady=2, sticky='e' )
		self.typeEntry = ttk.Entry( self.window, width=5, justify='center' )
		self.typeEntry.grid( column=1, row=2, padx=5, pady=2 )
		# Result Multiplier
		ttk.Label( self.window, text='Result Multiplier:' ).grid( column=0, row=3, padx=5, pady=2, sticky='e' )
		self.multiplierEntry = ttk.Entry( self.window, width=5, justify='center' )
		self.multiplierEntry.insert( 0, '1' ) # Default
		self.multiplierEntry.grid( column=1, row=3, padx=5, pady=2 )

		# Bind the event listeners for calculating the result
		for inputWidget in [ self.widthEntry, self.heightEntry, self.typeEntry, self.multiplierEntry ]:
			inputWidget.bind( '<KeyRelease>', self.calculateResult )

		# Set the output elements
		ttk.Label( self.window, text='Required File or RAM space:' ).grid( column=0, row=4, columnspan=2, padx=20, pady=5 )
		# In hex bytes
		self.resultEntryHex = ttk.Entry( self.window, width=20, justify='center' )
		self.resultEntryHex.grid( column=0, row=5, padx=5, pady=5 )
		ttk.Label( self.window, text='bytes (hex)' ).grid( column=1, row=5, padx=5, pady=5 )
		# In decimal bytes
		self.resultEntryDec = ttk.Entry( self.window, width=20, justify='center' )
		self.resultEntryDec.grid( column=0, row=6, padx=5, pady=5 )
		ttk.Label( self.window, text='(decimal)' ).grid( column=1, row=6, padx=5, pady=5 )

	def calculateResult( self, event ):
		try: 
			widthValue = self.widthEntry.get()
			if not widthValue: return
			elif '0x' in widthValue: width = int( widthValue, 16 )
			else: width = int( widthValue )

			heightValue = self.heightEntry.get()
			if not heightValue: return
			elif '0x' in heightValue: height = int( heightValue, 16 )
			else: height = int( heightValue )

			typeValue = self.typeEntry.get()
			if not typeValue: return
			elif '0x' in typeValue: _type = int( typeValue, 16 )
			else: _type = int( typeValue )

			multiplierValue = self.multiplierEntry.get()
			if not multiplierValue: return
			elif '0x' in multiplierValue: multiplier = int( multiplierValue, 16 )
			else: multiplier = float( multiplierValue )

			# Calculate the final amount of space required.
			imageDataLength = hsdStructures.ImageDataBlock.getDataLength( width, height, _type )
			finalSize = int( math.ceil(imageDataLength * multiplier) ) # Can't have fractional bytes, so we're rounding up

			self.resultEntryHex.delete( 0, 'end' )
			self.resultEntryHex.insert( 0, uHex(finalSize) )
			self.resultEntryDec.delete( 0, 'end' )
			self.resultEntryDec.insert( 0, humansize(finalSize) )
		except:
			self.resultEntryHex.delete( 0, 'end' )
			self.resultEntryHex.insert( 0, 'Invalid Input' )
			self.resultEntryDec.delete( 0, 'end' )


class TriCspCreator( object ):

	def __init__( self ):

		self.gimpDir = ''
		self.gimpExe = ''
		self.cspConfig = {}

		# Analyze the version of GIMP installed, and check for needed plugins
		self.determineGimpPath()
		gimpVersion = self.getGimpProgramVersion()
		pluginDir = self.getGimpPluginDirectory( gimpVersion )
		createCspScriptVersion = self.getScriptVersion( pluginDir, 'python-fu-create-tri-csp.py' )
		finishCspScriptVersion = self.getScriptVersion( pluginDir, 'python-fu-finish-csp.py' )
		
		# Print out version info
		print ''
		print '            Version info:'
		print ''
		print '  GIMP:                    ', gimpVersion
		print '  create-tri-csp script:   ', createCspScriptVersion
		print '  finish-csp script:       ', finishCspScriptVersion
		print ''
		print 'GIMP executable directory: ', self.gimpDir
		print 'GIMP Plug-ins directory:   ', pluginDir
		print ''
		
		# Load the CSP Configuration file
		try:
			cspConfigFilePath = os.path.join( globalData.paths['coreCodes'], 'CSP Configuration.yml' )
			with codecs.open( cspConfigFilePath, 'r', encoding='utf-8' ) as stream: # Using a different read method to accommodate UTF-8 encoding
				#cls.yamlDescriptions = yaml.safe_load( stream ) # Vanilla yaml module method (loses comments when saving/dumping back to file)
				self.cspConfig = yaml.load( stream, Loader=yaml.RoundTripLoader )
		except IOError: # Couldn't find the file
			msg( "Couldn't find the CSP config file at " + cspConfigFilePath, warning=True )
		except Exception as err: # Problem parsing the file
			msg( 'There was an error while parsing the yaml config file:\n\n{}'.format(err) )

	def determineGimpPath( self ):

		""" Determines the absolute file path to the GIMP console executable 
			(the exe itself varies based on program version). """
		
		# Check for the expected program folder
		directory = "C:\\Program Files\\GIMP 2\\bin"
		if not os.path.exists( directory ):
			msg( 'GIMP does not appear to be installed; unable to find the GIMP program directory at "{}".'.format(directory) )
			self.gimpDir = ''
			self.gimpExe = ''
			return
		
		# Check the files in the program folder for a 'console' executable
		for fileOrFolderName in os.listdir( directory ):
			if fileOrFolderName.startswith( 'gimp-console' ) and fileOrFolderName.endswith( '.exe' ):
				self.gimpDir = directory
				self.gimpExe = fileOrFolderName
				return

		else: # The loop above didn't break; unable to find the exe
			msg( 'Unable to find the GIMP console executable in "{}".'.format(directory) )
			self.gimpDir = ''
			self.gimpExe = ''
			return

	def getGimpProgramVersion( self ):
		#_, versionText = cmdChannel( 'start /B /D "{}" {} --version'.format(self.gimpDir, self.gimpExe), shell=True )
		_, versionText = cmdChannel( '"{}\{}" --version'.format(self.gimpDir, self.gimpExe) )
		return versionText.split()[-1]
		
	def getGimpPluginDirectory( self, gimpVersion ):

		""" Checks known directory paths for GIMP versions 2.8 and 2.10. If both appear 
			to be installed, we'll check the version of the executable that was found. """

		userFolder = os.path.expanduser( '~' ) # Resolves to "C:\Users\[userName]"
		v8_Path = os.path.join( userFolder, '.gimp-2.8\\plug-ins' )
		v10_Path = os.path.join( userFolder, 'AppData\\Roaming\\GIMP\\2.10\\plug-ins' )

		if os.path.exists( v8_Path ) and os.path.exists( v10_Path ):
			# Both versions seem to be installed. Use Gimp's version to decide which to use
			major, minor, _ = gimpVersion.split( '.' )
			if major != '2':
				return ''
			if minor == '8':
				return v8_Path
			else: # Hoping this path is good for other versions as well
				return v10_Path

		elif os.path.exists( v8_Path ): return v8_Path
		elif os.path.exists( v10_Path ): return v10_Path
		else: return ''

	def getScriptVersion( self, pluginDir, scriptFile ):

		""" Scans the given script (a file name) for a line like "version = 2.2\n" and parses it. """

		scriptPath = os.path.join( pluginDir, scriptFile )

		if os.path.exists( scriptPath ):
			with open( scriptPath, 'r' ) as script:
				for line in script:
					line = line.strip()

					if line.startswith( 'version' ) and '=' in line:
						return line.split( '=' )[-1].strip()
			
		return '-1'


class AsmToHexConverter( BasicWindow ):

	""" Tool window to convert assembly to hex and vice-verca. """

	def __init__( self, mod=None ):
		BasicWindow.__init__( self, globalData.gui.root, 'ASM <-> HEX Converter', offsets=(160, 100), resizable=True, topMost=False )
		self.window.minsize( width=480, height=350 )

		ttk.Label( self.window, text=('This assembles PowerPC assembly code into raw hex,\nor disassembles raw hex into PowerPC assembly.'
			#"\n\nNote that this functionality is also built into the entry fields for new code in the 'Add New Mod to Library' interface. "
			#'So you can use your assembly source code in those fields and it will automatically be converted to hex during installation. '
			'\nComments preceded with "#" will be ignored.'), wraplength=480 ).grid( column=0, row=0, padx=40 )

		self.lengthString = Tk.StringVar( value='' )
		self.mod = mod

		# Create the header row
		headersRow = ttk.Frame( self.window )
		ttk.Label( headersRow, text='ASM' ).grid( row=0, column=0, sticky='w' )
		ttk.Label( headersRow, textvariable=self.lengthString ).grid( row=0, column=1 )
		ttk.Label( headersRow, text='HEX' ).grid( row=0, column=2, sticky='e' )
		headersRow.grid( column=0, row=1, padx=40, pady=(7, 0), sticky='ew' )

		# Configure the header row, so it expands properly on window-resize
		headersRow.columnconfigure( 'all', weight=1 )

		# Create the text entry fields and center conversion buttons
		entryFieldsRow = ttk.Frame( self.window )
		self.sourceCodeEntry = ScrolledText( entryFieldsRow, width=30, height=20 )
		self.sourceCodeEntry.grid( rowspan=2, column=0, row=0, padx=5, pady=7, sticky='news' )
		ttk.Button( entryFieldsRow, text='->', command=self.asmToHexCode ).grid( column=1, row=0, pady=20, sticky='s' )
		ttk.Button( entryFieldsRow, text='<-', command=self.hexCodeToAsm ).grid( column=1, row=1, pady=20, sticky='n' )
		self.hexCodeEntry = ScrolledText( entryFieldsRow, width=30, height=20 )
		self.hexCodeEntry.grid( rowspan=2, column=2, row=0, padx=5, pady=7, sticky='news' )
		entryFieldsRow.grid( column=0, row=2, sticky='nsew' )
		
		# Configure the above columns, so that they expand proportionally upon window resizing
		entryFieldsRow.columnconfigure( 0, weight=6 )
		entryFieldsRow.columnconfigure( 1, weight=1 ) # Giving much less weight to this row, since it's just the buttons
		entryFieldsRow.columnconfigure( 2, weight=6 )
		entryFieldsRow.rowconfigure( 'all', weight=1 )

		# Determine the include paths to be used here, and add a button at the bottom of the window to display them
		self.detectContext()
		ttk.Button( self.window, text='View Include Paths', command=self.viewIncludePaths ).grid( column=0, row=3, pady=(2, 6), ipadx=20 )

		# Add the assembly time display (as an Entry widget so we can select text from it)
		self.assemblyTimeDisplay = Tk.Entry( self.window, width=25, borderwidth=0 )
		self.assemblyTimeDisplay.configure( state="readonly" )
		self.assemblyTimeDisplay.grid( column=0, row=3, sticky='w', padx=(7, 0) )

		# Configure this window's expansion as a whole, so that only the text entry row can expand when the window is resized
		self.window.columnconfigure( 0, weight=1 )
		self.window.rowconfigure( 0, weight=0 )
		self.window.rowconfigure( 1, weight=0 )
		self.window.rowconfigure( 2, weight=1 )
		self.window.rowconfigure( 3, weight=0 )

	def updateAssemblyDisplay( self, textInput ):
		self.assemblyTimeDisplay.configure( state="normal" )
		self.assemblyTimeDisplay.delete( 0, 'end' )
		self.assemblyTimeDisplay.insert( 0, textInput )
		self.assemblyTimeDisplay.configure( state="readonly" )

	def asmToHexCode( self ):
		# Clear the hex code field and info labels
		self.hexCodeEntry.delete( '1.0', 'end' )
		self.updateAssemblyDisplay( '' )
		self.lengthString.set( 'Length: ' )

		# Get the ASM to convert
		asmCode = self.sourceCodeEntry.get( '1.0', 'end' )

		# Assemble the code (this will also handle showing any warnings/errors to the user)
		tic = time.clock()
		#returnCode, hexCode = customCodeProcessor.preAssembleRawCode( asmCode, self.includePaths, discardWhitespace=False )
		#returnCode, hexCode = globalData.codeProcessor.()
		toc = time.clock()

		if returnCode != 0:
			return

		hexCode = hexCode.replace( '|S|', '' ) # Removes special branch syntax separators

		# Insert the new hex code
		self.hexCodeEntry.insert( 'end', hexCode )

		# Update the code length display
		codeLength = getCustomCodeLength( hexCode, preProcess=True, includePaths=self.includePaths ) # requires pre-processing to remove whitespace
		self.lengthString.set( 'Length: ' + uHex(codeLength) )

		# Update the assembly time display with appropriate units
		assemblyTime = round( toc - tic, 9 )
		if assemblyTime > 1:
			units = 's' # In seconds
		else:
			assemblyTime = assemblyTime * 1000
			if assemblyTime > 1:
				units = 'ms' # In milliseconds
			else:
				assemblyTime = assemblyTime * 1000
				units = 'us' # In microseconds
		self.updateAssemblyDisplay( 'Assembly Time:  {} {}'.format(assemblyTime, units) )

	def hexCodeToAsm( self ):
		# Delete the current assembly code, and clear the assembly time label
		self.sourceCodeEntry.delete( '1.0', 'end' )
		self.updateAssemblyDisplay( '' )

		# Get the HEX code to disassemble
		hexCode = self.hexCodeEntry.get( '1.0', 'end' )
		
		# Disassemble the code into assembly
		returnCode, asmCode = customCodeProcessor.preDisassembleRawCode( hexCode, discardWhitespace=False )

		if returnCode != 0:
			self.lengthString.set( 'Length: ' )
			return

		# Replace the current assembly code
		self.sourceCodeEntry.insert( 'end', asmCode )

		# Update the code length display
		codeLength = getCustomCodeLength( hexCode, preProcess=True, includePaths=self.includePaths )
		self.lengthString.set( 'Length: ' + uHex(codeLength) )

	def detectContext( self ):

		""" This window should use the same .include context for whatever mod it was opened with. 
			If an associated mod is not found, fall back on the default import directories. """

		if self.mod:
			self.includePaths = self.mod.includePaths
		else:
			libraryFolder = globalData.getModsFolderPath()
			self.includePaths = [ os.path.join(libraryFolder, '.include'), os.path.join(globalData.scriptHomeFolder, '.include') ]

	def viewIncludePaths( self ):

		""" Build and display a message to the user on assembly context and current paths. """

		# Build the message to show the user
		paths = [ os.getcwd() + '          <- Current Working Directory' ]
		paths.extend( self.includePaths )
		paths = '\n'.join( paths )

		message =	( 'Assembly context (for ".include" file imports) has the following priority:'
					  "\n\n1) The current working directory (usually the program root folder)"
					  "\n2) Directory of the mod's code file (or the code's root folder with AMFS)"
					  """\n3) The current Code Library's ".include" directory"""
					  """\n4) The program root folder's ".include" directory""" )

		if self.mod:
			message += ( '\n\n\nThis instance of the converter is using assembly context for .include file imports based on {}. '
					 'The exact paths are as follows:\n\n{}'.format( self.mod.name, paths ) )
		else:
			message += ( '\n\n\nThis instance of the converter is using default assembly context for .include file imports. '
					 'The exact paths are as follows:\n\n' + paths )

		cmsg( message, 'Include Paths', 'left' )


class DolphinController( object ):

	""" Wrapper the Dolphin emulator, to handle starting/stopping 
		the game, file I/O, and option configuration. """

	def __init__( self ):
		self._exePath = ''
		self.rootFolder = ''
		self.userFolder = ''
		self.process = None

	@property
	def exePath( self ):

		""" Set up initial filepaths. This should be done just once, on the first path request. 
			This is not done in the init method because program settings were not loaded then. """

		if self._exePath:
			return self._exePath
		
		self._exePath = globalData.getEmulatorPath()
		self.rootFolder = os.path.dirname( self._exePath )
		self.userFolder = os.path.join( self.rootFolder, 'User' )

		# Make sure that Dolphin is in 'portable' mode
		portableFile = os.path.join( self.rootFolder, 'portable.txt' )
		if not os.path.exists( portableFile ):
			print 'Dolphin is not in portable mode! Attempting to create portable.txt'
			try:
				with open( portableFile, 'w' ) as newFile:
					pass
			except:
				msg( "Dolphin is not in portable mode, and 'portable.txt' could not be created. Be sure that this program "
					 "has write permissions in the Dolphin root directory.", 'Non-portable Dolphin', globalData.gui.root, warning=True )
				return

		if not os.path.exists( self.userFolder ):
			self.start( '' ) # Will open, create the user folder, and close? todo: needs testing
			# time.sleep( 4 )
			# self.stop()

		return self._exePath

	@property
	def isRunning( self ):
		if not self.process: # Hasn't been started
			return False

		return ( self.process.poll() == None ) # None means the process is still running; anything else is an exit code

	def getVersion( self ):
		
		if not self.exePath:
			return '' # User may have canceled the prompt

		returnCode, output = cmdChannel( '{} --version'.format(self.exePath) )

		if returnCode == 0:
			return output
		else:
			return 'N/A'
	
	def start( self, discObj ):
		
		# Get the path to the user's emulator of choice
		#emulatorPath = globalData.getEmulatorPath() # Will also validate the path

		#print 'is running:', self.isRunning
		if not self.exePath:
			return # User may have canceled the prompt

		# Make sure there are no prior instances of Dolphin running
		if self.isRunning:
			self.stop()
		self.stopAllDolphinInstances()

		# print 'Booting', discObj.filePath
		# print 'In', self.exePath
		
		# Send the disc filepath to Dolphin
		# '--exec' loads the specified file. (Using '--exec' because '/e' is incompatible with Dolphin 5+, while '-e' is incompatible with Dolphin 4.x)
		# '--batch' will prevent dolphin from unnecessarily scanning game/ISO directories, and will shut down Dolphin when the game is stopped.
		printStatus( 'Booting in emulator....' )
		if globalData.checkSetting( 'runDolphinInDebugMode' ):
			command = '"{}" --debugger --exec="{}"'.format( self.exePath, discObj.filePath )
		else:
			command = '"{}" --batch --exec="{}"'.format( self.exePath, discObj.filePath )
		self.process = subprocess.Popen( command, stderr=subprocess.STDOUT, creationflags=0x08000000 )

		#print 'is running:', self.isRunning

	def stop( self ):

		""" Stop an existing Dolphin process that was spawned from this controller. """

		self.process.terminate()
		time.sleep( 2 )

	def stopAllDolphinInstances( self ):
		# Check for a running instances of Dolphin

		processFound = False

		for process in psutil.process_iter():
			if process.name() == 'Dolphin.exe':
				process.terminate()
				processFound = True
				printStatus( 'Stopped an older Dolphin process' )
		
		if processFound:
			time.sleep( 2 )